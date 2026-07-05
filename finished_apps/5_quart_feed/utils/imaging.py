"""Image processing with Wand/ImageMagick.

Two flavors:

* Avatars are square, so ``thumbnail_process`` center-crops to a square (off the
  wider side) and emits one PNG per size (sm/lg/xlg).
* Post images keep their aspect ratio but are scaled to a fixed HEIGHT
  (``image_height_transform``) so several can sit side-by-side at a uniform
  height — the FriendFeed post-image layout.

Files are written locally as ``{content_id}.{image_id}.{size}.png`` under a
per-kind folder; ``image_id`` is a unix timestamp stored on the owning row.
"""
import time
from pathlib import Path
from typing import List, Tuple, Union

from wand.image import Image

AVATAR_SIZES: List[Tuple[str, int]] = [("sm", 50), ("lg", 75), ("xlg", 200)]


def crop_center(image: Image) -> None:
    """Center-crop ``image`` to a square sized to its narrower dimension."""
    dst_landscape = 1 > image.width / image.height
    wh = image.width if dst_landscape else image.height
    image.crop(
        left=int((image.width - wh) / 2),
        top=int((image.height - wh) / 2),
        width=int(wh),
        height=int(wh),
    )


def thumbnail_process(
    blob: bytes,
    dest_dir: Union[str, Path],
    content_id: Union[str, int],
    sizes: List[Tuple[str, int]] = AVATAR_SIZES,
) -> int:
    """Square-crop ``blob`` and save one PNG per size. Returns the image_id."""
    image_id = int(time.time())
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for name, size in sizes:
        with Image(blob=blob) as img:
            crop_center(img)
            img.sample(size, size)
            img.format = "png"
            img.save(filename=str(dest / f"{content_id}.{image_id}.{name}.png"))
    return image_id


def image_height_transform(
    blob: bytes,
    dest_dir: Union[str, Path],
    content_id: Union[str, int],
    height: int = 200,
) -> Tuple[int, int]:
    """Scale ``blob`` to a fixed ``height`` (aspect kept). Returns (image_id, width)."""
    image_id = int(time.time())
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with Image(blob=blob) as img:
        img.transform(resize=f"x{height}")
        img.format = "png"
        img.save(filename=str(dest / f"{content_id}.{image_id}.xlg.png"))
        return image_id, img.width
