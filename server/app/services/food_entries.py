"""Food diary entries (constitution D2, D5–D7, food-005 FR-1): add with splitting, quantity parsing
and merging, update, soft delete and the most used quantities. Every query is scoped to the user (A1)."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodDay, FoodEntry
from app.models.user import User
from app.services.food_constants import ALL_CATEGORIES, CATEGORY_GROUP, SPORT_CATEGORIES, TEXT_MAX_LENGTH, UNITS
from app.services.food_days import FoodDayError
from app.services.food_quantity import ParsedItem, merge_duplicates, parse_item
from app.services.food_text import clean_text, normalize, split_entries

QUANTITY_OPTIONS_LIMIT = 5
_PRECISION = Decimal("0.001")  # food_entries.quantity is Numeric(10, 3)


class EntryNotFound(FoodDayError):
    def __init__(self):
        super().__init__("entry_not_found")


def _check_category(category: str) -> None:
    if category not in ALL_CATEGORIES:
        raise FoodDayError("unknown_category")


def _check_intensity(category: str, intensity: int | None) -> None:
    if intensity is not None and category not in SPORT_CATEGORIES:
        raise FoodDayError("intensity_not_allowed")


def _quantity(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(_PRECISION)


def _unit(unit: str | None) -> str | None:
    """Validates the unit; pieces ("ks" or nothing) are stored as None."""
    if unit is None or unit == "":
        return None
    unit = unit.strip().lower()
    if unit not in UNITS:
        raise FoodDayError("invalid_unit")
    return None if unit == "ks" else unit


def _clean_note(text: str) -> str:
    """Notes keep their line breaks; each line is trimmed and empty lines are dropped."""
    return "\n".join(line for line in (clean_text(part) for part in text.splitlines()) if line)


def _check_text(text: str) -> str:
    if not text:
        raise FoodDayError("empty_text")
    if len(text) > TEXT_MAX_LENGTH:
        raise FoodDayError("text_too_long")
    return text


def parse_input(category: str, text: str, quantity: float | None = None, unit: str | None = None) -> list[ParsedItem]:
    """One input -> items to store. Notes are one item; other categories are split on commas and
    new lines, the quantity is parsed from each part unless given explicitly, then duplicates merge."""
    if category in CATEGORY_GROUP and CATEGORY_GROUP[category] is None:
        return [ParsedItem(_check_text(_clean_note(text)), _quantity(quantity), _unit(unit) if quantity else None)]
    if quantity is None and unit:
        raise FoodDayError("unit_without_quantity")
    parts = split_entries(text)
    if not parts:
        raise FoodDayError("empty_text")
    if quantity is None:
        items = [parse_item(part) for part in parts]
    else:
        items = [ParsedItem(part, _quantity(quantity), _unit(unit)) for part in parts]
    items = merge_duplicates(items)
    for item in items:
        _check_text(item.text)
    return items


async def _next_position(db: AsyncSession, day_id: str, category: str) -> int:
    result = await db.execute(
        select(func.max(FoodEntry.position)).where(
            FoodEntry.day_id == day_id, FoodEntry.category == category, FoodEntry.deleted_at.is_(None)
        )
    )
    current = result.scalar_one_or_none()
    return 0 if current is None else current + 1


async def add_entries(
    db: AsyncSession,
    day: FoodDay,
    category: str,
    text: str,
    quantity: float | None = None,
    unit: str | None = None,
    intensity: int | None = None,
    entry_id: str | None = None,
) -> list[FoodEntry]:
    """Adds the entries of one input at the end of the category section of the day."""
    _check_category(category)
    _check_intensity(category, intensity)
    items = parse_input(category, text, quantity, unit)
    if entry_id is not None:
        if len(items) != 1:
            raise FoodDayError("id_requires_single_entry")
        if await db.get(FoodEntry, entry_id) is not None:
            raise FoodDayError("id_exists")

    position = await _next_position(db, day.id, category)
    entries = []
    for offset, item in enumerate(items):
        entry = FoodEntry(
            day_id=day.id,
            user_id=day.user_id,
            category=category,
            text=item.text,
            text_norm=normalize(item.text),
            quantity=item.quantity,
            unit=item.unit if item.quantity is not None else None,
            intensity=intensity,
            position=position + offset,
        )
        if entry_id is not None:
            entry.id = entry_id
        db.add(entry)
        entries.append(entry)
    await db.commit()
    for entry in entries:
        await db.refresh(entry)
    return entries


async def get_entry(db: AsyncSession, user: User, entry_id: str) -> FoodEntry:
    """The user's not deleted entry; another user's entry is "not found" too (constitution A1)."""
    result = await db.execute(
        select(FoodEntry).where(
            FoodEntry.id == entry_id, FoodEntry.user_id == user.id, FoodEntry.deleted_at.is_(None)
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise EntryNotFound()
    return entry


async def update_entry(db: AsyncSession, entry: FoodEntry, changes: dict) -> FoodEntry:
    """Applies the sent fields. A new text is only cleaned (no splitting, no quantity parsing)."""
    if "category" in changes:
        category = changes["category"]
        if category is None:
            raise FoodDayError("unknown_category")
        _check_category(category)
        if category != entry.category:
            entry.position = await _next_position(db, entry.day_id, category)
            entry.category = category
            if category not in SPORT_CATEGORIES:
                entry.intensity = None
    if "text" in changes:
        raw = changes["text"] or ""
        is_note = CATEGORY_GROUP.get(entry.category, "") is None
        entry.text = _check_text(_clean_note(raw) if is_note else clean_text(raw))
        entry.text_norm = normalize(entry.text)
    if "quantity" in changes:
        entry.quantity = _quantity(changes["quantity"])
        entry.unit = _unit(changes.get("unit")) if entry.quantity is not None else None
    elif "unit" in changes:
        if entry.quantity is None and changes["unit"]:
            raise FoodDayError("unit_without_quantity")
        entry.unit = _unit(changes["unit"])
    if "intensity" in changes:
        _check_intensity(entry.category, changes["intensity"])
        entry.intensity = changes["intensity"]
    if changes.get("position") is not None:
        entry.position = changes["position"]
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_entry(db: AsyncSession, entry: FoodEntry) -> None:
    now = datetime.now(timezone.utc)
    entry.deleted_at = now
    entry.updated_at = now
    await db.commit()


async def quantity_options(db: AsyncSession, user: User, text: str, category: str) -> list[dict]:
    """The most used quantity + unit combinations of the text in the category's group (D5)."""
    _check_category(category)
    group = CATEGORY_GROUP[category]
    text_norm = normalize(text)
    if group is None or not text_norm:
        return []
    categories = [c for c, g in CATEGORY_GROUP.items() if g == group]
    count = func.count(FoodEntry.id)
    result = await db.execute(
        select(FoodEntry.quantity, FoodEntry.unit, count)
        .where(
            FoodEntry.user_id == user.id,
            FoodEntry.deleted_at.is_(None),
            FoodEntry.category.in_(categories),
            FoodEntry.text_norm == text_norm,
            FoodEntry.quantity.is_not(None),
        )
        .group_by(FoodEntry.quantity, FoodEntry.unit)
        .order_by(count.desc(), func.max(FoodEntry.updated_at).desc())
        .limit(QUANTITY_OPTIONS_LIMIT)
    )
    return [{"quantity": float(q), "unit": unit, "count": n} for q, unit, n in result.all()]
