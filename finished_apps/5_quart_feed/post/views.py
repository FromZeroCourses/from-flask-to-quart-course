import asyncio
import json
from typing import Any, Dict, List, Optional

from quart import (
    Blueprint,
    abort,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func, insert, select

from comment.models import comment_table
from helpers import image_url, login_required
from like.models import like_table
from post.forms import PostForm
from post.models import feed_table, post_table
from relationship.views import followers
from sse import ServerSentEvent, broker
from user.models import user_table

post_app = Blueprint("post_app", __name__)


async def _post_extras(conn: Any, post_id: int, user_id: int) -> Dict[str, Any]:
    """Comments + like info for a single post, from the ``user_id`` viewer's POV."""
    comment_rows = (
        await conn.execute(
            select(
                comment_table.c.id,
                comment_table.c.comment,
                comment_table.c.created,
                user_table.c.username.label("author_username"),
            )
            .select_from(
                comment_table.join(user_table, comment_table.c.user_id == user_table.c.id)
            )
            .where(comment_table.c.post_id == post_id)
            .order_by(comment_table.c.created.asc())
        )
    ).fetchall()

    like_count = (
        await conn.execute(
            select(func.count())
            .select_from(like_table)
            .where(like_table.c.post_id == post_id)
        )
    ).scalar_one()

    liked_by_me = (
        await conn.execute(
            select(like_table).where(
                (like_table.c.post_id == post_id) & (like_table.c.user_id == user_id)
            )
        )
    ).fetchone() is not None

    return {
        "comments": comment_rows,
        "like_count": like_count,
        "liked_by_me": liked_by_me,
    }


async def _load_feed(
    conn: Any, user_id: int, offset: int = 0, limit: int = 10
) -> List[Dict[str, Any]]:
    """A page of feed rows for ``user_id``, each with comments + like info preloaded."""
    feed_query = (
        select(
            feed_table.c.updated,
            post_table.c.id.label("post_id"),
            post_table.c.message,
            post_table.c.created,
            user_table.c.id.label("author_id"),
            user_table.c.username.label("author_username"),
            user_table.c.image.label("author_image"),
        )
        .select_from(
            feed_table.join(post_table, feed_table.c.post_id == post_table.c.id).join(
                user_table, post_table.c.user_id == user_table.c.id
            )
        )
        .where(feed_table.c.user_id == user_id)
        .order_by(feed_table.c.updated.desc())
        .limit(limit)
        .offset(offset)
    )
    feed_rows = (await conn.execute(feed_query)).fetchall()

    posts = []
    for row in feed_rows:
        extras = await _post_extras(conn, row.post_id, user_id)
        posts.append(
            {
                "post_id": row.post_id,
                "message": row.message,
                "created": row.created,
                "author_id": row.author_id,
                "author_username": row.author_username,
                "avatar_url": image_url(row.author_id, row.author_image),
                **extras,
            }
        )

    return posts


async def _load_single_post(
    conn: Any, post_id: int, viewer_user_id: int
) -> Optional[Dict[str, Any]]:
    """Load ONE post by id (any post, not restricted to the feed).

    Returns the same dict shape as ``_load_feed``'s items so the shared card
    partial renders it unchanged, or ``None`` if the post does not exist.
    """
    row = (
        await conn.execute(
            select(
                post_table.c.id.label("post_id"),
                post_table.c.message,
                post_table.c.created,
                user_table.c.id.label("author_id"),
                user_table.c.username.label("author_username"),
                user_table.c.image.label("author_image"),
            )
            .select_from(
                post_table.join(user_table, post_table.c.user_id == user_table.c.id)
            )
            .where(post_table.c.id == post_id)
        )
    ).fetchone()

    if row is None:
        return None

    extras = await _post_extras(conn, row.post_id, viewer_user_id)
    return {
        "post_id": row.post_id,
        "message": row.message,
        "created": row.created,
        "author_id": row.author_id,
        "author_username": row.author_username,
        "avatar_url": image_url(row.author_id, row.author_image),
        **extras,
    }


@post_app.route("/")
async def home():
    if session.get("username") is None:
        return redirect(url_for("user_app.login"))

    form = await PostForm.create_form()
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        posts = await _load_feed(conn, session["user_id"])

    return await render_template("post/home.html", posts=posts, form=form)


@post_app.route("/feed")
@login_required
async def feed():
    """Return one page of feed cards (for infinite scroll). Empty when exhausted."""
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    form = await PostForm.create_form()
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        posts = await _load_feed(conn, session["user_id"], offset=offset, limit=10)

    return await render_template("post/_feed_items.html", posts=posts, form=form)


@post_app.route("/post/<int:post_id>")
@login_required
async def detail(post_id: int):
    """Permalink page for a single post."""
    form = await PostForm.create_form()
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        post = await _load_single_post(conn, post_id, session["user_id"])

    if post is None:
        abort(404)

    return await render_template("post/detail.html", post=post, form=form)


@post_app.route("/post", methods=["POST"])
@login_required
async def create_post():
    form = await PostForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            result = await conn.execute(
                insert(post_table).values(
                    user_id=session["user_id"], message=form.message.data
                )
            )
            post_id = result.inserted_primary_key[0]

            # Fan out: a feed row for every follower of me, and one for
            # myself so my own posts show up in my own feed too.
            recipient_ids = set(await followers(conn, session["user_id"]))
            recipient_ids.add(session["user_id"])
            for recipient_id in recipient_ids:
                await conn.execute(
                    insert(feed_table).values(user_id=recipient_id, post_id=post_id)
                )

            author = (
                await conn.execute(
                    select(user_table).where(user_table.c.id == session["user_id"])
                )
            ).fetchone()
            post_row = (
                await conn.execute(select(post_table).where(post_table.c.id == post_id))
            ).fetchone()

        payload = {
            "post_id": post_id,
            "message": post_row.message,
            "created": post_row.created.isoformat(),
            "author_id": author.id,
            "author_username": author.username,
            "avatar_url": image_url(author.id, author.image),
        }
        await broker.publish(ServerSentEvent(event="post", data=json.dumps(payload)))

    return redirect(url_for(".home"))


@post_app.route("/sse")
async def sse():
    async def gen():
        q = broker.subscribe()
        try:
            while True:
                event = await q.get()
                yield event.encode()
        except asyncio.CancelledError:
            broker.unsubscribe(q)
            raise

    response = await make_response(
        gen(),
        {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        },
    )
    response.timeout = None  # IMPORTANT: disable the default response timeout for streaming
    return response
