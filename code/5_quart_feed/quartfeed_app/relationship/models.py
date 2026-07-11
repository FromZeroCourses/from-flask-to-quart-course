from sqlalchemy import Column, ForeignKey, Integer, Table

from db import metadata

# Unidirectional follow (Twitter-style): fm_user_id follows to_user_id.
relationship_table = Table(
    "relationship",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fm_user_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("to_user_id", Integer, ForeignKey("user.id"), nullable=False),
)
