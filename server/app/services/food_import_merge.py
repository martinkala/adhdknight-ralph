"""Merge of parsed import data with the user's diary (food-011 FR-2) and the commit in one transaction.

Lists are joined without duplicates (same category + text_norm + quantity + unit), measurements without
duplicates (same values + time), an empty day value is filled and a different one is a conflict.
Everything is compared only with the not deleted data of the given user (constitution A1)."""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodWeight
from app.models.user import User
from app.services import food_med_dictionary as med_dictionary
from app.services.food_constants import ALL_CATEGORIES, MEDS_CATEGORIES
from app.services.food_days import DAY_VALUE_FIELDS, FoodDayError, next_position
from app.services.food_import_parser import ImportItem, ParsedDay, ParsedImport
from app.services.food_text import normalize

RESOLUTION_CHOICES = ("keep", "import")
_QUANTITY_PRECISION = Decimal("0.001")
_KG_PRECISION = Decimal("0.1")


class ImportUnresolved(FoodDayError):
    """A conflict without a decision or an unclassified medication / supplement; nothing was stored."""

    def __init__(self):
        super().__init__("unresolved")


@dataclass
class DayPlan:
    date: str
    status: str  # new | merge
    day: FoodDay | None  # the existing row (a soft-deleted one is restored), None = create
    entries: dict[str, list[ImportItem]] = field(default_factory=dict)
    unclassified: list[ImportItem] = field(default_factory=list)
    weights: list[dict] = field(default_factory=list)
    blood_pressures: list[dict] = field(default_factory=list)
    values: dict[str, int] = field(default_factory=dict)  # filled (empty before) day values
    conflicts: list[dict] = field(default_factory=list)  # {date, field, existing, incoming}
    duplicates_skipped: int = 0


@dataclass
class ImportPlan:
    parsed: ParsedImport
    days: list[DayPlan]
    needs_classification: list[dict]  # {text, text_norm}

    @property
    def conflicts(self) -> list[dict]:
        return [c for day in self.days for c in day.conflicts]

    def totals(self) -> dict[str, int]:
        return {
            "new_days": sum(d.status == "new" for d in self.days),
            "merged_days": sum(d.status == "merge" for d in self.days),
            "entries_added": sum(len(items) for d in self.days for items in d.entries.values())
            + sum(len(d.unclassified) for d in self.days),
            "measurements_added": sum(len(d.weights) + len(d.blood_pressures) for d in self.days),
            "values_filled": sum(len(d.values) for d in self.days),
            "duplicates_skipped": sum(d.duplicates_skipped for d in self.days),
            "conflicts": len(self.conflicts),
            "issues": len(self.parsed.issues),
            "skipped_empty_days": len(self.parsed.skipped_empty_days),
        }


def _q(value, precision: Decimal) -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(precision)


def _entry_key(category: str, text_norm: str, quantity, unit: str | None) -> tuple:
    return category, text_norm, _q(quantity, _QUANTITY_PRECISION), unit or None


def _weight_key(kg, measured_at: str | None) -> tuple:
    return _q(kg, _KG_PRECISION), measured_at


def _bp_key(systolic: int, diastolic: int, pulse: int | None, measured_at: str | None) -> tuple:
    return systolic, diastolic, pulse, measured_at


async def _alive(db: AsyncSession, model, day_ids: list[str]) -> list:
    if not day_ids:
        return []
    result = await db.execute(select(model).where(model.day_id.in_(day_ids), model.deleted_at.is_(None)))
    return list(result.scalars().all())


