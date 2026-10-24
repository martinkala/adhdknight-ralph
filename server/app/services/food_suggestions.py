"""Autocomplete suggestions from the user's own history (constitution D5, food-006 FR-1).

Matching, grouping and counting run in SQL (index user_id + category + text_norm), so the entries
are never loaded into Python. Every query is scoped to the user (A1)."""
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodDay, FoodEntry
from app.models.user import User
from app.services.food_constants import CATEGORY_GROUP
from app.services.food_days import FoodDayError
from app.services.food_text import normalize

SUGGESTION_GROUPS: tuple[str, ...] = tuple(sorted({g for g in CATEGORY_GROUP.values() if g is not None}))
SUGGESTIONS_LIMIT_DEFAULT, SUGGESTIONS_LIMIT_MAX = 10, 20
_ESCAPE = "\\"


def _like_literal(s: str) -> str:
    """Escapes LIKE wildcards so `%` and `_` in the query match literally."""
    return s.replace(_ESCAPE, _ESCAPE * 2).replace("%", _ESCAPE + "%").replace("_", _ESCAPE + "_")


async def suggestions(db: AsyncSession, user: User, group: str, q: str = "",
                      limit: int = SUGGESTIONS_LIMIT_DEFAULT) -> list[dict]:
    """The user's texts of the group whose text_norm starts with q or has a word starting with q,
    by number of uses (desc), then the last use (desc). `text` is the most used spelling."""
    if group not in SUGGESTION_GROUPS:
        raise FoodDayError("unknown_group")
    categories = [c for c, g in CATEGORY_GROUP.items() if g == group]
    filters = [
        FoodEntry.user_id == user.id,
        FoodEntry.deleted_at.is_(None),
        FoodEntry.category.in_(categories),
        FoodDay.deleted_at.is_(None),
    ]
    q_norm = normalize(q)
    if q_norm:
        pattern = _like_literal(q_norm)
        filters.append(or_(
            FoodEntry.text_norm.like(f"{pattern}%", escape=_ESCAPE),
            FoodEntry.text_norm.like(f"% {pattern}%", escape=_ESCAPE),
        ))
    base = select(FoodEntry).join(FoodDay, FoodDay.id == FoodEntry.day_id).where(*filters)

    count = func.count(FoodEntry.id)
    top = (await db.execute(
        base.with_only_columns(FoodEntry.text_norm, count)
        .group_by(FoodEntry.text_norm)
        .order_by(count.desc(), func.max(FoodDay.date).desc(), func.max(FoodEntry.created_at).desc(),
                  FoodEntry.text_norm)
        .limit(limit)
    )).all()
    if not top:
        return []

    # Most used original spelling per text_norm (ties: the most recent one); at most `limit` groups.
    spelling_count = func.count(FoodEntry.id)
    spellings = (await db.execute(
        base.where(FoodEntry.text_norm.in_([norm for norm, _ in top]))
        .with_only_columns(FoodEntry.text_norm, FoodEntry.text, spelling_count)
        .group_by(FoodEntry.text_norm, FoodEntry.text)
        .order_by(spelling_count.desc(), func.max(FoodDay.date).desc(), func.max(FoodEntry.created_at).desc())
    )).all()
    display: dict[str, str] = {}
    for norm, text, _ in spellings:
        display.setdefault(norm, text)
    return [{"text": display[norm], "count": n} for norm, n in top]
