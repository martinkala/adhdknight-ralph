from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers.food_days import DatePath, _day_or_404
from app.routers.food_entries import _http_error
from app.schemas.food import (
    Entry,
    MedDictionary,
    MedDictionaryItemResponse,
    MedDictionaryUpdate,
    MedsCreate,
    MedsResult,
)
from app.services import food_entries, food_med_dictionary
from app.services.food_days import FoodDayError

router = APIRouter(prefix="/api/v1/food", tags=["food"])

_ITEM_NOT_FOUND = {404: {"description": "`dictionary_item_not_found`"}}


@router.get("/med-dictionary", response_model=MedDictionary)
async def get_med_dictionary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The user's "medication or supplement" answers, alphabetically."""
    return MedDictionary(items=await food_med_dictionary.list_items(db, current_user))


@router.put(
    "/med-dictionary/{text_norm:path}",
    response_model=MedDictionaryItemResponse,
    responses={422: {"description": "`empty_text`, `text_too_long`, `invalid_kind`"}},
)
async def put_med_dictionary_item(
    text_norm: str,
    body: MedDictionaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates or changes an item. A changed `kind` moves all existing entries of the text
    between Medication and Supplements."""
    try:
        item = await food_med_dictionary.upsert(db, current_user, text_norm, body.kind, body.display_text)
    except FoodDayError as exc:
        raise _http_error(exc)
    return MedDictionaryItemResponse(**item)


@router.delete("/med-dictionary/{text_norm:path}", status_code=status.HTTP_204_NO_CONTENT, responses=_ITEM_NOT_FOUND)
async def delete_med_dictionary_item(
    text_norm: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes the item; the entries in days stay where they are."""
    try:
        await food_med_dictionary.delete(db, current_user, text_norm)
    except FoodDayError as exc:
        raise _http_error(exc)


@router.post(
    "/days/{date}/meds",
    response_model=MedsResult,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Unknown items in `needs_classification`, nothing was stored"},
        404: {"description": "`day_not_found`"},
        422: {"description": "`empty_text`, `text_too_long`"},
    },
)
async def add_meds(
    date: DatePath,
    body: MedsCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Medication and supplements in one input, sorted by the user's dictionary. While an item is
    unknown, nothing is stored (200) and the client asks and repeats the request with `classify`."""
    day = await _day_or_404(db, current_user, date)
    try:
        result = await food_entries.add_meds(db, day, body.text, body.classify)
    except FoodDayError as exc:
        raise _http_error(exc)
    if result["needs_classification"]:
        response.status_code = status.HTTP_200_OK
    return MedsResult(
        created=[Entry.model_validate(e, from_attributes=True) for e in result["created"]],
        needs_classification=result["needs_classification"],
    )
