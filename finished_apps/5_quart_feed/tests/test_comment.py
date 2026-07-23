import pytest
from quart import current_app
from sqlalchemy import select

from comment.models import comment_table
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
async def test_create_comment(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")
    post_id = await _make_post(create_test_client, create_test_app)

    response = await create_test_client.post(
        f"/comment/{post_id}", form={"comment": "nice post!"}
    )
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            comments = (await conn.execute(select(comment_table))).fetchall()
    assert len(comments) == 1
    assert comments[0].comment == "nice post!"


@pytest.mark.asyncio
async def test_empty_comment_is_rejected(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")
    post_id = await _make_post(create_test_client, create_test_app)

    # An empty comment fails validation, so no row is written.
    await create_test_client.post(f"/comment/{post_id}", form={"comment": ""})

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            comments = (await conn.execute(select(comment_table))).fetchall()
    assert comments == []


@pytest.mark.asyncio
async def test_comment_requires_login(create_test_client):
    response = await create_test_client.post("/comment/1", form={"comment": "hi"})
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")
