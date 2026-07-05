import pytest
from quart import current_app
from sqlalchemy import select

from user.models import user_table


@pytest.mark.asyncio
async def test_register_page_loads(create_test_client):
    response = await create_test_client.get("/register")
    body = await response.get_data()
    assert "Registration" in str(body)


@pytest.mark.asyncio
async def test_register_creates_user(create_test_client, create_test_app):
    response = await create_test_client.post(
        "/register", form={"username": "alice", "password": "secret123"}
    )
    assert response.status_code == 302

    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            row = (
                await conn.execute(
                    select(user_table).where(user_table.c.username == "alice")
                )
            ).fetchone()
            assert row is not None
            assert row.password != "secret123"  # stored hashed, not plaintext


@pytest.mark.asyncio
async def test_register_duplicate_username(create_test_client):
    await create_test_client.post(
        "/register", form={"username": "bob", "password": "secret123"}
    )
    response = await create_test_client.post(
        "/register", form={"username": "bob", "password": "secret123"}
    )
    body = await response.get_data()
    assert "User already exists" in str(body)


@pytest.mark.asyncio
async def test_register_missing_fields(create_test_client):
    response = await create_test_client.post(
        "/register", form={"username": "", "password": ""}
    )
    body = await response.get_data()
    assert "This field is required." in str(body)


@pytest.mark.asyncio
async def test_login_success(create_test_client):
    await create_test_client.post(
        "/register", form={"username": "carol", "password": "secret123"}
    )
    response = await create_test_client.post(
        "/login", form={"username": "carol", "password": "secret123"}
    )
    assert response.status_code == 302

    home_response = await create_test_client.get("/")
    body = await home_response.get_data()
    assert "QuartFeed" in str(body)


@pytest.mark.asyncio
async def test_login_unknown_user(create_test_client):
    response = await create_test_client.post(
        "/login", form={"username": "nobody", "password": "whatever"}
    )
    body = await response.get_data()
    assert "Invalid username or password" in str(body)


@pytest.mark.asyncio
async def test_login_wrong_password(create_test_client):
    await create_test_client.post(
        "/register", form={"username": "dave", "password": "secret123"}
    )
    response = await create_test_client.post(
        "/login", form={"username": "dave", "password": "wrongpassword"}
    )
    body = await response.get_data()
    assert "Invalid username or password" in str(body)


@pytest.mark.asyncio
async def test_logout(create_test_client):
    await create_test_client.post(
        "/register", form={"username": "erin", "password": "secret123"}
    )
    await create_test_client.post(
        "/login", form={"username": "erin", "password": "secret123"}
    )

    response = await create_test_client.get("/logout")
    assert response.status_code == 302

    # No longer logged in -> home redirects to login.
    home_response = await create_test_client.get("/")
    assert home_response.status_code == 302


@pytest.mark.asyncio
async def test_profile_edit_requires_login(create_test_client):
    response = await create_test_client.get("/profile/edit")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")
