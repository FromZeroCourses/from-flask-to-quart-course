import pytest
from quart import current_app
from sqlalchemy import select, update

from relationship.models import relationship_table
from user.models import user_table


async def _register_and_login(client, username: str, password: str = "secret123") -> None:
    await client.post("/register", form={"username": username, "password": password})
    await client.post("/login", form={"username": username, "password": password})


@pytest.mark.asyncio
async def test_follow_and_unfollow(create_test_app):
    alice_client = create_test_app.test_client()
    await _register_and_login(alice_client, "alice")

    bob_client = create_test_app.test_client()
    await _register_and_login(bob_client, "bob")

    response = await alice_client.post("/follow/bob")
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            rows = (await conn.execute(select(relationship_table))).fetchall()
            assert len(rows) == 1

    response = await alice_client.post("/unfollow/bob")
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            rows = (await conn.execute(select(relationship_table))).fetchall()
            assert len(rows) == 0


@pytest.mark.asyncio
async def test_follow_requires_login(create_test_client):
    response = await create_test_client.post("/follow/nobody")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


@pytest.mark.asyncio
async def test_profile_shows_relationship_state(create_test_app):
    alice_client = create_test_app.test_client()
    await _register_and_login(alice_client, "alice")

    bob_client = create_test_app.test_client()
    await _register_and_login(bob_client, "bob")

    response = await alice_client.get("/user/bob")
    body = await response.get_data()
    assert "Follow" in str(body)

    await alice_client.post("/follow/bob")

    response = await alice_client.get("/user/bob")
    body = await response.get_data()
    assert "Unfollow" in str(body)


@pytest.mark.asyncio
async def test_followers_list(create_test_app):
    alice_client = create_test_app.test_client()
    await _register_and_login(alice_client, "alice")

    bob_client = create_test_app.test_client()
    await _register_and_login(bob_client, "bob")

    await alice_client.post("/follow/bob")

    response = await bob_client.get("/user/bob/followers")
    body = str(await response.get_data())
    assert "alice" in body
    assert "<img" in body

    response = await alice_client.get("/user/alice/following")
    body = str(await response.get_data())
    assert "bob" in body


@pytest.mark.asyncio
async def test_follow_lists_empty(create_test_app):
    client = create_test_app.test_client()
    await _register_and_login(client, "carol")

    response = await client.get("/user/carol/followers")
    body = str(await response.get_data())
    assert "No followers yet" in body

    response = await client.get("/user/carol/following")
    body = str(await response.get_data())
    assert "Not following anyone yet" in body


@pytest.mark.asyncio
async def test_delete_image(create_test_app):
    client = create_test_app.test_client()
    await _register_and_login(client, "dave")

    # Give dave a custom avatar (non-null image timestamp) directly in the DB.
    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            await conn.execute(
                update(user_table)
                .where(user_table.c.username == "dave")
                .values(image=1783000000)
            )

    response = await client.post("/profile/delete-image")
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            row = (
                await conn.execute(
                    select(user_table).where(user_table.c.username == "dave")
                )
            ).fetchone()
            assert row.image is None

    response = await client.get("/user/dave")
    body = str(await response.get_data())
    assert "/static/default_profile.png" in body
