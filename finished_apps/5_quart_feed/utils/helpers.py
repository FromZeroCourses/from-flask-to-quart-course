import re
import secrets
import string
from functools import wraps
from typing import Any, Callable, List, Optional

from markupsafe import Markup, escape
from quart import current_app, redirect, request, session, url_for
from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table

_URL_RE = re.compile(r"(https?://[^\s<]+)")

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


def post_image_url(post_id: int, image_id: int) -> str:
    """URL for a post image (fixed-height variant), written by image_height_transform."""
    return f"{current_app.config['IMAGE_URL']}/posts/{post_id}.{image_id}.xlg.png"


def likes_line(likers: List[str], head: int = 3, collapse_over: int = 5) -> Markup:
    """FriendFeed-style "A, B and C liked this" line.

    Up to ``collapse_over`` names are listed in full; beyond that the first
    ``head`` are shown followed by an expandable "N other people" link.
    """
    names = [str(escape(name)) for name in likers]
    n = len(names)
    if n == 0:
        return Markup("")

    emoji = '<span class="likes-emoji">\U0001f642</span> '
    if n <= collapse_over:
        if n == 1:
            body = f"{names[0]} liked this"
        else:
            body = ", ".join(names[:-1]) + f" and {names[-1]} liked this"
        return Markup(emoji + body)

    shown = ", ".join(names[:head])
    others = n - head
    full = ", ".join(names)
    collapsed = (
        f'<span class="likers-collapsed">{shown} and '
        f'<a href="#" class="likers-more">{others} other people</a> liked this</span>'
    )
    expanded = f'<span class="likers-full d-none">{full} liked this</span>'
    return Markup(emoji + collapsed + expanded)


def linkify(text: Optional[str], max_len: int = 40) -> Markup:
    """Escape ``text`` and turn bare http(s) URLs into links, truncating long ones."""
    parts = _URL_RE.split(text or "")
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # a captured URL
            display = part if len(part) <= max_len else part[: max_len - 1] + "…"
            out.append(
                f'<a href="{escape(part)}" target="_blank" '
                f'rel="noopener">{escape(display)}</a>'
            )
        else:
            out.append(str(escape(part)))
    return Markup("".join(out))
