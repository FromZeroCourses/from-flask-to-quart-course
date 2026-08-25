from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text, func

from db import metadata

comment_table = Table(
    "comment",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("comment", Text, nullable=False),
    Column("created", DateTime(timezone=True), server_default=func.now()),
)
