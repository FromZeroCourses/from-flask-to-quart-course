from typing import List

from quart import Blueprint, abort, current_app, redirect, session, url_for
from quart_wtf import QuartForm
from sqlalchemy import delete, insert, select

from helpers import get_user_by_username, login_required
from relationship.models import relationship_table

relationship_app = Blueprint("relationship_app", __name__)


class EmptyForm(QuartForm):
    """CSRF-only form used for the follow/unfollow POSTs (no visible fields)."""


async def is_following(conn, fm_user_id: int, to_user_id: int) -> bool:
    result = await conn.execute(
        select(relationship_table).where(
            (relationship_table.c.fm_user_id == fm_user_id)
            & (relationship_table.c.to_user_id == to_user_id)
        )
    )
    return result.fetchone() is not None


async def followers(conn, user_id: int) -> List[int]:
    """Return the list of user_ids following ``user_id`` (needed for post fan-out)."""
    result = await conn.execute(
        select(relationship_table.c.fm_user_id).where(
            relationship_table.c.to_user_id == user_id
        )
    )
    return [row.fm_user_id for row in result.fetchall()]


@relationship_app.route("/follow/<username>", methods=["POST"])
@login_required
async def follow(username: str):
    form = await EmptyForm.create_form()
    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            target = await get_user_by_username(conn, username)
            if target is None:
                abort(404)

            my_id = session["user_id"]
            if target.id != my_id and not await is_following(conn, my_id, target.id):
                await conn.execute(
                    insert(relationship_table).values(
                        fm_user_id=my_id, to_user_id=target.id
                    )
                )

    return redirect(url_for("user_app.profile", username=username))


@relationship_app.route("/unfollow/<username>", methods=["POST"])
@login_required
async def unfollow(username: str):
    form = await EmptyForm.create_form()
    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            target = await get_user_by_username(conn, username)
            if target is None:
                abort(404)

            await conn.execute(
                delete(relationship_table).where(
                    (relationship_table.c.fm_user_id == session["user_id"])
                    & (relationship_table.c.to_user_id == target.id)
                )
            )

    return redirect(url_for("user_app.profile", username=username))
