import pytest
from quart import current_app
from sqlalchemy import select

from relationship.models import relationship_table


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
