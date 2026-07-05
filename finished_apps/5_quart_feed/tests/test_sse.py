import pytest
from quart import current_app
from sqlalchemy import select

from utils.sse import ServerSentEvent, broker
from user.models import user_table


async def _register_and_login(client, username: str, password: str = "secret123") -> None:
    await client.post("/register", form={"username": username, "password": password})
    await client.post("/login", form={"username": username, "password": password})


async def _user_id(app, username: str) -> int:
    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            row = (
                await conn.execute(
                    select(user_table.c.id).where(user_table.c.username == username)
                )
            ).fetchone()
    return row.id


@pytest.mark.asyncio
async def test_broker_delivers_only_to_addressed_user():
    """Unit: publish(user_id) reaches only that user's queues, not everyone's."""
    q_one = broker.subscribe(1)
    q_two = broker.subscribe(2)
    try:
        await broker.publish(1, ServerSentEvent(event="post", data="{}"))
        assert q_one.qsize() == 1
        assert q_two.qsize() == 0
    finally:
        broker.unsubscribe(1, q_one)
        broker.unsubscribe(2, q_two)


@pytest.mark.asyncio
async def test_sse_post_not_delivered_to_non_follower(create_test_app):
    """A post must NOT be pushed live to a user who does not follow the author.

    Regression for the leak where a single global broadcast pushed every post
    to every open feed. Non-followers briefly saw posts that then disappeared
    on refresh, because the persisted ``feed`` fan-out is follower-scoped.
    """
    carol_client = create_test_app.test_client()
    await _register_and_login(carol_client, "carol")

    jorge_client = create_test_app.test_client()
    await _register_and_login(jorge_client, "jorge")

    carol_id = await _user_id(create_test_app, "carol")
    jorge_id = await _user_id(create_test_app, "jorge")

    # jorge does NOT follow carol. Both have a live SSE connection open.
    q_carol = broker.subscribe(carol_id)
    q_jorge = broker.subscribe(jorge_id)
    try:
        await carol_client.post(
            "/post", form={"message": "I need to go to the supermarket"}
        )
        # carol sees her own post live; jorge (a non-follower) must not.
        assert q_carol.qsize() == 1
        assert q_jorge.qsize() == 0
    finally:
        broker.unsubscribe(carol_id, q_carol)
        broker.unsubscribe(jorge_id, q_jorge)


@pytest.mark.asyncio
async def test_sse_post_delivered_to_follower(create_test_app):
    """A follower DOES receive the author's post live over SSE."""
    carol_client = create_test_app.test_client()
    await _register_and_login(carol_client, "carol")

    dave_client = create_test_app.test_client()
    await _register_and_login(dave_client, "dave")

    await dave_client.post("/follow/carol")

    carol_id = await _user_id(create_test_app, "carol")
    dave_id = await _user_id(create_test_app, "dave")

    q_dave = broker.subscribe(dave_id)
    try:
        await carol_client.post("/post", form={"message": "hello followers"})
        assert q_dave.qsize() == 1
    finally:
        broker.unsubscribe(dave_id, q_dave)
