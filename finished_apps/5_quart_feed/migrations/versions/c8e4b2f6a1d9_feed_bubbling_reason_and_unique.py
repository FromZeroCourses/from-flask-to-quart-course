"""feed bubbling: reason columns + unique(user_id, post_id)

Revision ID: c8e4b2f6a1d9
Revises: b7f3a9c1d2e4
Create Date: 2026-07-05 16:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c8e4b2f6a1d9'
down_revision: Union[str, Sequence[str], None] = 'b7f3a9c1d2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bubbling attribution + enforce one feed row per (user, post)."""
    op.add_column('feed', sa.Column('reason_user_id', sa.Integer(), nullable=True))
    op.add_column('feed', sa.Column('reason_type', sa.String(length=16), nullable=True))
    op.create_foreign_key(
        'fk_feed_reason_user', 'feed', 'user', ['reason_user_id'], ['id']
    )

    # Collapse any pre-existing duplicate (user_id, post_id) rows, keeping the
    # earliest, before the unique constraint can be applied.
    op.execute(
        """
        DELETE FROM feed a USING feed b
        WHERE a.user_id = b.user_id AND a.post_id = b.post_id AND a.id > b.id
        """
    )
    op.create_unique_constraint('uq_feed_user_post', 'feed', ['user_id', 'post_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_feed_user_post', 'feed', type_='unique')
    op.drop_constraint('fk_feed_reason_user', 'feed', type_='foreignkey')
    op.drop_column('feed', 'reason_type')
    op.drop_column('feed', 'reason_user_id')
