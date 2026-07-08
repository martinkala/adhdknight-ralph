"""add note to element_values

Revision ID: a1b2c3d4e5f6
Revises: 51a4112e7c48
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '51a4112e7c48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('element_values', sa.Column('note', sa.String(250), nullable=True))


def downgrade() -> None:
    op.drop_column('element_values', 'note')
