"""Feed fan-out helpers.

The ``feed`` table is the materialized per-user timeline. Two things put a post
in your feed:

1. Fan-out — when someone you follow (or you) posts, the post lands directly in
   your feed (no attribution).
2. Bubbling — when someone you follow comments on a post, that post surfaces in
   your feed even if you don't follow the author, tagged with the reason
   ("<name> commented on this").

UNIQUE(user_id, post_id) guarantees a post appears at most once per feed, so a
post you'd get from both routes is de-duplicated. On a conflict we bump
``updated`` so fresh activity floats the post back to the top.
"""
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
    """A brand-new post lands directly in the author's + followers' feeds."""
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
