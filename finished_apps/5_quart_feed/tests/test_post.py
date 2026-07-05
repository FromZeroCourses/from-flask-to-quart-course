import pytest
from quart import current_app
from sqlalchemy import select

from comment.models import comment_table
from like.models import like_table
from post.models import feed_table, post_table


async def _register_and_login(client, username: str, password: str = "secret123") -> None:
    await client.post("/register", form={"username": username, "password": password})
    await client.post("/login", form={"username": username, "password": password})


@pytest.mark.asyncio
async def test_create_post_appears_in_own_feed(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")

    response = await create_test_client.post("/post", form={"message": "hello world"})
    assert response.status_code == 302

    home_response = await create_test_client.get("/")
    body = await home_response.get_data()
    assert "hello world" in str(body)

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            posts = (await conn.execute(select(post_table))).fetchall()
            assert len(posts) == 1
            feed_rows = (await conn.execute(select(feed_table))).fetchall()
            assert len(feed_rows) == 1  # the author's own feed row


@pytest.mark.asyncio
async def test_follower_sees_post_in_feed(create_test_app):
    alice_client = create_test_app.test_client()
    await _register_and_login(alice_client, "alice")

    bob_client = create_test_app.test_client()
    await _register_and_login(bob_client, "bob")

    await bob_client.post("/follow/alice")
    await alice_client.post("/post", form={"message": "hi followers"})

    home_response = await bob_client.get("/")
    body = await home_response.get_data()
    assert "hi followers" in str(body)

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            feed_rows = (await conn.execute(select(feed_table))).fetchall()
            # one for the author (alice) + one for the follower (bob)
            assert len(feed_rows) == 2


@pytest.mark.asyncio
async def test_comment_and_like_toggle(create_test_client, create_test_app):
    await _register_and_login(create_test_client, "alice")
    await create_test_client.post("/post", form={"message": "hello world"})

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            post_row = (await conn.execute(select(post_table))).fetchone()
    post_id = post_row.id

    comment_response = await create_test_client.post(
        f"/comment/{post_id}", form={"comment": "nice post!"}
    )
    assert comment_response.status_code == 302

    like_response = await create_test_client.post(f"/like/{post_id}")
    assert like_response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            comments = (await conn.execute(select(comment_table))).fetchall()
            assert len(comments) == 1
            assert comments[0].comment == "nice post!"

            likes = (await conn.execute(select(like_table))).fetchall()
            assert len(likes) == 1

    # Toggling like again removes it.
    await create_test_client.post(f"/like/{post_id}")

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            likes = (await conn.execute(select(like_table))).fetchall()
            assert len(likes) == 0


@pytest.mark.asyncio
async def test_post_requires_login(create_test_client):
    response = await create_test_client.post("/post", form={"message": "hi"})
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")
