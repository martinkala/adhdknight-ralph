"""Food diary days (constitution D1, D3, B2): create / restore, read, day values, soft delete.
Every query is scoped to the given user (constitution A1)."""
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodWeight
from app.models.user import User
from app.schemas.food import BloodPressure, DayDetail, Entry, Weight
from app.services.food_constants import ALL_CATEGORIES
from app.services.food_time import is_future, today_for

DAY_VALUE_FIELDS = ("sleep_quality", "stool", "gas")


class FoodDayError(Exception):
    """Domain error with an API error code (`detail`)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class DayNotFound(FoodDayError):
    def __init__(self):
        super().__init__("day_not_found")


async def next_position(db: AsyncSession, day_id: str, category: str) -> int:
    """Position after the last not deleted entry of the category section of the day."""
    result = await db.execute(
        select(func.max(FoodEntry.position)).where(
            FoodEntry.day_id == day_id, FoodEntry.category == category, FoodEntry.deleted_at.is_(None)
        )
    )
    current = result.scalar_one_or_none()
    return 0 if current is None else current + 1


def today_str(user: User, now: datetime | None = None) -> str:
    return today_for(user, now).isoformat()


async def _find_day(db: AsyncSession, user: User, date: str) -> FoodDay | None:
    """The user's day row for the date, soft-deleted included."""
    result = await db.execute(select(FoodDay).where(FoodDay.user_id == user.id, FoodDay.date == date))
    return result.scalar_one_or_none()


async def get_day(db: AsyncSession, user: User, date: str) -> FoodDay:
    day = await _find_day(db, user, date)
    if day is None or day.deleted_at is not None:
        raise DayNotFound()
    return day


async def day_exists(db: AsyncSession, user: User, date: str) -> bool:
    day = await _find_day(db, user, date)
    return day is not None and day.deleted_at is None


async def create_day(
    db: AsyncSession, user: User, date: str | None, day_id: str | None = None, now: datetime | None = None
) -> FoodDay:
    """Creates an empty day (default today). A soft-deleted day is restored empty; its old
    entries and measurements stay deleted. Raises FoodDayError future_date / day_exists / id_exists."""
    date = date or today_str(user, now)
    if is_future(date, user, now):
        raise FoodDayError("future_date")
    day = await _find_day(db, user, date)
    if day is not None:
        if day.deleted_at is None:
            raise FoodDayError("day_exists")
        day.deleted_at = None
        for field in DAY_VALUE_FIELDS:
            setattr(day, field, None)
    else:
        if day_id is not None and await db.get(FoodDay, day_id) is not None:
            raise FoodDayError("id_exists")
        day = FoodDay(user_id=user.id, date=date)
        if day_id is not None:
            day.id = day_id
        db.add(day)
    await db.commit()
    await db.refresh(day)
    return day


async def update_day_values(db: AsyncSession, day: FoodDay, values: dict) -> FoodDay:
    """Sets the given day values (sleep_quality, stool, gas); None clears a value."""
    for field, value in values.items():
        if field in DAY_VALUE_FIELDS:
            setattr(day, field, value)
    await db.commit()
    await db.refresh(day)
    return day


async def delete_day(db: AsyncSession, day: FoodDay) -> None:
    """Soft-deletes the day together with all its entries and measurements."""
    now = datetime.now(timezone.utc)
    for model in (FoodEntry, FoodWeight, FoodBloodPressure):
        await db.execute(
            update(model)
            .where(model.day_id == day.id, model.deleted_at.is_(None))
            .values(deleted_at=now, updated_at=now)
        )
    day.deleted_at = now
    await db.commit()


async def _neighbour_date(db: AsyncSession, day: FoodDay, before: bool) -> str | None:
    column = FoodDay.date
    stmt = select(column).where(FoodDay.user_id == day.user_id, FoodDay.deleted_at.is_(None))
    stmt = stmt.where(column < day.date).order_by(column.desc()) if before else \
        stmt.where(column > day.date).order_by(column.asc())
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


def _measurement_order(model):
    # Measurements without a time go last, then by creation.
    return (model.measured_at.is_(None), model.measured_at, model.created_at)


async def _alive_children(db: AsyncSession, model, day: FoodDay, order_by) -> list:
    result = await db.execute(
        select(model).where(model.day_id == day.id, model.deleted_at.is_(None)).order_by(*order_by)
    )
    return list(result.scalars().all())


async def day_detail(db: AsyncSession, day: FoodDay) -> DayDetail:
    entries = await _alive_children(db, FoodEntry, day, (FoodEntry.position, FoodEntry.created_at))
    weights = await _alive_children(db, FoodWeight, day, _measurement_order(FoodWeight))
    pressures = await _alive_children(db, FoodBloodPressure, day, _measurement_order(FoodBloodPressure))

    by_category: dict[str, list[Entry]] = {category: [] for category in ALL_CATEGORIES}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(Entry.model_validate(entry, from_attributes=True))

    return DayDetail(
        id=day.id,
        date=day.date,
        sleep_quality=day.sleep_quality,
        stool=day.stool,
        gas=day.gas,
        updated_at=day.updated_at,
        entries=by_category,
        weights=[Weight.model_validate(w, from_attributes=True) for w in weights],
        blood_pressures=[BloodPressure.model_validate(bp, from_attributes=True) for bp in pressures],
        prev_date=await _neighbour_date(db, day, before=True),
        next_date=await _neighbour_date(db, day, before=False),
    )
