from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import require_monitoring_operator
from app.monitoring.models import IntegritySnapshot, IntegrityWarning, MonitoringCheckResult, MonitoringTarget
from app.monitoring.synthetic_checks import get_consecutive_failures

router = APIRouter(
    prefix="/internal/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(require_monitoring_operator)],
)


class CheckStatus(BaseModel):
    checked_at: datetime
    success: bool
    error_detail: str | None
    consecutive_failures: int


class IntegritySnapshotSummary(BaseModel):
    captured_at: datetime
    total_user_count: int


class WarningSummary(BaseModel):
    raised_at: datetime
    metric: str
    user_id: str | None
    previous_value: int
    current_value: int
    threshold: int


class MonitoringStatusResponse(BaseModel):
    last_web_console_check: CheckStatus | None
    last_api_check: CheckStatus | None
    last_integrity_snapshot: IntegritySnapshotSummary | None
    recent_warnings: list[WarningSummary]


async def _last_check_status(db: AsyncSession, target: MonitoringTarget) -> CheckStatus | None:
    stmt = (
        select(MonitoringCheckResult)
        .where(MonitoringCheckResult.target == target)
        .order_by(MonitoringCheckResult.checked_at.desc())
        .limit(1)
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    if result is None:
        return None
    return CheckStatus(
        checked_at=result.checked_at,
        success=result.success,
        error_detail=result.error_detail,
        consecutive_failures=await get_consecutive_failures(db, target),
    )


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(db: AsyncSession = Depends(get_db)):
    last_web_console_check = await _last_check_status(db, MonitoringTarget.web_console)
    last_api_check = await _last_check_status(db, MonitoringTarget.api)

    snapshot_stmt = select(IntegritySnapshot).order_by(IntegritySnapshot.captured_at.desc()).limit(1)
    snapshot = (await db.execute(snapshot_stmt)).scalar_one_or_none()
    last_integrity_snapshot = (
        IntegritySnapshotSummary(captured_at=snapshot.captured_at, total_user_count=snapshot.total_user_count)
        if snapshot is not None
        else None
    )

    warnings_stmt = select(IntegrityWarning).order_by(IntegrityWarning.raised_at.desc()).limit(20)
    warnings = (await db.execute(warnings_stmt)).scalars().all()

    return MonitoringStatusResponse(
        last_web_console_check=last_web_console_check,
        last_api_check=last_api_check,
        last_integrity_snapshot=last_integrity_snapshot,
        recent_warnings=[
            WarningSummary(
                raised_at=w.raised_at,
                metric=w.metric.value,
                user_id=w.user_id,
                previous_value=w.previous_value,
                current_value=w.current_value,
                threshold=w.threshold,
            )
            for w in warnings
        ],
    )
