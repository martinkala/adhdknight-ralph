from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime
import json

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.tracking import TrackingDay, DailyIndex

router = APIRouter(prefix="/api/v1/user", tags=["user"])


class DayDebugItem(BaseModel):
    date: str
    element_count: int
    is_complete: bool
    day_updated_at: datetime
    device_id: str | None
    has_daily_index: bool
    index_value: float | None
    index_computed_at: datetime | None


class DebugResponse(BaseModel):
    schema_version: str = "1.0"
    app_id: str
    email: str
    total_days: int
    days_with_index: int
    days: list[DayDebugItem]


class DetailItem(BaseModel):
    element_key: str
    value_effective: float
    weight: float
    contribution: float
    impact: int


class HistoryDay(BaseModel):
    date: str
    index_value: float | None
    detail: list[DetailItem]


class HistoryResponse(BaseModel):
    schema_version: str = "1.0"
    days: list[HistoryDay]
    total_days: int


class MeResponse(BaseModel):
    email: str
    created_at: datetime
    total_days: int


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    days: int = Query(default=30, ge=1, le=90),
    app_id: str = Query(default="adhd_tracker"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TrackingDay)
        .where(TrackingDay.user_id == current_user.id, TrackingDay.app_id == app_id)
        .options(selectinload(TrackingDay.daily_index))
        .order_by(TrackingDay.date.desc())
        .limit(days)
    )
    result = await db.execute(stmt)
    tracking_days = result.scalars().all()

    history: list[HistoryDay] = []
    for day in tracking_days:
        index_val = None
        detail_items: list[DetailItem] = []
        if day.daily_index:
            index_val = day.daily_index.index_value
            if day.daily_index.detail_json:
                try:
                    raw = json.loads(day.daily_index.detail_json)
                    detail_items = [DetailItem(**item) for item in raw]
                except Exception:
                    pass
        history.append(HistoryDay(date=day.date, index_value=index_val, detail=detail_items))

    return HistoryResponse(days=history, total_days=len(history))


@router.get("/me", response_model=MeResponse)
async def get_me(
    app_id: str = Query(default="adhd_tracker"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TrackingDay).where(TrackingDay.user_id == current_user.id, TrackingDay.app_id == app_id)
    result = await db.execute(stmt)
    total = len(result.scalars().all())

    return MeResponse(
        email=current_user.email,
        created_at=current_user.created_at,
        total_days=total,
    )


@router.get("/debug", response_model=DebugResponse)
async def get_debug(
    days: int = Query(default=60, ge=1, le=365),
    app_id: str = Query(default="adhd_tracker"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Raw per-day diagnostics — for verifying why a user's computed index/trend is or
    isn't showing up, without needing direct DB access."""
    stmt = (
        select(TrackingDay)
        .where(TrackingDay.user_id == current_user.id, TrackingDay.app_id == app_id)
        .options(selectinload(TrackingDay.daily_index), selectinload(TrackingDay.values))
        .order_by(TrackingDay.date.desc())
        .limit(days)
    )
    result = await db.execute(stmt)
    tracking_days = result.scalars().all()

    day_items: list[DayDebugItem] = []
    days_with_index = 0
    for day in tracking_days:
        has_index = day.daily_index is not None
        if has_index:
            days_with_index += 1
        day_items.append(DayDebugItem(
            date=day.date,
            element_count=len(day.values),
            is_complete=day.is_complete,
            day_updated_at=day.updated_at,
            device_id=day.device_id,
            has_daily_index=has_index,
            index_value=day.daily_index.index_value if has_index else None,
            index_computed_at=day.daily_index.computed_at if has_index else None,
        ))

    return DebugResponse(
        app_id=app_id,
        email=current_user.email,
        total_days=len(tracking_days),
        days_with_index=days_with_index,
        days=day_items,
    )
