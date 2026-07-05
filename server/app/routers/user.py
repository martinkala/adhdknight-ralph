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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TrackingDay)
        .where(TrackingDay.user_id == current_user.id)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TrackingDay).where(TrackingDay.user_id == current_user.id)
    result = await db.execute(stmt)
    total = len(result.scalars().all())

    return MeResponse(
        email=current_user.email,
        created_at=current_user.created_at,
        total_days=total,
    )
