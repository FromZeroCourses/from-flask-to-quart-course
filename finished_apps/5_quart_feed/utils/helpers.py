import re
import secrets
import string
from functools import wraps
from typing import Any, Callable, Optional

from quart import current_app, redirect, request, session, url_for
from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table

# base36 (lowercase letters + digits) keeps post uids short and URL-clean.
_UID_ALPHABET = string.ascii_lowercase + string.digits


def generate_uid(length: int = 8) -> str:
    """Return a short, opaque, URL-safe id for a post permalink."""
    return "".join(secrets.choice(_UID_ALPHABET) for _ in range(length))


def slugify(text: str, max_words: int = 6, max_len: int = 60) -> str:
    """Turn a post message into an SEO-friendly URL slug.

    Lowercases, strips punctuation, and keeps the first few words so the
    permalink reads like ``/post/ab12cd34/i-need-to-go-to-the-supermarket``.
    """
    words = re.sub(r"[^a-z0-9\s-]", "", (text or "").lower()).split()
    slug = "-".join(words[:max_words])[:max_len].strip("-")
    return slug or "post"


def login_required(f: Callable) -> Callable:
    """Redirect anonymous visitors to the login page.

    The wrapper itself must be an async function (not a sync function that
    merely returns a coroutine) so that Quart's routing recognizes it as a
    coroutine function and awaits it correctly.
    """

    @wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session.get("username") is None:
            return redirect(url_for("user_app.login", next=request.url))
        return await f(*args, **kwargs)

    return decorated_function


async def get_user_by_username(conn: Any, username: str) -> Optional[Row]:
    result = await conn.execute(
        select(user_table).where(user_table.c.username == username)
    )
    return result.fetchone()


async def get_user_by_id(conn: Any, user_id: int) -> Optional[Row]:
    result = await conn.execute(select(user_table).where(user_table.c.id == user_id))
    return result.fetchone()


def image_url(user_id: int, image: Optional[int], size: str = "lg") -> str:
    """Build the avatar URL for a user, at the requested size (sm/lg/xlg).

    ``user_id``/``image`` are passed separately (rather than a full user row)
    so this works both for a full ``user`` row and for a joined feed row that
    only carries ``author_id``/``author_image`` columns. ``image`` is the
    avatar's image_id (a timestamp); files are named by ``thumbnail_process``
    as ``avatars/{user_id}.{image_id}.{size}.png``.
    """
    if image:
        return f"{current_app.config['IMAGE_URL']}/avatars/{user_id}.{image}.{size}.png"
    return "/static/default_profile.png"
