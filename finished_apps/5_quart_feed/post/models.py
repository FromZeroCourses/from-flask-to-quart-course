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

# Fan-out table: when a user posts, one feed row is inserted for every
# follower of that user AND for the user themselves. feed.user_id is the
# feed OWNER (the recipient), not the author.
#
# A post also surfaces ("bubbles") into your feed when someone you follow
# comments on it, even if you don't follow the author. reason_user_id /
# reason_type record WHY the post is in your feed so the card can show
# "(Robert Scoble commented on this)". A direct follow leaves them NULL.
#
# UNIQUE(user_id, post_id): a post appears at most once per feed. Following
# the author AND having a followee comment on it must not double-insert.
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
