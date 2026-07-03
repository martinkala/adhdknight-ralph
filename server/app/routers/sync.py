from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.tracking import TrackingDay
from app.schemas.sync import BatchSyncRequest, BatchSyncResponse, SyncSummary
from app.services.sync_service import process_batch_sync

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.post("/batch", response_model=BatchSyncResponse)
async def batch_sync(
    body: BatchSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await process_batch_sync(
        user_id=current_user.id,
        days=body.days,
        device_id=body.device_id,
        db=db,
    )
    return BatchSyncResponse(
        sync_id=result.sync_id,
        summary=SyncSummary(
            days_received=len(body.days),
            records_sent=result.records_sent,
            records_accepted=result.records_accepted,
            records_conflicted=result.records_conflicted,
            records_rejected=result.records_rejected,
        ),
        conflicts=result.conflicts,
        computed_indices=result.computed_indices,
    )


@router.get("/status")
async def sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TrackingDay).where(TrackingDay.user_id == current_user.id)
    result = await db.execute(stmt)
    days = result.scalars().all()
    return {"user_id": current_user.id, "total_days_synced": len(days)}
