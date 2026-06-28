from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from quart import current_app

metadata = MetaData()


def get_engine():
    c = current_app.config
    url = (
        f"postgresql+asyncpg://{c['DB_USERNAME']}:{c['DB_PASSWORD']}"
        f"@{c['DB_HOST']}:5432/{c['DATABASE_NAME']}"
    )
    return create_async_engine(url, pool_size=5, max_overflow=15)
