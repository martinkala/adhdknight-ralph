"""Overview of the user's days (food-008): month calendar and the paginated days list.
Every query is scoped to the given user (constitution A1)."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodWeight
from app.models.user import User
from app.schemas.food import CalendarDay, CalendarMonth, DayList, DaySummary
from app.services.food_constants import FOOD_CATEGORIES
from app.services.food_time import today_for

FOOD_PREVIEW_MAX = 8


def severity(stool: int | None, gas: int | None) -> str:
    """Digestion severity of a day from the worse of stool / gas."""
    values = [v for v in (stool, gas) if v is not None]
    if not values:
        return "none"
    worst = max(values)
    return "ok" if worst <= 3 else "mid" if worst <= 6 else "bad"


def _alive_days(user: User):
    return select(FoodDay).where(FoodDay.user_id == user.id, FoodDay.deleted_at.is_(None))


async def _entry_counts(db: AsyncSession, day_ids: list[str]) -> dict[str, int]:
    if not day_ids:
        return {}
    result = await db.execute(
        select(FoodEntry.day_id, func.count())
        .where(FoodEntry.day_id.in_(day_ids), FoodEntry.deleted_at.is_(None))
        .group_by(FoodEntry.day_id)
    )
    return dict(result.all())


async def calendar(db: AsyncSession, user: User, month: str | None, now: datetime | None = None) -> CalendarMonth:
    """Existing days of the month (YYYY-MM, default the user's current month)."""
    today = today_for(user, now).isoformat()
    month = month or today[:7]
    # Dates are YYYY-MM-DD strings, so a string range selects the month.
    result = await db.execute(
        _alive_days(user)
        .where(FoodDay.date >= f"{month}-01", FoodDay.date <= f"{month}-31")
        .order_by(FoodDay.date)
    )
    days = list(result.scalars().all())
    counts = await _entry_counts(db, [d.id for d in days])
    return CalendarMonth(
        month=month,
        today=today,
        days=[
            CalendarDay(date=d.date, stool=d.stool, gas=d.gas, severity=severity(d.stool, d.gas),
                        entry_count=counts.get(d.id, 0))
            for d in days
        ],
    )


async def _children_by_day(db: AsyncSession, model, day_ids: list[str], *order_by) -> dict[str, list]:
    result = await db.execute(
        select(model).where(model.day_id.in_(day_ids), model.deleted_at.is_(None)).order_by(*order_by)
    )
    by_day: dict[str, list] = {}
    for row in result.scalars().all():
        by_day.setdefault(row.day_id, []).append(row)
    return by_day


def _measurement_order(model):
    return (model.measured_at.is_(None), model.measured_at, model.created_at)


def _bp_text(bp: FoodBloodPressure) -> str:
    text = f"{bp.systolic}/{bp.diastolic}"
    return f"{text} {bp.pulse}" if bp.pulse is not None else text


async def day_list(db: AsyncSession, user: User, page: int, page_size: int) -> DayList:
    """The user's days from the newest, one page with a short summary of each day."""
    total = (await db.execute(
        select(func.count()).select_from(FoodDay).where(FoodDay.user_id == user.id, FoodDay.deleted_at.is_(None))
    )).scalar_one()
    result = await db.execute(
        _alive_days(user).order_by(FoodDay.date.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    days = list(result.scalars().all())
    day_ids = [d.id for d in days]

    summaries = []
    if day_ids:
        counts = await _entry_counts(db, day_ids)
        foods = await _children_by_day(
            db, FoodEntry, day_ids, FoodEntry.position, FoodEntry.created_at
        )
        weights = await _children_by_day(db, FoodWeight, day_ids, *_measurement_order(FoodWeight))
        pressures = await _children_by_day(db, FoodBloodPressure, day_ids, *_measurement_order(FoodBloodPressure))
        section = {category: index for index, category in enumerate(FOOD_CATEGORIES)}
        for d in days:
            food = sorted(
                (e for e in foods.get(d.id, []) if e.category in section),
                key=lambda e: section[e.category],  # stable: keeps the position order inside a section
            )
            summaries.append(DaySummary(
                date=d.date,
                stool=d.stool,
                gas=d.gas,
                severity=severity(d.stool, d.gas),
                sleep_quality=d.sleep_quality,
                weights=[float(w.kg) for w in weights.get(d.id, [])],
                bp=[_bp_text(bp) for bp in pressures.get(d.id, [])],
                food_preview=[e.text for e in food[:FOOD_PREVIEW_MAX]],
                entry_count=counts.get(d.id, 0),
            ))
    return DayList(page=page, page_size=page_size, total=total, days=summaries)
