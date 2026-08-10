from typing import Iterable

from sqlalchemy import insert

from post.models import feed_table


async def add_to_feed(conn, user_id: int, post_id: int) -> None:
    """Insert one feed row for a recipient."""
    await conn.execute(
        insert(feed_table).values(user_id=user_id, post_id=post_id)
    )


async def fan_out_post(conn, post_id: int, recipient_ids: Iterable[int]) -> None:
    """A brand-new post lands directly in the author's and followers' feeds."""
    for user_id in set(recipient_ids):
        await add_to_feed(conn, user_id, post_id)
