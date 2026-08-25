from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from post.models import feed_table


async def add_to_feed(
    conn,
    user_id: int,
    post_id: int,
    reason_user_id: Optional[int] = None,
    reason_type: Optional[str] = None,
) -> None:
    """Insert one feed row for a recipient, or bump it if it already exists."""
    stmt = pg_insert(feed_table).values(
        user_id=user_id,
        post_id=post_id,
        reason_user_id=reason_user_id,
        reason_type=reason_type,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_feed_user_post",
        set_={"updated": func.now()},
    )
    await conn.execute(stmt)


async def fan_out_post(conn, post_id: int, recipient_ids: Iterable[int]) -> None:
    """A brand-new post lands directly in the author's and followers' feeds."""
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id)


async def bubble_post(
    conn,
    post_id: int,
    recipient_ids: Iterable[int],
    reason_user_id: int,
    reason_type: str,
) -> None:
    """Surface an existing post into more feeds because someone engaged with it."""
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id, reason_user_id, reason_type)
