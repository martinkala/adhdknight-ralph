"""Weight and blood pressure measurements of a day (constitution D4, food-005 FR-2): add, update,
soft delete. Validation errors are FoodDayError codes (bp_format, bp_range, weight_range, time_format)."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodWeight
from app.models.user import User
from app.services.food_days import FoodDayError, today_str
from app.services.food_measurements import (
    MeasurementError,
    normalize_time,
    parse_blood_pressure,
    validate_blood_pressure,
    validate_weight,
)
from app.services.food_text import clean_text
from app.services.food_time import local_time_for


class MeasurementNotFound(FoodDayError):
    def __init__(self):
        super().__init__("measurement_not_found")


def _time(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    try:
        return normalize_time(raw)
    except MeasurementError as exc:
        raise FoodDayError(exc.code) from None


def _note(raw: str | None) -> str | None:
    return clean_text(raw) or None if raw is not None else None


def _fill_time(user: User, day: FoodDay, measured_at: str | None, fill: bool, now: datetime | None) -> str | None:
    """Without a time on today's day, the current local time of the user is used."""
    if measured_at is None and fill and day.date == today_str(user, now):
        return local_time_for(user, now)
    return measured_at


async def _check_new_id(db: AsyncSession, model, record_id: str | None) -> None:
    if record_id is not None and await db.get(model, record_id) is not None:
        raise FoodDayError("id_exists")


async def _save(db: AsyncSession, record):
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def _weight(kg) -> Decimal:
    try:
        return validate_weight(kg)
    except MeasurementError as exc:
        raise FoodDayError(exc.code) from None


async def add_weight(db: AsyncSession, user: User, day: FoodDay, data: dict, now: datetime | None = None) -> FoodWeight:
    await _check_new_id(db, FoodWeight, data.get("id"))
    weight = FoodWeight(
        day_id=day.id,
        user_id=day.user_id,
        kg=_weight(data["kg"]),
        measured_at=_fill_time(user, day, _time(data.get("measured_at")), data.get("fill_time", False), now),
        note=_note(data.get("note")),
    )
    if data.get("id"):
        weight.id = data["id"]
    return await _save(db, weight)


async def update_weight(db: AsyncSession, weight: FoodWeight, changes: dict) -> FoodWeight:
    if "kg" in changes:
        if changes["kg"] is None:
            raise FoodDayError("weight_range")
        weight.kg = _weight(changes["kg"])
    if "measured_at" in changes:
        weight.measured_at = _time(changes["measured_at"])
    if "note" in changes:
        weight.note = _note(changes["note"])
    return await _save(db, weight)


def _pressure_values(data: dict) -> dict:
    """{systolic, diastolic, pulse, measured_at} from `raw` or from the separate fields."""
    if data.get("raw") is not None:
        try:
            values = parse_blood_pressure(data["raw"])
        except MeasurementError as exc:
            raise FoodDayError(exc.code) from None
        # An explicit time wins over a missing time in the quick entry.
        if values["measured_at"] is None and data.get("measured_at"):
            values["measured_at"] = _time(data["measured_at"])
        return values
    if data.get("systolic") is None or data.get("diastolic") is None:
        raise FoodDayError("bp_format")
    return {
        "systolic": data["systolic"],
        "diastolic": data["diastolic"],
        "pulse": data.get("pulse"),
        "measured_at": _time(data.get("measured_at")),
    }


def _validate_pressure(systolic: int, diastolic: int, pulse: int | None) -> None:
    try:
        validate_blood_pressure(systolic, diastolic, pulse)
    except MeasurementError as exc:
        raise FoodDayError(exc.code) from None


async def add_blood_pressure(
    db: AsyncSession, user: User, day: FoodDay, data: dict, now: datetime | None = None
) -> FoodBloodPressure:
    values = _pressure_values(data)
    _validate_pressure(values["systolic"], values["diastolic"], values["pulse"])
    await _check_new_id(db, FoodBloodPressure, data.get("id"))
    values["measured_at"] = _fill_time(user, day, values["measured_at"], data.get("fill_time", False), now)
    pressure = FoodBloodPressure(day_id=day.id, user_id=day.user_id, note=_note(data.get("note")), **values)
    if data.get("id"):
        pressure.id = data["id"]
    return await _save(db, pressure)


async def update_blood_pressure(db: AsyncSession, pressure: FoodBloodPressure, changes: dict) -> FoodBloodPressure:
    if changes.get("raw") is not None:
        changes = {**changes, **_pressure_values(changes)}
        changes.pop("raw")
    for field in ("systolic", "diastolic"):
        if field in changes and changes[field] is None:
            raise FoodDayError("bp_format")
    systolic = changes.get("systolic", pressure.systolic)
    diastolic = changes.get("diastolic", pressure.diastolic)
    pulse = changes.get("pulse", pressure.pulse)
    _validate_pressure(systolic, diastolic, pulse)
    pressure.systolic, pressure.diastolic, pressure.pulse = systolic, diastolic, pulse
    if "measured_at" in changes:
        pressure.measured_at = _time(changes["measured_at"])
    if "note" in changes:
        pressure.note = _note(changes["note"])
    return await _save(db, pressure)


async def get_measurement(db: AsyncSession, user: User, model, record_id: str):
    """The user's not deleted weight / blood pressure; another user's record is "not found" (A1)."""
    result = await db.execute(
        select(model).where(model.id == record_id, model.user_id == user.id, model.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise MeasurementNotFound()
    return record


async def delete_measurement(db: AsyncSession, record) -> None:
    now = datetime.now(timezone.utc)
    record.deleted_at = now
    record.updated_at = now
    await db.commit()
