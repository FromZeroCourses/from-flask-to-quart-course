import io

import pytest
from quart import current_app
from sqlalchemy import select
from wand.color import Color
from wand.image import Image
from werkzeug.datastructures import FileStorage

from post.models import post_image_table


async def _register_and_login(client, username: str, password: str = "secret123") -> None:
    await client.post("/register", form={"username": username, "password": password})
    await client.post("/login", form={"username": username, "password": password})


def _img_blob(width: int, height: int) -> bytes:
    with Image(width=width, height=height, background=Color("green")) as img:
        img.format = "png"
        return img.make_blob()


@pytest.mark.asyncio
async def test_create_post_with_image(create_test_app, tmp_path):
    app = create_test_app
    app.config["UPLOADS_FOLDER"] = str(tmp_path)

    client = app.test_client()
    await _register_and_login(client, "shooter")

    # 400x800 scaled to a fixed height of 200 -> 100x200
    resp = await client.post(
        "/post",
        form={"message": "look at this"},
        files={
            "image": FileStorage(
                stream=io.BytesIO(_img_blob(400, 800)),
                filename="pic.png",
                content_type="image/png",
            )
        },
    )
    assert resp.status_code == 302

    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            rows = (await conn.execute(select(post_image_table))).fetchall()

    assert len(rows) == 1
    row = rows[0]
    saved = tmp_path / "posts" / f"{row.post_id}.{row.image_id}.xlg.png"
    assert saved.exists()
    with Image(filename=str(saved)) as img:
        assert img.height == 200  # fixed height
        assert img.width == row.width == 100  # aspect preserved (400x800 -> 100x200)


@pytest.mark.asyncio
async def test_post_without_image_has_no_post_image_rows(create_test_app, tmp_path):
    app = create_test_app
    app.config["UPLOADS_FOLDER"] = str(tmp_path)

    client = app.test_client()
    await _register_and_login(client, "texter")
    resp = await client.post("/post", form={"message": "just words"})
    assert resp.status_code == 302

    async with app.app_context():
        async with current_app.dbc.begin() as conn:
            rows = (await conn.execute(select(post_image_table))).fetchall()
    assert rows == []
