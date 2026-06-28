import os

import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv(".quartenv")

from application import create_app
from db import metadata


@pytest_asyncio.fixture
async def create_db():
    print("Creating db")
    db_name = os.environ["DATABASE_NAME"]
    db_host = os.environ["DB_HOST"]
    db_username = os.environ["DB_USERNAME"]
    db_password = os.environ["DB_PASSWORD"]

    base_uri = f"postgresql+asyncpg://{db_username}:{db_password}@{db_host}:5432/"
    test_db_name = db_name + "_test"

    # CREATE/DROP DATABASE must run outside a transaction (AUTOCOMMIT)
    admin = create_async_engine(base_uri + db_name, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)"))
        await conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    await admin.dispose()

    print("Creating test tables")
    engine = create_async_engine(base_uri + test_db_name)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await engine.dispose()

    yield {
        "DB_USERNAME": db_username,
        "DB_PASSWORD": db_password,
        "DB_HOST": db_host,
        "DATABASE_NAME": test_db_name,
        "TESTING": True,
    }

    print("Destroying db")
    admin = create_async_engine(base_uri + db_name, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)"))
    await admin.dispose()


@pytest_asyncio.fixture
async def create_test_app(create_db):
    app = create_app(**create_db)
    await app.startup()
    yield app
    await app.shutdown()


@pytest_asyncio.fixture
async def create_test_client(create_test_app):
    print("Creating test client")
    return create_test_app.test_client()