async def plan_import(
    db: AsyncSession, user: User, parsed: ParsedImport, classify: dict[str, str] | None = None,
) -> ImportPlan:
    """What the import would add, skip and where it conflicts. Reads only, stores nothing.
    `classify` (text_norm -> medication | supplement) answers medication items unknown to the dictionary."""
    dates = [d.date for d in parsed.days]
    existing_days: dict[str, FoodDay] = {}
    if dates:
        result = await db.execute(select(FoodDay).where(FoodDay.user_id == user.id, FoodDay.date.in_(dates)))
        existing_days = {d.date: d for d in result.scalars().all()}
    alive_ids = [d.id for d in existing_days.values() if d.deleted_at is None]
    entries = Counter()
    weights = Counter()
    pressures = Counter()
    for e in await _alive(db, FoodEntry, alive_ids):
        entries[(e.day_id, *_entry_key(e.category, e.text_norm, e.quantity, e.unit))] += 1
    for w in await _alive(db, FoodWeight, alive_ids):
        weights[(w.day_id, *_weight_key(w.kg, w.measured_at))] += 1
    for bp in await _alive(db, FoodBloodPressure, alive_ids):
        pressures[(bp.day_id, *_bp_key(bp.systolic, bp.diastolic, bp.pulse, bp.measured_at))] += 1

    answers = {normalize(key): med_dictionary.check_kind(kind) for key, kind in (classify or {}).items()}
    med_norms = {normalize(item.text) for d in parsed.days for item in d.meds}
    known = await med_dictionary.kinds(db, user.id, med_norms)

    plans = []
    needs: dict[str, dict] = {}
    for source in parsed.days:
        day = existing_days.get(source.date)
        alive = day is not None and day.deleted_at is None
        plan = DayPlan(source.date, "merge" if alive else "new", day)
        day_id = day.id if alive else None

        def unique(counter: Counter, key: tuple) -> bool:
            """False (a duplicate) if an existing row with the key is still unmatched."""
            if day_id is not None and counter[(day_id, *key)] > 0:
                counter[(day_id, *key)] -= 1
                plan.duplicates_skipped += 1
                return False
            return True

        items_by_category = {category: list(items) for category, items in source.entries.items()}
        for item in source.meds:
            norm = normalize(item.text)
            kind = known.get(norm) or answers.get(norm)
            if kind is None:
                plan.unclassified.append(item)
                needs.setdefault(norm, {"text": item.text, "text_norm": norm})
            else:
                items_by_category.setdefault(kind, []).append(item)
        for category in ALL_CATEGORIES:
            added = [item for item in items_by_category.get(category, [])
                     if unique(entries, _entry_key(category, normalize(item.text), item.quantity, item.unit))]
            if added:
                plan.entries[category] = added
        plan.weights = [w for w in source.weights if unique(weights, _weight_key(w["kg"], w["measured_at"]))]
        plan.blood_pressures = [
            bp for bp in source.blood_pressures
            if unique(pressures, _bp_key(bp["systolic"], bp["diastolic"], bp["pulse"], bp["measured_at"]))
        ]
        for name in DAY_VALUE_FIELDS:
            incoming = source.values.get(name)
            if incoming is None:
                continue
            current = getattr(day, name) if alive else None
            if current is None:
                plan.values[name] = incoming
            elif current != incoming:
                plan.conflicts.append({"date": source.date, "field": name, "existing": current, "incoming": incoming})
        plans.append(plan)
    return ImportPlan(parsed, plans, list(needs.values()))


def _resolved_values(plan: ImportPlan, resolutions: list[dict], default: str | None) -> dict[str, dict[str, int]]:
    """date -> day values to write. Raises ImportUnresolved for a conflict without a decision."""
    choices = {(r["date"], r["field"]): r["choice"] for r in resolutions}
    values: dict[str, dict[str, int]] = {}
    for day in plan.days:
        values[day.date] = dict(day.values)
        for conflict in day.conflicts:
            choice = choices.get((conflict["date"], conflict["field"])) or default
            if choice not in RESOLUTION_CHOICES:
                raise ImportUnresolved()
            if choice == "import":
                values[day.date][conflict["field"]] = conflict["incoming"]
    return values


async def commit_import(
    db: AsyncSession, user: User, plan: ImportPlan, resolutions: list[dict] | None = None,
    default_resolution: str | None = None,
) -> None:
    """Stores the plan in one transaction: any error rolls everything back and is raised again.
    Raises ImportUnresolved (nothing stored) while a conflict or a medication item is undecided."""
    if plan.needs_classification:
        raise ImportUnresolved()
    values = _resolved_values(plan, resolutions or [], default_resolution)
    try:
        await _apply(db, user, plan, values)
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def _apply(db: AsyncSession, user: User, plan: ImportPlan, values: dict[str, dict[str, int]]) -> None:
    # Measurements are ordered by created_at after their time, so the input order is kept explicitly.
    created = datetime.now(timezone.utc)

    def stamp():
        nonlocal created
        created += timedelta(microseconds=1)
        return {"created_at": created, "updated_at": created}

    for day_plan in plan.days:
        day = day_plan.day
        if day is None:
            day = FoodDay(user_id=user.id, date=day_plan.date)
            db.add(day)
            await db.flush()
        elif day.deleted_at is not None:
            # Restored empty like create_day; its old entries and measurements stay deleted.
            day.deleted_at = None
            for name in DAY_VALUE_FIELDS:
                setattr(day, name, None)
        for name, value in values[day_plan.date].items():
            setattr(day, name, value)

        for category, items in day_plan.entries.items():
            position = await next_position(db, day.id, category)
            for offset, item in enumerate(items):
                db.add(FoodEntry(
                    day_id=day.id, user_id=user.id, category=category, text=item.text,
                    text_norm=normalize(item.text), quantity=item.quantity,
                    unit=item.unit if item.quantity is not None else None, intensity=item.intensity,
                    position=position + offset, **stamp(),
                ))
                if category in MEDS_CATEGORIES:
                    await med_dictionary.stage(db, user.id, item.text, category)
        for weight in day_plan.weights:
            db.add(FoodWeight(day_id=day.id, user_id=user.id, **weight, **stamp()))
        for bp in day_plan.blood_pressures:
            db.add(FoodBloodPressure(day_id=day.id, user_id=user.id, **bp, **stamp()))
        await db.flush()
