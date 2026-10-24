"""add monitoring account flag to users, seed the monitoring account (FR-004)

Revision ID: 187ee05ae8ff
Revises: 0fe796b54aed
Create Date: 2026-08-18 20:20:38.492980

"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '187ee05ae8ff'
down_revision: Union[str, Sequence[str], None] = '0fe796b54aed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_DAYS = 3  # enough for a synthetic history check (FR-005) to confirm data is present


def upgrade() -> None:
    op.add_column('users', sa.Column('is_monitoring_account', sa.Boolean(), server_default='0', nullable=False))

    # Seed the dedicated monitoring account (FR-004) plus a few days of history so the
    # synthetic web-console check (FR-005) has real data to verify is returned, not just
    # a successful login. Credentials come from app config, not hardcoded, so ops can
    # rotate the password without a new migration.
    from app.config import get_settings
    from app.services.auth_service import hash_password

    settings = get_settings()
    bind = op.get_bind()

    users = sa.table(
        'users', sa.column('id'), sa.column('email'), sa.column('password_hash'),
        sa.column('created_at'), sa.column('is_active'), sa.column('is_monitoring_account'),
    )
    tracking_days = sa.table(
        'tracking_days', sa.column('id'), sa.column('user_id'), sa.column('app_id'),
        sa.column('date'), sa.column('is_complete'), sa.column('created_at'), sa.column('updated_at'),
    )
    daily_indices = sa.table(
        'daily_indices', sa.column('id'), sa.column('tracking_day_id'),
        sa.column('index_value'), sa.column('computed_at'), sa.column('config_version'),
    )

    existing = bind.execute(
        sa.select(users.c.id).where(users.c.email == settings.monitoring_account_email)
    ).first()
    if existing is not None:
        return

    now = datetime.now(timezone.utc)
    user_id = str(uuid.uuid4())
    bind.execute(users.insert().values(
        id=user_id,
        email=settings.monitoring_account_email,
        password_hash=hash_password(settings.monitoring_account_password),
        created_at=now,
        is_active=True,
        is_monitoring_account=True,
    ))

    for i in range(_SEED_DAYS):
        day_date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        day_id = str(uuid.uuid4())
        bind.execute(tracking_days.insert().values(
            id=day_id, user_id=user_id, app_id="adhd_tracker", date=day_date,
            is_complete=True, created_at=now, updated_at=now,
        ))
        bind.execute(daily_indices.insert().values(
            id=str(uuid.uuid4()), tracking_day_id=day_id,
            index_value=50.0, computed_at=now, config_version="1.0",
        ))


def downgrade() -> None:
    from app.config import get_settings

    settings = get_settings()
    bind = op.get_bind()
    users = sa.table('users', sa.column('id'), sa.column('email'))
    row = bind.execute(sa.select(users.c.id).where(users.c.email == settings.monitoring_account_email)).first()
    if row is not None:
        # tracking_days/daily_indices cascade-delete via ON DELETE CASCADE on the FK.
        bind.execute(sa.table('users', sa.column('id')).delete().where(sa.column('id') == row.id))

    op.drop_column('users', 'is_monitoring_account')
