"""comments and feed bubbling

Revision ID: e5b7c3a91d42
Revises: ad6b0951f001
Create Date: 2026-08-24 22:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5b7c3a91d42'
down_revision: Union[str, Sequence[str], None] = 'ad6b0951f001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('feed', sa.Column('reason_user_id', sa.Integer(), nullable=True))
    op.add_column('feed', sa.Column('reason_type', sa.String(length=16), nullable=True))
    op.create_foreign_key(None, 'feed', 'user', ['reason_user_id'], ['id'])
    op.create_unique_constraint('uq_feed_user_post', 'feed', ['user_id', 'post_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_feed_user_post', 'feed', type_='unique')
    op.drop_constraint(None, 'feed', type_='foreignkey')
    op.drop_column('feed', 'reason_type')
    op.drop_column('feed', 'reason_user_id')
    op.drop_table('comment')
