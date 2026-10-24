from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user, get_now
from app.models.user import User
from app.schemas.food import DATE_PATTERN, FoodChanges, FoodExport, _check_date
from app.services import food_changes, food_export
from app.services.food_changes import CHANGES_LIMIT_DEFAULT, CHANGES_LIMIT_MAX
from app.services.food_days import today_str

router = APIRouter(prefix="/api/v1/food", tags=["food"])

DateQuery = Annotated[str | None, Query(pattern=DATE_PATTERN, examples=["2026-10-01"])]


def _valid_range(date_from: str | None, date_to: str | None) -> None:
    try:
        _check_date(date_from)
        _check_date(date_to)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_date")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="invalid_range")


@router.get(
    "/export",
    response_model=FoodExport,
    responses={
        200: {"content": {"text/csv": {"schema": {"type": "string"}}},
              "description": "`FoodExport` JSON, or long-format CSV with `format=csv`"},
        422: {"description": "`invalid_date`, `invalid_range`"},
    },
)
async def export(
    format: Literal["json", "csv"] = "json",
    date_from: Annotated[DateQuery, Query(alias="from")] = None,
    date_to: Annotated[DateQuery, Query(alias="to")] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """All not deleted data of the user in the range (both ends optional, inclusive) as a download.
    CSV: UTF-8 with a BOM, one row per entry, measurement and filled day value."""
    _valid_range(date_from, date_to)
    data = await food_export.build_export(db, current_user, date_from, date_to, now)
    name = food_export.filename(data, date_from, date_to, today_str(current_user, now), format)
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    if format == "csv":
        return Response(food_export.to_csv(data), media_type="text/csv; charset=utf-8", headers=headers)
    return Response(data.model_dump_json(), media_type="application/json", headers=headers)


@router.get("/changes", response_model=FoodChanges)
async def changes(
    since: Annotated[datetime | None, Query(examples=["2026-10-24T18:00:00Z"])] = None,
    limit: Annotated[int, Query(ge=1, le=CHANGES_LIMIT_MAX)] = CHANGES_LIMIT_DEFAULT,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Days, entries, measurements and dictionary items changed after `since` (ISO 8601, UTC without
    a zone), deleted ones included with `deleted_at`. Without `since` everything. Use `server_time`
    as the next `since`; while `has_more` is true, call again."""
    return await food_changes.changes(db, current_user, since, limit)
