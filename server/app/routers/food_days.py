from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user, get_now
from app.models.user import User
from app.schemas.food import (
    DATE_PATTERN,
    MONTH_PATTERN,
    CalendarMonth,
    DayCreate,
    DayDetail,
    DayList,
    DayUpdate,
    TodayResponse,
)
from app.services import food_days, food_overview
from app.services.food_days import DayNotFound, FoodDayError

router = APIRouter(prefix="/api/v1/food", tags=["food"])

_ERROR_STATUS = {"future_date": 422, "day_exists": 409, "id_exists": 409}
_NOT_FOUND = {404: {"description": "Day does not exist or was deleted"}}

DatePath = Annotated[str, Path(pattern=DATE_PATTERN, examples=["2026-10-24"])]


async def _day_or_404(db: AsyncSession, user: User, date: str):
    try:
        return await food_days.get_day(db, user, date)
    except DayNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="day_not_found")


@router.get("/today", response_model=TodayResponse)
async def get_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """Today in the user's timezone and whether that day already exists."""
    today = food_days.today_str(current_user, now)
    return TodayResponse(date=today, exists=await food_days.day_exists(db, current_user, today))


@router.get("/calendar", response_model=CalendarMonth)
async def get_calendar(
    month: Annotated[str | None, Query(pattern=MONTH_PATTERN, examples=["2026-10"])] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """Existing days of the month (default the current month) with digestion values and entry counts."""
    return await food_overview.calendar(db, current_user, month, now)


@router.get("/days", response_model=DayList)
async def list_days(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Days from the newest with a short summary (values, measurements, first food texts)."""
    return await food_overview.day_list(db, current_user, page, page_size)


@router.post(
    "/days",
    response_model=DayDetail,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "`day_exists` or `id_exists`"}, 422: {"description": "`future_date`"}},
)
async def create_day(
    body: DayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """Creates an empty day (default today). A deleted day is restored empty."""
    try:
        day = await food_days.create_day(db, current_user, body.date, body.id, now)
    except FoodDayError as exc:
        raise HTTPException(status_code=_ERROR_STATUS[exc.code], detail=exc.code)
    return await food_days.day_detail(db, day)


@router.get("/days/{date}", response_model=DayDetail, responses=_NOT_FOUND)
async def get_day(
    date: DatePath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    day = await _day_or_404(db, current_user, date)
    return await food_days.day_detail(db, day)


@router.patch("/days/{date}", response_model=DayDetail, responses=_NOT_FOUND)
async def patch_day(
    date: DatePath,
    body: DayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sets day values (sleep_quality 1–3, stool and gas 1–10). Only sent fields change; null clears."""
    day = await _day_or_404(db, current_user, date)
    day = await food_days.update_day_values(db, day, body.model_dump(include=body.model_fields_set))
    return await food_days.day_detail(db, day)


@router.delete("/days/{date}", status_code=status.HTTP_204_NO_CONTENT, responses=_NOT_FOUND)
async def delete_day(
    date: DatePath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes the day with all its entries and measurements."""
    day = await _day_or_404(db, current_user, date)
    await food_days.delete_day(db, day)
