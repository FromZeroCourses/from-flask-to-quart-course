import pytest
from quart import current_app
from sqlalchemy import select

from counter.models import counter_table


@pytest.mark.asyncio
async def test_initial_response(create_test_client):
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 1" in str(body)


@pytest.mark.asyncio
async def test_second_response(create_test_client, create_test_app):
    # First hit sets the counter to 1
    await create_test_client.get("/")

    # Second hit should bump it to 2
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 2" in str(body)

    # Verify directly against the model/database
    async with create_test_app.app_context():
        async with current_app.dbc.begin() as conn:
            result = (await conn.execute(select(counter_table))).fetchall()
            assert result[0].count == 2
