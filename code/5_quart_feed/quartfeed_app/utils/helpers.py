import os
import re
from functools import wraps
from typing import Any, Callable, Optional

from quart import current_app, redirect, request, session, url_for
from snowflake import SnowflakeGenerator
from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table


async def get_user_by_username(conn: Any, username: str) -> Optional[Row]:
    result = await conn.execute(
        select(user_table).where(user_table.c.username == username)
    )
    return result.fetchone()


def login_required(f: Callable) -> Callable:
    @wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session.get("username") is None:
            return redirect(url_for("user_app.login", next=request.url))
        return await f(*args, **kwargs)

    return decorated_function


async def get_user_by_id(conn: Any, user_id: int) -> Optional[Row]:
    result = await conn.execute(select(user_table).where(user_table.c.id == user_id))
    return result.fetchone()


def image_url(user_id: int, image: Optional[int], size: str = "lg") -> str:
    if image:
        return f"{current_app.config['IMAGE_URL']}/avatars/{user_id}.{image}.{size}.png"
    return "/static/default_profile.png"


# Every process minting ids needs its OWN instance number, or two of them
# will eventually agree on a millisecond and a sequence.
_snowflake = SnowflakeGenerator(int(os.environ.get("INSTANCE_ID", "0")))


def generate_uid() -> str:
    """The post's public id: a Snowflake, hex encoded so it fits in a URL."""
    return f"{next(_snowflake):016x}"


def slugify(text: str, max_words: int = 6, max_len: int = 60) -> str:
    """Turn a post message into an SEO-friendly URL slug."""
    words = re.sub(r"[^a-z0-9\s-]", "", (text or "").lower()).split()
    slug = "-".join(words[:max_words])[:max_len].strip("-")
    return slug or "post"


def post_image_url(post_id: int, image_id: int) -> str:
    """URL for a post image, written by image_height_transform."""
    return f"{current_app.config['IMAGE_URL']}/posts/{post_id}.{image_id}.xlg.png"
