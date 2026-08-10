from pathlib import Path
from typing import Any, Dict, List, Optional

from quart import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import insert, select

from post.feed_ops import fan_out_post
from post.forms import PostForm
from post.models import feed_table, post_image_table, post_table
from relationship.views import followers
from user.models import user_table
from utils.helpers import (
    generate_uid,
    image_url,
    login_required,
    post_image_url,
    slugify,
)
from utils.imaging import image_height_transform

post_app = Blueprint("post_app", __name__)


def _posts_dir() -> Path:
    return Path(current_app.config["UPLOADS_FOLDER"]) / "posts"


async def _post_images(conn: Any, post_id: int) -> List[Dict[str, Any]]:
    """Images attached to a post, ordered for side-by-side display."""
    rows = (
        await conn.execute(
            select(post_image_table.c.image_id, post_image_table.c.width)
            .where(post_image_table.c.post_id == post_id)
            .order_by(post_image_table.c.position.asc())
        )
    ).fetchall()
    return [
        {"url": post_image_url(post_id, row.image_id), "width": row.width}
        for row in rows
    ]


async def _load_feed(
    conn: Any, user_id: int, offset: int = 0, limit: int = 10
) -> List[Dict[str, Any]]:
    """One page of a user's feed, newest activity first."""
    feed_query = (
        select(
            post_table.c.id.label("post_id"),
            post_table.c.uid,
            post_table.c.message,
            post_table.c.created,
            user_table.c.id.label("author_id"),
            user_table.c.username.label("author_username"),
            user_table.c.image.label("author_image"),
        )
        .select_from(
            feed_table.join(post_table, feed_table.c.post_id == post_table.c.id)
            .join(user_table, post_table.c.user_id == user_table.c.id)
        )
        .where(feed_table.c.user_id == user_id)
        .order_by(feed_table.c.updated.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await conn.execute(feed_query)).fetchall()

    posts = []
    for row in rows:
        posts.append(
            {
                "post_id": row.post_id,
                "message": row.message,
                "created": row.created,
                "author_username": row.author_username,
                "avatar_url": image_url(row.author_id, row.author_image, "sm"),
                "images": await _post_images(conn, row.post_id),
                "permalink": url_for(
                    "post_app.detail", uid=row.uid, slug=slugify(row.message)
                ),
            }
        )

    return posts


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
    """One page of feed cards for infinite scroll. Empty when exhausted."""
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        posts = await _load_feed(conn, session["user_id"], offset=offset)

    return await render_template("post/_feed_items.html", posts=posts)


@post_app.route("/post", methods=["POST"])
@login_required
async def create_post():
    form = await PostForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            result = await conn.execute(
                insert(post_table).values(
                    uid=generate_uid(),
                    user_id=session["user_id"],
                    message=form.message.data,
                )
            )
            post_id = result.inserted_primary_key[0]

            recipient_ids = set(await followers(conn, session["user_id"]))
            recipient_ids.add(session["user_id"])
            await fan_out_post(conn, post_id, recipient_ids)

            if form.image.data:
                image_id, width = image_height_transform(
                    form.image.data.read(), _posts_dir(), post_id
                )
                await conn.execute(
                    insert(post_image_table).values(
                        post_id=post_id, image_id=image_id, width=width, position=0
                    )
                )

    return redirect(url_for(".home"))


@post_app.route("/post/<uid>/")
@post_app.route("/post/<uid>/<slug>")
@login_required
async def detail(uid: str, slug: Optional[str] = None):
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        row = (
            await conn.execute(select(post_table).where(post_table.c.uid == uid))
        ).fetchone()

        if row is None:
            abort(404)

        post = {
            "uid": row.uid,
            "message": row.message,
            "created": row.created,
            "images": await _post_images(conn, row.id),
        }

    canonical_slug = slugify(post["message"])
    if slug != canonical_slug:
        return redirect(
            url_for("post_app.detail", uid=uid, slug=canonical_slug), code=301
        )

    return await render_template("post/detail.html", post=post)
