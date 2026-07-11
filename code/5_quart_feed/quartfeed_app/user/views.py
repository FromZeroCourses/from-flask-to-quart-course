from typing import Optional, Union

from passlib.hash import pbkdf2_sha256
from quart import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from sqlalchemy import insert, select

from utils.helpers import get_user_by_username, login_required
from relationship.models import relationship_table
from relationship.views import EmptyForm, is_following
from user.forms import UserForm
from user.models import user_table

user_app = Blueprint("user_app", __name__)


@user_app.route("/register", methods=["GET", "POST"])
async def register() -> Union[str, Response]:
    form = await UserForm.create_form()
    error: Optional[str] = None

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            existing = await get_user_by_username(conn, form.username.data)

            if existing is not None:
                error = "User already exists"
            else:
                password_hash = pbkdf2_sha256.hash(form.password.data)
                await conn.execute(
                    insert(user_table).values(
                        username=form.username.data, password=password_hash
                    )
                )

        if not error:
            await flash("User registered successfully, please login")
            return redirect(url_for(".login"))

    return await render_template("user/register.html", form=form, error=error)


@user_app.route("/login", methods=["GET", "POST"])
async def login() -> Union[str, Response]:
    form = await UserForm.create_form()
    error: Optional[str] = None

    if await form.validate_on_submit():
        engine = current_app.dbc  # type: ignore
        async with engine.begin() as conn:
            user = await get_user_by_username(conn, form.username.data)

        if user is None or not pbkdf2_sha256.verify(
            form.password.data, user.password
        ):
            error = "Invalid username or password"
        else:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("post_app.home"))

    return await render_template("user/login.html", form=form, error=error)


@user_app.route("/logout")
async def logout() -> Response:
    session.pop("user_id", None)
    session.pop("username", None)
    await flash("You have been logged out")
    return redirect(url_for(".login"))


@user_app.route("/user/<username>")
async def profile(username: str) -> str:
    engine = current_app.dbc  # type: ignore
    async with engine.begin() as conn:
        profile_user = await get_user_by_username(conn, username)
        if profile_user is None:
            abort(404)

        my_user_id = session.get("user_id")
        if profile_user.id == my_user_id:
            relationship = "self"
        elif my_user_id is not None and await is_following(
            conn, my_user_id, profile_user.id
        ):
            relationship = "following"
        else:
            relationship = "not_following"

        followers_result = await conn.execute(
            select(relationship_table).where(
                relationship_table.c.to_user_id == profile_user.id
            )
        )
        follower_count = len(followers_result.fetchall())

    follow_form = await EmptyForm.create_form()

    return await render_template(
        "user/profile.html",
        profile_user=profile_user,
        relationship=relationship,
        follower_count=follower_count,
        follow_form=follow_form,
    )
