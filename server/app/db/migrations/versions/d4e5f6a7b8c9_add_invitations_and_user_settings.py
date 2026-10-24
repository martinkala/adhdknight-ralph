"""add invitations table, users.language and users.timezone (food-002)

Revision ID: d4e5f6a7b8c9
Revises: 187ee05ae8ff
Create Date: 2026-10-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '187ee05ae8ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'invitations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_by_user_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['used_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('language', sa.String(length=5), nullable=False, server_default='sk'))
        batch_op.add_column(
            sa.Column('timezone', sa.String(length=64), nullable=False, server_default='Europe/Bratislava')
        )


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('timezone')
        batch_op.drop_column('language')
    op.drop_table('invitations')
