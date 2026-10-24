from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user, get_now
from app.models.user import User
from app.routers.food_entries import _http_error
from app.schemas.food import (
    ImportAdd,
    ImportCommitRequest,
    ImportDayPreview,
    ImportItemOut,
    ImportPreview,
    ImportPreviewRequest,
    ImportResult,
    ImportUnresolvedResponse,
)
from app.services import food_import_merge as merge
from app.services.food_days import FoodDayError, today_str
from app.services.food_import_parser import ImportItem, parse_import

router = APIRouter(prefix="/api/v1/food", tags=["food"])

IMPORT_MAX_BYTES = 1024 * 1024

_ERRORS = {
    413: {"description": "`input_too_large` (more than 1 MB)"},
    422: {"description": "`empty_input`, `invalid_format`, `invalid_json`, `missing_header`, "
                         "`unsupported_format_legacy` (formats 2022–2025, see `docs/food/import-mapping.md`)"},
}


def _item(item: ImportItem) -> ImportItemOut:
    quantity = None if item.quantity is None else float(item.quantity)
    return ImportItemOut(text=item.text, quantity=quantity, unit=item.unit, intensity=item.intensity)


def _preview(plan: merge.ImportPlan) -> ImportPreview:
    parsed = plan.parsed
    return ImportPreview(
        format=parsed.format,
        days=[
            ImportDayPreview(
                date=d.date,
                status=d.status,
                add=ImportAdd(
                    entries={category: [_item(i) for i in items] for category, items in d.entries.items()},
                    unclassified_meds=[_item(i) for i in d.unclassified],
                    weights=[{**w, "kg": float(w["kg"])} for w in d.weights],
                    blood_pressures=d.blood_pressures,
                    values=d.values,
                ),
                duplicates_skipped=d.duplicates_skipped,
                conflicts=d.conflicts,
            )
            for d in plan.days
        ],
        needs_classification=plan.needs_classification,
        issues=parsed.issues,
        skipped_empty_days=parsed.skipped_empty_days,
        unknown_columns=parsed.unknown_columns,
        totals=plan.totals(),
    )


async def _plan(body: ImportPreviewRequest, db: AsyncSession, user: User, now: datetime) -> merge.ImportPlan:
    if len(body.raw_text.encode("utf-8")) > IMPORT_MAX_BYTES:
        raise HTTPException(status_code=413, detail="input_too_large")
    try:
        parsed = parse_import(body.raw_text, body.format, today_str(user, now))
        return await merge.plan_import(db, user, parsed, body.classify)
    except FoodDayError as exc:
        raise _http_error(exc)


@router.post("/import/preview", response_model=ImportPreview, responses=_ERRORS)
async def import_preview(
    body: ImportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """What the import would add (`new` day / `merge` into an existing one), which duplicates it skips,
    where a day value conflicts and which medication items need "medication or supplement?".
    Stores nothing. Typos are not corrected."""
    return _preview(await _plan(body, db, current_user, now))


@router.post(
    "/import/commit",
    response_model=ImportResult,
    responses={**_ERRORS, 409: {"model": ImportUnresolvedResponse,
                                "description": "`unresolved`: a conflict without a resolution or an "
                                               "unclassified medication item; nothing was stored"}},
)
async def import_commit(
    body: ImportCommitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """Parses and merges again and stores everything in one transaction (an error stores nothing).
    Conflicts are decided by `resolutions`, the rest by `default_resolution`; `classify` answers
    unknown medication items and is saved to the dictionary."""
    plan = await _plan(body, db, current_user, now)
    try:
        await merge.commit_import(
            db, current_user, plan, [r.model_dump() for r in body.resolutions], body.default_resolution,
        )
    except merge.ImportUnresolved:
        content = ImportUnresolvedResponse(detail="unresolved", preview=_preview(plan))
        return JSONResponse(status_code=409, content=content.model_dump(mode="json"))
    return ImportResult(dates=[d.date for d in plan.days], totals=plan.totals())
