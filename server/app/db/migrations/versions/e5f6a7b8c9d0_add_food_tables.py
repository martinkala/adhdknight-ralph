"""add_food_tables: food diary days, entries, weights, blood pressures, meds dictionary (food-003)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    ]


def _user_fk() -> list:
    return [
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    ]


def _day_fk() -> list:
    return [
        sa.Column('day_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['food_days.id'], ondelete='CASCADE'),
    ]


def upgrade() -> None:
    op.create_table(
        'food_days',
        *_common_columns(),
        *_user_fk(),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        sa.Column('stool', sa.Integer(), nullable=True),
        sa.Column('gas', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_food_days_user_date'),
    )
    op.create_table(
        'food_entries',
        *_common_columns(),
        *_day_fk(),
        *_user_fk(),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('text', sa.String(length=200), nullable=False),
        sa.Column('text_norm', sa.String(length=200), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('unit', sa.String(length=5), nullable=True),
        sa.Column('intensity', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_food_entries_user_category_text_norm', 'food_entries', ['user_id', 'category', 'text_norm'])
    op.create_index('ix_food_entries_day_id', 'food_entries', ['day_id'])
    op.create_table(
        'food_weights',
        *_common_columns(),
        *_day_fk(),
        *_user_fk(),
        sa.Column('kg', sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column('measured_at', sa.String(length=5), nullable=True),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_food_weights_day_id', 'food_weights', ['day_id'])
    op.create_table(
        'food_blood_pressures',
        *_common_columns(),
        *_day_fk(),
        *_user_fk(),
        sa.Column('systolic', sa.Integer(), nullable=False),
        sa.Column('diastolic', sa.Integer(), nullable=False),
        sa.Column('pulse', sa.Integer(), nullable=True),
        sa.Column('measured_at', sa.String(length=5), nullable=True),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_food_blood_pressures_day_id', 'food_blood_pressures', ['day_id'])
    op.create_table(
        'food_med_dictionary',
        *_common_columns(),
        *_user_fk(),
        sa.Column('text_norm', sa.String(length=200), nullable=False),
        sa.Column('display_text', sa.String(length=200), nullable=False),
        sa.Column('kind', sa.String(length=12), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'text_norm', name='uq_food_med_dictionary_user_text_norm'),
    )


def downgrade() -> None:
    op.drop_table('food_med_dictionary')
    op.drop_index('ix_food_blood_pressures_day_id', table_name='food_blood_pressures')
    op.drop_table('food_blood_pressures')
    op.drop_index('ix_food_weights_day_id', table_name='food_weights')
    op.drop_table('food_weights')
    op.drop_index('ix_food_entries_day_id', table_name='food_entries')
    op.drop_index('ix_food_entries_user_category_text_norm', table_name='food_entries')
    op.drop_table('food_entries')
    op.drop_table('food_days')
