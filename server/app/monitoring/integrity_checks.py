import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tracking import TrackingDay
from app.models.user import User
from app.monitoring.models import IntegritySnapshot, IntegrityWarning, IntegrityWarningMetric, UserDataVolumeSnapshot

logger = logging.getLogger("adhd.monitoring")


async def _current_counts(db: AsyncSession) -> tuple[int, dict[str, int]]:
    """Real (non-monitoring-account) users only — the monitoring account's own seeded
    activity must never look like anomalous growth."""
    user_ids = (
        (await db.execute(select(User.id).where(User.is_monitoring_account.is_(False))))
        .scalars()
        .all()
    )
    if not user_ids:
        return 0, {}

    rows = (
        await db.execute(
            select(TrackingDay.user_id, func.count(TrackingDay.id))
            .where(TrackingDay.user_id.in_(user_ids))
            .group_by(TrackingDay.user_id)
        )
    ).all()
    counts = {user_id: 0 for user_id in user_ids}
    counts.update({user_id: count for user_id, count in rows})
    return len(user_ids), counts


async def _previous_snapshot(db: AsyncSession) -> IntegritySnapshot | None:
    stmt = select(IntegritySnapshot).order_by(IntegritySnapshot.captured_at.desc()).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


async def capture_and_compare(db: AsyncSession) -> IntegritySnapshot:
    """FR-009/FR-011: capture the current snapshot; FR-010/FR-012: compare it against the
    most recent prior snapshot and raise IntegrityWarning rows on threshold breach.
    The very first check ever run has no prior snapshot — captures a baseline, no warnings."""
    settings = get_settings()
    previous = await _previous_snapshot(db)
    total_user_count, data_counts = await _current_counts(db)

    now = datetime.now(timezone.utc)
    snapshot = IntegritySnapshot(captured_at=now, total_user_count=total_user_count)
    db.add(snapshot)
    await db.flush()  # assigns snapshot.id for the FK below

    for user_id, count in data_counts.items():
        db.add(UserDataVolumeSnapshot(snapshot_id=snapshot.id, user_id=user_id, data_count=count))

    if previous is not None:
        user_growth = total_user_count - previous.total_user_count
        if user_growth > settings.integrity_user_count_growth_threshold:
            db.add(IntegrityWarning(
                raised_at=now,
                metric=IntegrityWarningMetric.user_count_growth,
                user_id=None,
                previous_value=previous.total_user_count,
                current_value=total_user_count,
                threshold=settings.integrity_user_count_growth_threshold,
            ))
            logger.warning(
                "integrity warning: user_count_growth previous=%d current=%d threshold=%d",
                previous.total_user_count, total_user_count, settings.integrity_user_count_growth_threshold,
            )

        previous_volumes = {
            v.user_id: v.data_count
            for v in (
                await db.execute(
                    select(UserDataVolumeSnapshot).where(UserDataVolumeSnapshot.snapshot_id == previous.id)
                )
            ).scalars().all()
        }
        for user_id, current_count in data_counts.items():
            previous_count = previous_volumes.get(user_id, 0)
            data_growth = current_count - previous_count
            if data_growth > settings.integrity_user_data_growth_threshold:
                db.add(IntegrityWarning(
                    raised_at=now,
                    metric=IntegrityWarningMetric.user_data_growth,
                    user_id=user_id,
                    previous_value=previous_count,
                    current_value=current_count,
                    threshold=settings.integrity_user_data_growth_threshold,
                ))
                logger.warning(
                    "integrity warning: user_data_growth user_id=%s previous=%d current=%d threshold=%d",
                    user_id, previous_count, current_count, settings.integrity_user_data_growth_threshold,
                )

    await db.commit()
    await db.refresh(snapshot)
    return snapshot
