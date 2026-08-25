from quart import Quart, url_for

from db import get_engine
from utils.helpers import linkify, slugify


def create_app(**config_overrides):
    app = Quart(__name__)
    app.config.from_pyfile("settings.py")

    # apply overrides for tests
    app.config.update(config_overrides)

    from user.views import user_app
    from relationship.views import relationship_app
    from post.views import post_app
    from comment.views import comment_app

    app.register_blueprint(user_app)
    app.register_blueprint(relationship_app)
    app.register_blueprint(post_app)
    app.register_blueprint(comment_app)

    @app.template_global()
    def post_url(uid: str, message: str) -> str:
        """Canonical SEO permalink for a post: /post/<uid>/<slug>."""
        return url_for("post_app.detail", uid=uid, slug=slugify(message))

    app.add_template_filter(linkify, "linkify")

    @app.before_serving
    async def create_db_conn():
        app.dbc = get_engine()

    @app.after_serving
    async def close_db_conn():
        await app.dbc.dispose()

    return app
