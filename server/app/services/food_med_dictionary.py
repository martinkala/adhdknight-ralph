"""Per-user "medication or supplement?" dictionary keyed by text_norm (constitution D7, food-007 FR-1).

Deleting an item is a soft delete; saving it again restores the row (unique user_id + text_norm).
Every query is scoped to the user (A1)."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodDay, FoodEntry, FoodMedDictionary
from app.models.user import User
from app.services.food_constants import MED_KINDS, MEDS_CATEGORIES, TEXT_MAX_LENGTH
from app.services.food_days import FoodDayError, next_position
from app.services.food_text import clean_text, normalize


class DictionaryItemNotFound(FoodDayError):
    def __init__(self):
        super().__init__("dictionary_item_not_found")


def check_kind(kind: str | None) -> str:
    if kind not in MED_KINDS:
        raise FoodDayError("invalid_kind")
    return kind


async def _row(db: AsyncSession, user_id: str, text_norm: str) -> FoodMedDictionary | None:
    """The user's row for text_norm, deleted rows included (they are restored on save)."""
    result = await db.execute(
        select(FoodMedDictionary).where(FoodMedDictionary.user_id == user_id, FoodMedDictionary.text_norm == text_norm)
    )
    return result.scalar_one_or_none()


async def kinds(db: AsyncSession, user_id: str, text_norms: set[str]) -> dict[str, str]:
    """text_norm -> kind of the not deleted dictionary items among text_norms."""
    if not text_norms:
        return {}
    result = await db.execute(
        select(FoodMedDictionary.text_norm, FoodMedDictionary.kind).where(
            FoodMedDictionary.user_id == user_id,
            FoodMedDictionary.deleted_at.is_(None),
            FoodMedDictionary.text_norm.in_(text_norms),
        )
    )
    return dict(result.all())


async def _usage_counts(db: AsyncSession, user: User) -> dict[str, int]:
    count = func.count(FoodEntry.id)
    result = await db.execute(
        select(FoodEntry.text_norm, count)
        .join(FoodDay, FoodDay.id == FoodEntry.day_id)
        .where(
            FoodEntry.user_id == user.id,
            FoodEntry.deleted_at.is_(None),
            FoodEntry.category.in_(MEDS_CATEGORIES),
            FoodDay.deleted_at.is_(None),
        )
        .group_by(FoodEntry.text_norm)
    )
    return dict(result.all())


async def list_items(db: AsyncSession, user: User) -> list[dict]:
    """Not deleted items alphabetically (by text_norm) with the number of their med entries."""
    result = await db.execute(
        select(FoodMedDictionary)
        .where(FoodMedDictionary.user_id == user.id, FoodMedDictionary.deleted_at.is_(None))
        .order_by(FoodMedDictionary.text_norm)
    )
    counts = await _usage_counts(db, user)
    return [
        {"text_norm": row.text_norm, "display_text": row.display_text, "kind": row.kind,
         "usage_count": counts.get(row.text_norm, 0)}
        for row in result.scalars().all()
    ]


def _key(text_norm: str) -> str:
    text_norm = normalize(text_norm)
    if not text_norm:
        raise FoodDayError("empty_text")
    if len(text_norm) > TEXT_MAX_LENGTH:
        raise FoodDayError("text_too_long")
    return text_norm


async def _move_entries(db: AsyncSession, user: User, text_norm: str, kind: str) -> None:
    """Moves the user's med entries of text_norm to the section of kind (at the end of each day's section)."""
    result = await db.execute(
        select(FoodEntry)
        .where(
            FoodEntry.user_id == user.id,
            FoodEntry.deleted_at.is_(None),
            FoodEntry.text_norm == text_norm,
            FoodEntry.category.in_(MEDS_CATEGORIES),
            FoodEntry.category != kind,
        )
        .order_by(FoodEntry.day_id, FoodEntry.position)
    )
    for entry in result.scalars().all():
        entry.position = await next_position(db, entry.day_id, kind)
        entry.category = kind
        await db.flush()


async def stage(db: AsyncSession, user_id: str, text: str, kind: str) -> FoodMedDictionary:
    """Adds (or restores) the dictionary item of text without committing. An existing item keeps its kind."""
    text_norm = _key(text)
    row = await _row(db, user_id, text_norm)
    if row is None:
        row = FoodMedDictionary(user_id=user_id, text_norm=text_norm, display_text=clean_text(text), kind=kind)
        db.add(row)
    elif row.deleted_at is not None:
        row.deleted_at = None
        row.kind = kind
        row.display_text = clean_text(text)
    return row


async def upsert(db: AsyncSession, user: User, text_norm: str, kind: str, display_text: str | None = None) -> dict:
    """Creates or changes the item. A changed kind moves all existing entries of the text_norm."""
    check_kind(kind)
    text_norm = _key(text_norm)
    row = await _row(db, user.id, text_norm)
    display = clean_text(display_text or "")
    if len(display) > TEXT_MAX_LENGTH:
        raise FoodDayError("text_too_long")
    if row is None:
        row = FoodMedDictionary(user_id=user.id, text_norm=text_norm, display_text=display or text_norm, kind=kind)
        db.add(row)
    else:
        if row.deleted_at is not None:
            row.deleted_at = None
        row.kind = kind
        if display:
            row.display_text = display
        row.updated_at = datetime.now(timezone.utc)
    await _move_entries(db, user, text_norm, kind)
    await db.commit()
    counts = await _usage_counts(db, user)
    return {"text_norm": row.text_norm, "display_text": row.display_text, "kind": row.kind,
            "usage_count": counts.get(row.text_norm, 0)}


async def delete(db: AsyncSession, user: User, text_norm: str) -> None:
    """Soft-deletes the item; the entries in days stay where they are."""
    row = await _row(db, user.id, normalize(text_norm))
    if row is None or row.deleted_at is not None:
        raise DictionaryItemNotFound()
    now = datetime.now(timezone.utc)
    row.deleted_at = now
    row.updated_at = now
    await db.commit()
