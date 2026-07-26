"""add app_id scoping to tracking_days, weight_configs, sync_records

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tracking_days') as batch_op:
        batch_op.add_column(sa.Column('app_id', sa.String(50), nullable=False, server_default='adhd_tracker'))
        batch_op.drop_constraint('uq_user_date', type_='unique')
        batch_op.create_unique_constraint('uq_user_app_date', ['user_id', 'app_id', 'date'])

    with op.batch_alter_table('weight_configs') as batch_op:
        batch_op.add_column(sa.Column('app_id', sa.String(50), nullable=False, server_default='adhd_tracker'))
        batch_op.drop_constraint('uq_user_element_weight', type_='unique')
        batch_op.create_unique_constraint('uq_user_app_element_weight', ['user_id', 'app_id', 'element_key'])

    with op.batch_alter_table('sync_records') as batch_op:
        batch_op.add_column(sa.Column('app_id', sa.String(50), nullable=False, server_default='adhd_tracker'))


def downgrade() -> None:
    with op.batch_alter_table('sync_records') as batch_op:
        batch_op.drop_column('app_id')

    with op.batch_alter_table('weight_configs') as batch_op:
        batch_op.drop_constraint('uq_user_app_element_weight', type_='unique')
        batch_op.drop_column('app_id')
        batch_op.create_unique_constraint('uq_user_element_weight', ['user_id', 'element_key'])

    with op.batch_alter_table('tracking_days') as batch_op:
        batch_op.drop_constraint('uq_user_app_date', type_='unique')
        batch_op.drop_column('app_id')
        batch_op.create_unique_constraint('uq_user_date', ['user_id', 'date'])
