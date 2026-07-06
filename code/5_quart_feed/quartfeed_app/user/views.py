from quart import Blueprint

user_app = Blueprint("user_app", __name__)


@user_app.route("/register")
async def register() -> str:
    return "<h1>User Registration</h1>"
