from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

from db import metadata

post_table = Table(
    "post",
    metadata,
    Column("id", Integer, primary_key=True),
    # Opaque, URL-safe id used in the SEO permalink (/post/<uid>/<slug>).
    Column("uid", String(16), nullable=False, unique=True, index=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("message", Text, nullable=False),
    Column("created", DateTime(timezone=True), server_default=func.now()),
)

feed_table = Table(
    "feed",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("updated", DateTime(timezone=True), server_default=func.now()),
    Column("reason_user_id", Integer, ForeignKey("user.id"), nullable=True),
    Column("reason_type", String(16), nullable=True),  # e.g. "comment"
    UniqueConstraint("user_id", "post_id", name="uq_feed_user_post"),
)

# Images attached to a post. One per post in the UI for now, but the table is
# multi-image ready: several rows (ordered by ``position``) render side-by-side
# at a uniform height. ``image_id`` is a timestamp; ``width`` is the scaled
# width so the layout can reserve space. File: posts/{post_id}.{image_id}.xlg.png
post_image_table = Table(
    "post_image",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("image_id", Integer, nullable=False),
    Column("width", Integer, nullable=False),
    Column("position", Integer, nullable=False),
)
