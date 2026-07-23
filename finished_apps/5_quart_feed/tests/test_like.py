import pytest
from quart import current_app
from sqlalchemy import select

from like.models import like_table
from post.models import post_table


async def _register_and_login(client, username: str, password: str = "secret123") -> None:
    await client.post("/register", form={"username": username, "password": password})
    await client.post("/login", form={"username": username, "password": password})


async def _make_post(client, app, message: str = "hello world") -> int:
    await client.post("/post", form={"message": message})
    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            row = (await conn.execute(select(post_table))).fetchone()
    return row.id


@pytest.mark.asyncio
async def test_like_adds_row(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")
    post_id = await _make_post(create_test_client, create_test_app)

    response = await create_test_client.post(f"/like/{post_id}")
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            likes = (await conn.execute(select(like_table))).fetchall()
    assert len(likes) == 1


@pytest.mark.asyncio
async def test_like_toggles_off(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")
    post_id = await _make_post(create_test_client, create_test_app)

    await create_test_client.post(f"/like/{post_id}")  # like
    await create_test_client.post(f"/like/{post_id}")  # unlike

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            likes = (await conn.execute(select(like_table))).fetchall()
    assert len(likes) == 0


@pytest.mark.asyncio
async def test_like_requires_login(create_test_client):
    response = await create_test_client.post("/like/1")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")
