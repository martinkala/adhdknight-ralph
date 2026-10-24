"""Export of the user's food diary (food-009): JSON (`FoodExport`) and long-format CSV.
Only not deleted data of the given user (constitution A1, D9). Generated in memory, the data is small."""
import csv
import io
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodWeight
from app.models.user import User
from app.schemas.food import ExportBloodPressure, ExportDay, ExportEntry, ExportWeight, FoodExport
from app.services.food_constants import ALL_CATEGORIES
from app.services.food_days import DAY_VALUE_FIELDS
from app.services.food_overview import _children_by_day, _measurement_order

CSV_COLUMNS = (
    "date", "record_type", "category", "text", "quantity", "unit", "intensity", "value",
    "systolic", "diastolic", "pulse", "measured_at", "note",
)


def _float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


async def _days(db: AsyncSession, user: User, date_from: str | None, date_to: str | None) -> list[FoodDay]:
    stmt = select(FoodDay).where(FoodDay.user_id == user.id, FoodDay.deleted_at.is_(None))
    if date_from:
        stmt = stmt.where(FoodDay.date >= date_from)
    if date_to:
        stmt = stmt.where(FoodDay.date <= date_to)
    return list((await db.execute(stmt.order_by(FoodDay.date))).scalars().all())


async def build_export(
    db: AsyncSession, user: User, date_from: str | None = None, date_to: str | None = None,
    now: datetime | None = None,
) -> FoodExport:
    """Days in the range (both ends optional, inclusive) ascending, every category present."""
    days = await _days(db, user, date_from, date_to)
    day_ids = [d.id for d in days]
    entries = await _children_by_day(db, FoodEntry, day_ids, FoodEntry.position, FoodEntry.created_at)
    weights = await _children_by_day(db, FoodWeight, day_ids, *_measurement_order(FoodWeight))
    pressures = await _children_by_day(db, FoodBloodPressure, day_ids, *_measurement_order(FoodBloodPressure))

    export_days = []
    for day in days:
        by_category: dict[str, list[ExportEntry]] = {category: [] for category in ALL_CATEGORIES}
        for e in entries.get(day.id, []):
            by_category.setdefault(e.category, []).append(
                ExportEntry(text=e.text, quantity=_float(e.quantity), unit=e.unit, intensity=e.intensity)
            )
        export_days.append(ExportDay(
            date=day.date,
            sleep_quality=day.sleep_quality,
            stool=day.stool,
            gas=day.gas,
            entries=by_category,
            weights=[ExportWeight(kg=float(w.kg), measured_at=w.measured_at, note=w.note)
                     for w in weights.get(day.id, [])],
            blood_pressures=[
                ExportBloodPressure(systolic=bp.systolic, diastolic=bp.diastolic, pulse=bp.pulse,
                                    measured_at=bp.measured_at, note=bp.note)
                for bp in pressures.get(day.id, [])
            ],
        ))
    return FoodExport(exported_at=now or datetime.now(timezone.utc), days=export_days)


def _cell(value) -> str:
    """CSV cell: empty for missing values, numbers with a decimal point and without a trailing .0."""
    if value is None:
        return ""
    if isinstance(value, float):
        return format(Decimal(repr(value)).normalize(), "f")
    return str(value)


def export_rows(export: FoodExport) -> list[dict[str, str]]:
    """Long format: one row per entry, measurement and filled day value."""
    rows = []

    def add(**cells):
        rows.append({column: _cell(cells.get(column)) for column in CSV_COLUMNS})

    for day in export.days:
        for field in DAY_VALUE_FIELDS:
            value = getattr(day, field)
            if value is not None:
                add(date=day.date, record_type="day_value", category=field, value=value)
        for category, entries in day.entries.items():
            for e in entries:
                add(date=day.date, record_type="entry", category=category, text=e.text,
                    quantity=e.quantity, unit=e.unit, intensity=e.intensity)
        for w in day.weights:
            add(date=day.date, record_type="weight", value=w.kg, measured_at=w.measured_at, note=w.note)
        for bp in day.blood_pressures:
            add(date=day.date, record_type="blood_pressure", systolic=bp.systolic, diastolic=bp.diastolic,
                pulse=bp.pulse, measured_at=bp.measured_at, note=bp.note)
    return rows


def to_csv(export: FoodExport) -> str:
    """UTF-8 CSV text with a BOM (Excel reads the diacritics), RFC 4180 quoting, CRLF line ends."""
    buffer = io.StringIO()
    buffer.write("﻿")
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(export_rows(export))
    return buffer.getvalue()


def filename(export: FoodExport, date_from: str | None, date_to: str | None, today: str, extension: str) -> str:
    """food-diary-<from>-<to>.<ext>; a missing end is the first / last exported day (or today)."""
    first = date_from or (export.days[0].date if export.days else today)
    last = date_to or (export.days[-1].date if export.days else today)
    return f"food-diary-{first}-{last}.{extension}"
