import time
from pathlib import Path
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
    request,
    session,
    url_for,
)
from sqlalchemy import insert, select, update
from wand.image import Image

from helpers import get_user_by_id, get_user_by_username, image_url, login_required
from post.models import post_table
from relationship.models import relationship_table
from relationship.views import EmptyForm, followers, is_following
from user.forms import ProfileEditForm, UserForm
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

        # Never reveal whether it was the username or the password that
        # was wrong.
        if user is None or not pbkdf2_sha256.verify(form.password.data, user.password):
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
        elif my_user_id is not None and await is_following(conn, my_user_id, profile_user.id):
            relationship = "following"
        else:
            relationship = "not_following"

        follower_ids = await followers(conn, profile_user.id)
        following_result = await conn.execute(
            select(relationship_table).where(
                relationship_table.c.fm_user_id == profile_user.id
            )
        )
        following_count = len(following_result.fetchall())

        posts_result = await conn.execute(
            select(post_table)
            .where(post_table.c.user_id == profile_user.id)
            .order_by(post_table.c.created.desc())
            .limit(10)
        )
        posts = posts_result.fetchall()

    follow_form = await EmptyForm.create_form()

    return await render_template(
        "user/profile.html",
        profile_user=profile_user,
        relationship=relationship,
        follower_count=len(follower_ids),
        following_count=following_count,
        posts=posts,
        avatar_url=image_url(profile_user.id, profile_user.image),
        follow_form=follow_form,
    )


def _save_avatar(file_storage, user_id: int) -> int:
    """Resize the uploaded avatar with Wand/ImageMagick and save it to disk.

    Returns the unix timestamp used in the saved filename (also stored on
    ``user.image``).
    """
    ts = int(time.time())
    uploads_folder = Path(current_app.config["UPLOADS_FOLDER"])
    uploads_folder.mkdir(parents=True, exist_ok=True)
    dest = uploads_folder / f"{user_id}_{ts}.png"

    data = file_storage.read()
    with Image(blob=data) as img:
        img.transform(resize="200x200^")
        img.crop(width=200, height=200, gravity="center")
        img.format = "png"
        img.save(filename=str(dest))

    return ts


@user_app.route("/profile/edit", methods=["GET", "POST"])
@login_required
async def profile_edit() -> Union[str, Response]:
    form = await ProfileEditForm.create_form()
    error: Optional[str] = None
    engine = current_app.dbc  # type: ignore

    async with engine.begin() as conn:
        current_user = await get_user_by_id(conn, session["user_id"])

    if request.method == "GET":
        form.username.data = current_user.username

    if await form.validate_on_submit():
        new_username = form.username.data
        ts: Optional[int] = None
        if form.image.data:
            ts = _save_avatar(form.image.data, session["user_id"])

        async with engine.begin() as conn:
            if new_username != current_user.username:
                existing = await get_user_by_username(conn, new_username)
                if existing is not None and existing.id != session["user_id"]:
                    error = "Username already exists"

            if not error:
                values = {"username": new_username}
                if ts is not None:
                    values["image"] = ts
                await conn.execute(
                    update(user_table)
                    .where(user_table.c.id == session["user_id"])
                    .values(**values)
                )

        if not error:
            session["username"] = new_username
            await flash("Profile updated")
            return redirect(url_for(".profile", username=new_username))

    return await render_template(
        "user/profile_edit.html",
        form=form,
        avatar_url=image_url(current_user.id, current_user.image),
        error=error,
    )
