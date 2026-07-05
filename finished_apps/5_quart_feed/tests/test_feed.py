import pytest
from quart import current_app
from sqlalchemy import select

from post.models import feed_table, post_table
from post.views import _load_feed
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


async def _only_post_id(app) -> int:
    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            row = (await conn.execute(select(post_table.c.id))).fetchone()
    return row.id


async def _feed_rows(app, user_id: int):
    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            return (
                await conn.execute(
                    select(feed_table).where(feed_table.c.user_id == user_id)
                )
            ).fetchall()


@pytest.mark.asyncio
async def test_comment_bubbles_post_to_commenters_followers(create_test_app):
    """A followee commenting surfaces a post you don't otherwise follow, attributed."""
    app = create_test_app
    author = app.test_client()
    await _register_and_login(author, "author")
    commenter = app.test_client()
    await _register_and_login(commenter, "commenter")
    viewer = app.test_client()
    await _register_and_login(viewer, "viewer")

    # viewer follows the commenter, but NOT the author
    await viewer.post("/follow/commenter")

    await author.post("/post", form={"message": "friend of a friend post"})
    viewer_id = await _user_id(app, "viewer")
    assert await _feed_rows(app, viewer_id) == []  # author isn't followed → not yet here

    # commenter (whom viewer follows) comments → the post bubbles into viewer's feed
    post_id = await _only_post_id(app)
    await commenter.post(f"/comment/{post_id}", form={"comment": "interesting"})

    rows = await _feed_rows(app, viewer_id)
    assert len(rows) == 1
    assert rows[0].post_id == post_id
    assert rows[0].reason_user_id == await _user_id(app, "commenter")
    assert rows[0].reason_type == "comment"

    # attribution resolves through _load_feed
    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            feed = await _load_feed(conn, viewer_id)
    assert len(feed) == 1
    assert feed[0]["reason_username"] == "commenter"
    assert feed[0]["reason_type"] == "comment"


@pytest.mark.asyncio
async def test_comment_does_not_bubble_to_unrelated_user(create_test_app):
    """Someone who follows neither the author nor the commenter gets nothing."""
    app = create_test_app
    author = app.test_client()
    await _register_and_login(author, "author")
    commenter = app.test_client()
    await _register_and_login(commenter, "commenter")
    stranger = app.test_client()
    await _register_and_login(stranger, "stranger")

    await author.post("/post", form={"message": "hello"})
    post_id = await _only_post_id(app)
    await commenter.post(f"/comment/{post_id}", form={"comment": "hi"})

    stranger_id = await _user_id(app, "stranger")
    assert await _feed_rows(app, stranger_id) == []


@pytest.mark.asyncio
async def test_bubble_dedups_against_direct_follow(create_test_app):
    """Following the author AND the commenter yields ONE feed row (direct wins)."""
    app = create_test_app
    author = app.test_client()
    await _register_and_login(author, "author")
    commenter = app.test_client()
    await _register_and_login(commenter, "commenter")
    viewer = app.test_client()
    await _register_and_login(viewer, "viewer")

    await viewer.post("/follow/author")
    await viewer.post("/follow/commenter")

    await author.post("/post", form={"message": "dedup me"})
    viewer_id = await _user_id(app, "viewer")
    rows = await _feed_rows(app, viewer_id)
    assert len(rows) == 1 and rows[0].reason_user_id is None  # direct follow, no reason

    post_id = await _only_post_id(app)
    await commenter.post(f"/comment/{post_id}", form={"comment": "hi"})

    rows = await _feed_rows(app, viewer_id)
    assert len(rows) == 1  # still one row, not duplicated
    assert rows[0].reason_user_id is None  # direct-follow row keeps its NULL reason
