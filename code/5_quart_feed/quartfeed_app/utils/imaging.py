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
