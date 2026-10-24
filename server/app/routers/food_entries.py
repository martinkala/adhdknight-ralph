from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user, get_now
from app.models.food import FoodBloodPressure, FoodWeight
from app.models.user import User
from app.routers.food_days import DatePath, _day_or_404
from app.schemas.food import (
    BloodPressure,
    BloodPressureCreate,
    BloodPressureUpdate,
    EntriesCreated,
    Entry,
    EntryCreate,
    EntryUpdate,
    QuantityOptions,
    Suggestions,
    Weight,
    WeightCreate,
    WeightUpdate,
)
from app.services import food_entries, food_measurement_records as records, food_suggestions
from app.services.food_days import FoodDayError
from app.services.food_suggestions import SUGGESTIONS_LIMIT_DEFAULT, SUGGESTIONS_LIMIT_MAX

router = APIRouter(prefix="/api/v1/food", tags=["food"])

_ERROR_STATUS = {"id_exists": 409, "entry_not_found": 404, "measurement_not_found": 404}
_ENTRY_NOT_FOUND = {404: {"description": "`entry_not_found`"}}
_MEASUREMENT_NOT_FOUND = {404: {"description": "`measurement_not_found`"}}


def _http_error(exc: FoodDayError) -> HTTPException:
    """Domain error codes -> HTTP status; validation codes (empty_text, bp_range, ...) are 422."""
    return HTTPException(status_code=_ERROR_STATUS.get(exc.code, 422), detail=exc.code)


def _changes(body) -> dict:
    return body.model_dump(include=body.model_fields_set)


# --- Entries ---------------------------------------------------------------------------------


@router.post(
    "/days/{date}/entries",
    response_model=EntriesCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "`day_not_found`"},
        409: {"description": "`id_exists`"},
        422: {"description": "`empty_text`, `text_too_long`, `unknown_category`, `intensity_not_allowed`, "
                             "`invalid_unit`, `unit_without_quantity`, `id_requires_single_entry`"},
    },
)
async def add_entries(
    date: DatePath,
    body: EntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adds one or more entries to the end of a section ("2 toasty, kafe" -> 2 entries)."""
    day = await _day_or_404(db, current_user, date)
    try:
        created = await food_entries.add_entries(
            db, day, body.category, body.text, body.quantity, body.unit, body.intensity, body.id
        )
    except FoodDayError as exc:
        raise _http_error(exc)
    return EntriesCreated(created=[Entry.model_validate(e, from_attributes=True) for e in created])


@router.patch("/entries/{entry_id}", response_model=Entry, responses=_ENTRY_NOT_FOUND)
async def patch_entry(
    entry_id: str,
    body: EntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Changes the sent fields. `quantity: null` removes the quantity."""
    try:
        entry = await food_entries.get_entry(db, current_user, entry_id)
        entry = await food_entries.update_entry(db, entry, _changes(body))
    except FoodDayError as exc:
        raise _http_error(exc)
    return Entry.model_validate(entry, from_attributes=True)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, responses=_ENTRY_NOT_FOUND)
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        entry = await food_entries.get_entry(db, current_user, entry_id)
    except FoodDayError as exc:
        raise _http_error(exc)
    await food_entries.delete_entry(db, entry)


@router.get("/quantities", response_model=QuantityOptions, responses={422: {"description": "`unknown_category`"}})
async def get_quantities(
    text: Annotated[str, Query(max_length=200, examples=["toasty"])],
    category: Annotated[str, Query(examples=["breakfast"])],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The most used quantities (max. 5) of the text in the category's autocomplete group."""
    try:
        options = await food_entries.quantity_options(db, current_user, text, category)
    except FoodDayError as exc:
        raise _http_error(exc)
    return QuantityOptions(options=options)


@router.get("/suggestions", response_model=Suggestions, responses={422: {"description": "`unknown_group`"}})
async def get_suggestions(
    group: Annotated[str, Query(examples=["food"], description="`food`, `meds` or `sport`")],
    q: Annotated[str, Query(max_length=200, examples=["tu"])] = "",
    limit: Annotated[int, Query(ge=1, le=SUGGESTIONS_LIMIT_MAX)] = SUGGESTIONS_LIMIT_DEFAULT,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Autocomplete: the user's texts of the group matching `q` from the start of the text or of any
    word, without diacritics, by number of uses. An empty `q` returns the most used texts."""
    try:
        items = await food_suggestions.suggestions(db, current_user, group, q, limit)
    except FoodDayError as exc:
        raise _http_error(exc)
    return Suggestions(suggestions=items)


# --- Measurements ----------------------------------------------------------------------------

_MEASUREMENT_ERRORS = {
    404: {"description": "`day_not_found`"},
    409: {"description": "`id_exists`"},
    422: {"description": "`weight_range`, `bp_format`, `bp_range`, `time_format`"},
}


@router.post("/days/{date}/weights", response_model=Weight, status_code=status.HTTP_201_CREATED,
             responses=_MEASUREMENT_ERRORS)
async def add_weight(
    date: DatePath,
    body: WeightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    day = await _day_or_404(db, current_user, date)
    try:
        weight = await records.add_weight(db, current_user, day, body.model_dump(), now)
    except FoodDayError as exc:
        raise _http_error(exc)
    return Weight.model_validate(weight, from_attributes=True)


@router.patch("/weights/{weight_id}", response_model=Weight, responses=_MEASUREMENT_NOT_FOUND)
async def patch_weight(
    weight_id: str,
    body: WeightUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        weight = await records.get_measurement(db, current_user, FoodWeight, weight_id)
        weight = await records.update_weight(db, weight, _changes(body))
    except FoodDayError as exc:
        raise _http_error(exc)
    return Weight.model_validate(weight, from_attributes=True)


@router.delete("/weights/{weight_id}", status_code=status.HTTP_204_NO_CONTENT, responses=_MEASUREMENT_NOT_FOUND)
async def delete_weight(
    weight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        weight = await records.get_measurement(db, current_user, FoodWeight, weight_id)
    except FoodDayError as exc:
        raise _http_error(exc)
    await records.delete_measurement(db, weight)


@router.post("/days/{date}/blood-pressures", response_model=BloodPressure, status_code=status.HTTP_201_CREATED,
             responses=_MEASUREMENT_ERRORS)
async def add_blood_pressure(
    date: DatePath,
    body: BloodPressureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    now: datetime = Depends(get_now),
):
    """Quick entry `{"raw": "130/85 72 7:30"}` or separate fields."""
    day = await _day_or_404(db, current_user, date)
    try:
        pressure = await records.add_blood_pressure(db, current_user, day, body.model_dump(), now)
    except FoodDayError as exc:
        raise _http_error(exc)
    return BloodPressure.model_validate(pressure, from_attributes=True)


@router.patch("/blood-pressures/{pressure_id}", response_model=BloodPressure, responses=_MEASUREMENT_NOT_FOUND)
async def patch_blood_pressure(
    pressure_id: str,
    body: BloodPressureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pressure = await records.get_measurement(db, current_user, FoodBloodPressure, pressure_id)
        pressure = await records.update_blood_pressure(db, pressure, _changes(body))
    except FoodDayError as exc:
        raise _http_error(exc)
    return BloodPressure.model_validate(pressure, from_attributes=True)


@router.delete("/blood-pressures/{pressure_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses=_MEASUREMENT_NOT_FOUND)
async def delete_blood_pressure(
    pressure_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pressure = await records.get_measurement(db, current_user, FoodBloodPressure, pressure_id)
    except FoodDayError as exc:
        raise _http_error(exc)
    await records.delete_measurement(db, pressure)
