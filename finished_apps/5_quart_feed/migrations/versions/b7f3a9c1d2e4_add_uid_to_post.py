"""add uid to post

Revision ID: b7f3a9c1d2e4
Revises: 4622ef52e361
Create Date: 2026-07-05 16:10:00.000000

"""
import secrets
import string
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7f3a9c1d2e4'
down_revision: Union[str, Sequence[str], None] = '4622ef52e361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UID_ALPHABET = string.ascii_lowercase + string.digits


def _uid(length: int = 8) -> str:
    return "".join(secrets.choice(_UID_ALPHABET) for _ in range(length))


def upgrade() -> None:
    """Add the permalink uid, backfilling existing rows before enforcing NOT NULL."""
    # 1) add nullable so existing posts are allowed while we backfill
    op.add_column('post', sa.Column('uid', sa.String(length=16), nullable=True))

    # 2) give every existing post a unique uid
    conn = op.get_bind()
    ids = [row.id for row in conn.execute(sa.text("SELECT id FROM post"))]
    used: set[str] = set()
    for post_id in ids:
        uid = _uid()
        while uid in used:
            uid = _uid()
        used.add(uid)
        conn.execute(
            sa.text("UPDATE post SET uid = :uid WHERE id = :id"),
            {"uid": uid, "id": post_id},
        )

    # 3) enforce NOT NULL + uniqueness now that no row is null
    op.alter_column('post', 'uid', existing_type=sa.String(length=16), nullable=False)
    op.create_index(op.f('ix_post_uid'), 'post', ['uid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_post_uid'), table_name='post')
    op.drop_column('post', 'uid')
