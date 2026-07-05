import json

from quart import Blueprint, current_app, redirect, session, url_for
from quart_wtf import QuartForm
from sqlalchemy import delete, func, insert, select

from utils.helpers import login_required
from like.models import like_table
from post.models import feed_table
from utils.sse import ServerSentEvent, broker

like_app = Blueprint("like_app", __name__)


class LikeForm(QuartForm):
    """CSRF-only form used for the like/unlike toggle POST (no visible fields)."""


@like_app.route("/like/<int:post_id>", methods=["POST"])
@login_required
async def toggle_like(post_id: int):
    form = await LikeForm.create_form()

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            existing = (
                await conn.execute(
                    select(like_table).where(
                        (like_table.c.post_id == post_id)
                        & (like_table.c.user_id == session["user_id"])
                    )
                )
            ).fetchone()

            if existing is not None:
                await conn.execute(delete(like_table).where(like_table.c.id == existing.id))
            else:
                await conn.execute(
                    insert(like_table).values(post_id=post_id, user_id=session["user_id"])
                )

            like_count = (
                await conn.execute(
                    select(func.count())
                    .select_from(like_table)
                    .where(like_table.c.post_id == post_id)
                )
            ).scalar_one()

            # Deliver the updated count only to pages that have this post
            # (i.e. the users whose feed contains it), not every open page.
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

        await broker.publish_many(
            recipient_ids,
            ServerSentEvent(
                event="like",
                data=json.dumps({"post_id": post_id, "like_count": like_count}),
            ),
        )

    return redirect(url_for("post_app.home"))
