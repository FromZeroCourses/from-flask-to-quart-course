from wand.color import Color
from wand.image import Image

from utils.imaging import (
    AVATAR_SIZES,
    crop_center,
    image_height_transform,
    thumbnail_process,
)


def _blob(width: int, height: int, color: str = "red") -> bytes:
    with Image(width=width, height=height, background=Color(color)) as img:
        img.format = "png"
        return img.make_blob()


def test_crop_center_squares_to_narrower_side():
    with Image(width=300, height=100, background=Color("blue")) as img:
        crop_center(img)
        assert img.width == img.height == 100


def test_thumbnail_process_writes_all_sizes(tmp_path):
    image_id = thumbnail_process(_blob(300, 100), tmp_path, "avatar42")
    for name, size in AVATAR_SIZES:
        f = tmp_path / f"avatar42.{image_id}.{name}.png"
        assert f.exists()
        with Image(filename=str(f)) as img:
            assert img.width == img.height == size  # square, exact size


def test_image_height_transform_fixes_height(tmp_path):
    # 400x200 scaled to a height of 100 keeps aspect -> 200x100
    image_id, width = image_height_transform(
        _blob(400, 200), tmp_path, "post7", height=100
    )
    f = tmp_path / f"post7.{image_id}.xlg.png"
    assert f.exists()
    with Image(filename=str(f)) as img:
        assert img.height == 100
        assert img.width == width == 200
