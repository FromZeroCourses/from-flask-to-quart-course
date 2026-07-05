import json

from quart import Blueprint, current_app, redirect, session, url_for
from sqlalchemy import insert, select

from comment.forms import CommentForm
from comment.models import comment_table
from utils.feed_ops import bubble_post
from utils.helpers import login_required
from post.models import feed_table
from relationship.views import followers
from utils.sse import ServerSentEvent, broker
from user.models import user_table

comment_app = Blueprint("comment_app", __name__)


@comment_app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
async def create_comment(post_id: int):
    form = await CommentForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            result = await conn.execute(
                insert(comment_table).values(
                    post_id=post_id,
                    user_id=session["user_id"],
                    comment=form.comment.data,
                )
            )
            comment_id = result.inserted_primary_key[0]

            comment_row = (
                await conn.execute(
                    select(comment_table).where(comment_table.c.id == comment_id)
                )
            ).fetchone()
            author = (
                await conn.execute(
                    select(user_table).where(user_table.c.id == session["user_id"])
                )
            ).fetchone()

            # Bubble the post into the feeds of my followers (and mine), so a
            # post I comment on surfaces for the people who follow me — even if
            # they don't follow its author — tagged "<me> commented on this".
            bubble_recipients = set(await followers(conn, session["user_id"]))
            bubble_recipients.add(session["user_id"])
            await bubble_post(
                conn, post_id, bubble_recipients, session["user_id"], "comment"
            )

            # The recipients are exactly the users who have this post in their
            # feed (now including the just-bubbled ones), so the live comment
            # reaches the same pages showing the post.
            recipient_ids = [
                r.user_id
                for r in (
                    await conn.execute(
                        select(feed_table.c.user_id).where(
                            feed_table.c.post_id == post_id
                        )
                    )
                ).fetchall()
            ]

        payload = {
            "post_id": post_id,
            "comment_id": comment_id,
            "comment": comment_row.comment,
            "created": comment_row.created.isoformat(),
            "author_username": author.username,
        }
        await broker.publish_many(
            recipient_ids, ServerSentEvent(event="comment", data=json.dumps(payload))
        )

    return redirect(url_for("post_app.home"))
