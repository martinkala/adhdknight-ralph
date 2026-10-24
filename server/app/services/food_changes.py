"""Changes since a point in time (food-009 FR-3, constitution B2) for the Android sync.
Returns the user's entities with `updated_at > since`, soft-deleted ones included (tombstones)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodMedDictionary, FoodWeight
from app.models.user import User
from app.schemas.food import (
    BloodPressureChange,
    DayChange,
    EntryChange,
    FoodChanges,
    MedDictionaryChange,
    WeightChange,
)

CHANGES_LIMIT_DEFAULT = 500
CHANGES_LIMIT_MAX = 1000

# Response list -> (model, response schema)
_KINDS = {
    "days": (FoodDay, DayChange),
    "entries": (FoodEntry, EntryChange),
    "weights": (FoodWeight, WeightChange),
    "blood_pressures": (FoodBloodPressure, BloodPressureChange),
    "med_dictionary": (FoodMedDictionary, MedDictionaryChange),
}
_TIMESTAMPS = ("created_at", "updated_at", "deleted_at")


def _utc(value: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; every stored timestamp is UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


async def _rows(db: AsyncSession, model, user: User, since: datetime | None, limit: int) -> list:
    stmt = select(model).where(model.user_id == user.id)
    if since is not None:
        stmt = stmt.where(model.updated_at > since)
    stmt = stmt.order_by(model.updated_at, model.id).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


def _change(schema, row):
    change = schema.model_validate(row, from_attributes=True)
    return change.model_copy(update={name: _utc(getattr(change, name)) for name in _TIMESTAMPS})


async def changes(
    db: AsyncSession, user: User, since: datetime | None, limit: int = CHANGES_LIMIT_DEFAULT
) -> FoodChanges:
    """At most `limit` changes, oldest first across all entities. A page never splits a group of changes
    with the same `updated_at` (e.g. a deleted day with its entries), so `server_time` = the last
    `updated_at` of the page is a safe next `since`. Without `has_more`, `server_time` is the time
    before the queries started."""
    started = datetime.now(timezone.utc)
    since = _utc(since)

    # The oldest limit + 1 rows of each kind contain the oldest limit + 1 rows overall.
    found = []
    for kind, (model, _) in _KINDS.items():
        found += [(_utc(row.updated_at), kind, row) for row in await _rows(db, model, user, since, limit + 1)]
    found.sort(key=lambda item: (item[0], item[2].id))

    has_more = len(found) > limit
    server_time = started
    if has_more:
        last = found[limit - 1][0]
        page = [item for item in found[:limit] if item[0] < last] if found[limit][0] == last else found[:limit]
        if not page:
            # One group of the same timestamp is larger than the limit: return the whole group.
            page = []
            for kind, (model, _) in _KINDS.items():
                result = await db.execute(
                    select(model).where(model.user_id == user.id, model.updated_at == last).order_by(model.id)
                )
                page += [(last, kind, row) for row in result.scalars().all()]
        found = page
        server_time = found[-1][0]

    lists: dict[str, list] = {kind: [] for kind in _KINDS}
    for _, kind, row in found:
        lists[kind].append(_change(_KINDS[kind][1], row))
    return FoodChanges(server_time=server_time, has_more=has_more, **lists)
