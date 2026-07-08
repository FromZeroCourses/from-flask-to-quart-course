from typing import Optional, Union

from passlib.hash import pbkdf2_sha256
from quart import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from sqlalchemy import insert, select

from utils.helpers import get_user_by_username
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
