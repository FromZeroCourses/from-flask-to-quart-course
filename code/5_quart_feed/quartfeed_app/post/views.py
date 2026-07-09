from quart import Blueprint, redirect, render_template, session, url_for

post_app = Blueprint("post_app", __name__)


@post_app.route("/")
async def home():
    if session.get("username") is None:
        return redirect(url_for("user_app.login"))

    return await render_template("post/home.html")
