import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.config import get_settings
from app.models.tracking import TrackingDay
from app.models.user import User
from app.monitoring.integrity_checks import capture_and_compare
from app.monitoring.models import IntegritySnapshot, IntegrityWarning, IntegrityWarningMetric, UserDataVolumeSnapshot


@pytest_asyncio.fixture(autouse=True)
async def _clear_integrity_tables(db_session):
    """Snapshot comparisons are relative (this-check vs. previous-check), so tests don't
    need a clean `users`/`tracking_days` table — but they do need a clean integrity-table
    slate so "no prior snapshot" is actually true and warnings from other tests don't leak."""
    await db_session.execute(delete(IntegrityWarning))
    await db_session.execute(delete(UserDataVolumeSnapshot))
    await db_session.execute(delete(IntegritySnapshot))
    await db_session.commit()
    yield


async def _make_user(db_session) -> User:
    user = User(id=str(uuid.uuid4()), email=f"integrity-{uuid.uuid4()}@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    return user


async def _add_tracking_days(db_session, user: User, count: int) -> None:
    base = date(2020, 1, 1)
    for i in range(count):
        db_session.add(TrackingDay(
            id=str(uuid.uuid4()), user_id=user.id, app_id="adhd_tracker",
            date=(base + timedelta(days=i)).isoformat(),
        ))
    await db_session.commit()


async def _all_warnings(db_session):
    return (await db_session.execute(select(IntegrityWarning))).scalars().all()


@pytest.mark.asyncio
async def test_first_check_ever_captures_baseline_without_error(db_session):
    snapshot = await capture_and_compare(db_session)
    assert snapshot.id is not None
    assert await _all_warnings(db_session) == []


@pytest.mark.asyncio
async def test_user_count_growth_over_threshold_raises_warning(db_session):
    settings = get_settings()
    baseline = await capture_and_compare(db_session)

    for _ in range(settings.integrity_user_count_growth_threshold + 1):
        await _make_user(db_session)

    await capture_and_compare(db_session)

    warnings = [w for w in await _all_warnings(db_session) if w.metric == IntegrityWarningMetric.user_count_growth]
    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.previous_value == baseline.total_user_count
    assert warning.current_value - warning.previous_value == settings.integrity_user_count_growth_threshold + 1
    assert warning.threshold == settings.integrity_user_count_growth_threshold


@pytest.mark.asyncio
async def test_user_data_growth_over_threshold_identifies_correct_user(db_session):
    settings = get_settings()
    user = await _make_user(db_session)
    await capture_and_compare(db_session)  # baseline: user has 0 tracking days

    await _add_tracking_days(db_session, user, settings.integrity_user_data_growth_threshold + 1)
    await capture_and_compare(db_session)

    stmt = select(IntegrityWarning).where(
        IntegrityWarning.metric == IntegrityWarningMetric.user_data_growth,
        IntegrityWarning.user_id == user.id,
    )
    warning = (await db_session.execute(stmt)).scalar_one()
    assert warning.previous_value == 0
    assert warning.current_value == settings.integrity_user_data_growth_threshold + 1
    assert warning.threshold == settings.integrity_user_data_growth_threshold


@pytest.mark.asyncio
async def test_growth_within_threshold_raises_no_warning(db_session):
    settings = get_settings()
    user = await _make_user(db_session)
    await capture_and_compare(db_session)

    await _add_tracking_days(db_session, user, settings.integrity_user_data_growth_threshold)  # exactly at, not over
    await capture_and_compare(db_session)

    stmt = select(IntegrityWarning).where(IntegrityWarning.user_id == user.id)
    assert (await db_session.execute(stmt)).scalars().all() == []
