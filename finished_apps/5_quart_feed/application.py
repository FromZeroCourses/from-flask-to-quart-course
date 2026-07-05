import random

from quart import Quart, url_for

from db import get_engine
from utils.helpers import likes_line, linkify, slugify


def create_app(**config_overrides):
    app = Quart(__name__)
    app.config.from_pyfile("settings.py")

    # apply overrides for tests
    app.config.update(config_overrides)

    from user.views import user_app
    from relationship.views import relationship_app
    from post.views import post_app
    from comment.views import comment_app
    from like.views import like_app

    app.register_blueprint(user_app)
    app.register_blueprint(relationship_app)
    app.register_blueprint(post_app)
    app.register_blueprint(comment_app)
    app.register_blueprint(like_app)

    @app.context_processor
    def inject_cache_buster():
        # A fresh value every request. Appended to static asset URLs as
        # ?cb=<n> so reloading the page always re-fetches the current JS/CSS
        # instead of a stale browser-cached copy — handy while students edit
        # files on the host and watch the page update.
        return {"cb": random.randint(0, 2**31 - 1)}

    @app.template_global()
    def post_url(uid: str, message: str) -> str:
        """Canonical SEO permalink for a post: /post/<uid>/<slug>."""
        return url_for("post_app.detail", uid=uid, slug=slugify(message))

    app.add_template_global(likes_line, "likes_line")
    app.add_template_filter(linkify, "linkify")

    @app.before_serving
    async def create_db_conn():
        app.dbc = get_engine()

    @app.after_serving
    async def close_db_conn():
        await app.dbc.dispose()

    return app
