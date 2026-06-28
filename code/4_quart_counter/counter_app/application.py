from quart import Quart

from db import get_engine


def create_app(**config_overrides):
    app = Quart(__name__)
    app.config.from_pyfile("settings.py")

    # apply overrides for tests
    app.config.update(config_overrides)

    from counter.views import counter_app

    app.register_blueprint(counter_app)

    @app.before_serving
    async def create_db_conn():
        app.dbc = get_engine()

    @app.after_serving
    async def close_db_conn():
        await app.dbc.dispose()

    return app
