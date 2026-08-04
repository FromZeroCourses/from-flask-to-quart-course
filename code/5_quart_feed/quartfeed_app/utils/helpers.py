import os
import re
import string
import time
from functools import wraps
from typing import Any, Callable, Optional

from quart import current_app, redirect, request, session, url_for
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


SNOWFLAKE_EPOCH_MS = 1_704_067_200_000  # 2024-01-01T00:00:00Z
_WORKER_ID_BITS = 10
_SEQUENCE_BITS = 12
_MAX_WORKER_ID = (1 << _WORKER_ID_BITS) - 1
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1


class SnowflakeGenerator:
    """Twitter's id scheme: 41 bits of milliseconds, 10 of worker, 12 of sequence."""

    def __init__(self, worker_id: int, epoch_ms: int = SNOWFLAKE_EPOCH_MS) -> None:
        if not 0 <= worker_id <= _MAX_WORKER_ID:
            raise ValueError(f"worker_id must be between 0 and {_MAX_WORKER_ID}")
        self.worker_id = worker_id
        self.epoch_ms = epoch_ms
        self._sequence = 0
        self._last_ms = -1

    def next_id(self) -> int:
        now_ms = int(time.time() * 1000)

        if now_ms < self._last_ms:
            drift = self._last_ms - now_ms
            raise RuntimeError(f"clock moved backwards {drift}ms, refusing to mint")

        if now_ms == self._last_ms:
            self._sequence = (self._sequence + 1) & _MAX_SEQUENCE
            while self._sequence == 0 and now_ms <= self._last_ms:
                now_ms = int(time.time() * 1000)
        else:
            self._sequence = 0

        self._last_ms = now_ms
        return (
            ((now_ms - self.epoch_ms) << (_WORKER_ID_BITS + _SEQUENCE_BITS))
            | (self.worker_id << _SEQUENCE_BITS)
            | self._sequence
        )


_BASE62 = string.digits + string.ascii_uppercase + string.ascii_lowercase
_snowflake = SnowflakeGenerator(worker_id=int(os.environ.get("WORKER_ID", "0")))


def _base62(number: int) -> str:
    """Encode a non-negative integer as base62, shortest form."""
    digits = []
    while number:
        number, remainder = divmod(number, 62)
        digits.append(_BASE62[remainder])
    return "".join(reversed(digits)) or _BASE62[0]


def generate_uid() -> str:
    """The post's public id: a Snowflake, base62 encoded so it fits in a URL."""
    return _base62(_snowflake.next_id())


def slugify(text: str, max_words: int = 6, max_len: int = 60) -> str:
    """Turn a post message into an SEO-friendly URL slug."""
    words = re.sub(r"[^a-z0-9\s-]", "", (text or "").lower()).split()
    slug = "-".join(words[:max_words])[:max_len].strip("-")
    return slug or "post"


def post_image_url(post_id: int, image_id: int) -> str:
    """URL for a post image, written by image_height_transform."""
    return f"{current_app.config['IMAGE_URL']}/posts/{post_id}.{image_id}.xlg.png"
