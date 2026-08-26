import json

from quart import Blueprint, current_app, redirect, session, url_for
from sqlalchemy import insert, select

from comment.forms import CommentForm
from comment.models import comment_table
from post.feed_ops import bubble_post
from post.models import feed_table
from post.views import build_post_payload
from utils.helpers import login_required
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

            # Bubble into my followers' feeds (and mine): "<me> commented on this".
            follower_ids = await followers(conn, session["user_id"])
            bubble_recipients = set(follower_ids)
            bubble_recipients.add(session["user_id"])
            await bubble_post(
                conn, post_id, bubble_recipients, session["user_id"], "comment"
            )

            # Everyone with this post in their feed gets the live comment.
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

            # The bubbled post's payload, tagged with who commented and why.
            bubble_payload = await build_post_payload(
                conn, post_id, "comment", author.username
            )

        # Push the post to followers first, then the comment to everyone holding it.
        if follower_ids:
            await broker.publish_many(
                follower_ids,
                ServerSentEvent(event="post", data=json.dumps(bubble_payload)),
            )

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
