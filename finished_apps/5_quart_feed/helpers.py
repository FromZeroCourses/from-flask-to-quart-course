from functools import wraps
from typing import Any, Callable, Optional

from quart import current_app, redirect, request, session, url_for
from sqlalchemy import select
from sqlalchemy.engine import Row

from user.models import user_table


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


def image_url(user_id: int, image: Optional[int]) -> str:
    """Build the avatar URL for a user.

    ``user_id``/``image`` are passed separately (rather than a full user row)
    so this works both for a full ``user`` row and for a joined feed row that
    only carries ``author_id``/``author_image`` columns.
    """
    if image:
        return f"{current_app.config['IMAGE_URL']}/{user_id}_{image}.png"
    return "/static/default_profile.png"
