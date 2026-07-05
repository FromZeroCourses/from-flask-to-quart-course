from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text, func

from db import metadata

post_table = Table(
    "post",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("message", Text, nullable=False),
    Column("created", DateTime(timezone=True), server_default=func.now()),
)

# Fan-out table: when a user posts, one feed row is inserted for every
# follower of that user AND for the user themselves. feed.user_id is the
# feed OWNER (the recipient), not the author.
feed_table = Table(
    "feed",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("post_id", Integer, ForeignKey("post.id"), nullable=False),
    Column("updated", DateTime(timezone=True), server_default=func.now()),
)
