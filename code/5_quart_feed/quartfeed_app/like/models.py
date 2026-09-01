from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint

from db import metadata

like_table = Table(
    "like",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),
)
