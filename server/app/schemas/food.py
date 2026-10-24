"""Pydantic schemas of the Food diary API (`/api/v1/food`)."""
from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.food_constants import (
    DIGESTION_MAX,
    DIGESTION_MIN,
    INTENSITY_MAX,
    INTENSITY_MIN,
    SLEEP_QUALITY_MAX,
    SLEEP_QUALITY_MIN,
    TEXT_MAX_LENGTH,
)

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


def _check_date(value: str | None) -> str | None:
    if value is not None:
        date_type.fromisoformat(value)  # ValueError -> 422
    return value


class Entry(BaseModel):
    id: str
    category: str
    text: str
    # Normalized text (constitution D5), the key of the medication dictionary.
    text_norm: str
    quantity: float | None
    unit: str | None
    intensity: int | None
    position: int
    updated_at: datetime


class Weight(BaseModel):
    id: str
    kg: float
    measured_at: str | None
    note: str | None
    updated_at: datetime


class BloodPressure(BaseModel):
    id: str
    systolic: int
    diastolic: int
    pulse: int | None
    measured_at: str | None
    note: str | None
    updated_at: datetime


class DayDetail(BaseModel):
    schema_version: str = "1.0"
    id: str
    date: str
    sleep_quality: int | None
    stool: int | None
    gas: int | None
    updated_at: datetime
    # Every category of constitution D2, empty lists included.
    entries: dict[str, list[Entry]]
    weights: list[Weight]
    blood_pressures: list[BloodPressure]
    # Nearest existing (not deleted) days, for prev/next navigation.
    prev_date: str | None = None
    next_date: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "id": "0b6f8a8e-3c1e-4f7a-9d3c-2f1e5a7b9c01",
                "date": "2026-10-24",
                "sleep_quality": 2,
                "stool": 1,
                "gas": 3,
                "updated_at": "2026-10-24T07:30:00Z",
                "entries": {
                    "breakfast": [{
                        "id": "5d1c2b3a-0000-4000-8000-000000000001", "category": "breakfast", "text": "toasty",
                        "text_norm": "toasty", "quantity": 2, "unit": None, "intensity": None, "position": 0,
                        "updated_at": "2026-10-24T07:30:00Z",
                    }],
                    "lunch": [],
                },
                "weights": [{"id": "5d1c2b3a-0000-4000-8000-000000000002", "kg": 80.6, "measured_at": "07:00",
                             "note": None, "updated_at": "2026-10-24T07:00:00Z"}],
                "blood_pressures": [],
                "prev_date": "2026-10-23",
                "next_date": None,
            }
        }
    )


class TodayResponse(BaseModel):
    schema_version: str = "1.0"
    date: str
    exists: bool

    model_config = ConfigDict(
        json_schema_extra={"example": {"schema_version": "1.0", "date": "2026-10-24", "exists": False}}
    )


class DayCreate(BaseModel):
    # Missing date = today in the user's timezone.
    date: str | None = Field(default=None, pattern=DATE_PATTERN)
    id: str | None = Field(default=None, min_length=1, max_length=36)

    model_config = ConfigDict(json_schema_extra={"example": {"date": "2026-10-24"}})

    _valid_date = field_validator("date")(_check_date)


class DayUpdate(BaseModel):
    """Only the sent fields change; null clears the value."""

    sleep_quality: int | None = Field(default=None, ge=SLEEP_QUALITY_MIN, le=SLEEP_QUALITY_MAX)
    stool: int | None = Field(default=None, ge=DIGESTION_MIN, le=DIGESTION_MAX)
    gas: int | None = Field(default=None, ge=DIGESTION_MIN, le=DIGESTION_MAX)

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"sleep_quality": 2, "stool": None}})


# --- Entries (food-005 FR-1) -----------------------------------------------------------------

_ID = Field(default=None, min_length=1, max_length=36)
_QUANTITY = Field(default=None, gt=0, le=1_000_000)
_INTENSITY = Field(default=None, ge=INTENSITY_MIN, le=INTENSITY_MAX)
_NOTE = Field(default=None, max_length=TEXT_MAX_LENGTH)
_TIME = Field(default=None, max_length=5, description="Local time HH:MM (7:30 is accepted)")


class EntryCreate(BaseModel):
    """`text` is split on commas and new lines (not for `note`); without `quantity` the quantity is
    parsed from the start of each part ("2 toasty", "200 g ryža"). Repeated items are merged."""

    category: str
    text: str = Field(max_length=2000)
    quantity: float | None = _QUANTITY
    unit: str | None = None
    intensity: int | None = _INTENSITY
    id: str | None = _ID

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"example": {"category": "breakfast", "text": "2 toasty, kafe"}}
    )


class EntriesCreated(BaseModel):
    schema_version: str = "1.0"
    created: list[Entry]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "created": [
                    {"id": "5d1c2b3a-0000-4000-8000-000000000001", "category": "breakfast", "text": "toasty",
                     "text_norm": "toasty", "quantity": 2, "unit": None, "intensity": None, "position": 0,
                     "updated_at": "2026-10-24T07:30:00Z"},
                    {"id": "5d1c2b3a-0000-4000-8000-000000000002", "category": "breakfast", "text": "kafe",
                     "text_norm": "kafe", "quantity": None, "unit": None, "intensity": None, "position": 1,
                     "updated_at": "2026-10-24T07:30:00Z"},
                ],
            }
        }
    )


class EntryUpdate(BaseModel):
    """Only the sent fields change. `quantity: null` = no quantity. A new category puts the entry
    at the end of the target section."""

    text: str | None = Field(default=None, max_length=2000)
    quantity: float | None = _QUANTITY
    unit: str | None = None
    intensity: int | None = _INTENSITY
    category: str | None = None
    position: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"quantity": 0.5, "unit": "l"}})


class QuantityOption(BaseModel):
    quantity: float
    unit: str | None
    count: int


class QuantityOptions(BaseModel):
    schema_version: str = "1.0"
    options: list[QuantityOption]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "options": [{"quantity": 2, "unit": None, "count": 3}, {"quantity": 3, "unit": None, "count": 1}],
            }
        }
    )


class Suggestion(BaseModel):
    text: str
    count: int


class Suggestions(BaseModel):
    schema_version: str = "1.0"
    suggestions: list[Suggestion]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "suggestions": [{"text": "toasty", "count": 3}, {"text": "smažený tuniak", "count": 1}],
            }
        }
    )


# --- Medication dictionary and the common meds input (food-007) -------------------------------

MedKind = Literal["medication", "supplement"]


class MedDictionaryItem(BaseModel):
    text_norm: str
    display_text: str
    kind: str
    # Not deleted medication + supplement entries with this text_norm.
    usage_count: int


class MedDictionary(BaseModel):
    schema_version: str = "1.0"
    items: list[MedDictionaryItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "items": [
                    {"text_norm": "prestarium", "display_text": "Prestarium", "kind": "medication", "usage_count": 12},
                    {"text_norm": "zn", "display_text": "zn", "kind": "supplement", "usage_count": 30},
                ],
            }
        }
    )


class MedDictionaryItemResponse(MedDictionaryItem):
    schema_version: str = "1.0"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"schema_version": "1.0", "text_norm": "zn", "display_text": "zn", "kind": "supplement",
                        "usage_count": 30}
        }
    )


class MedDictionaryUpdate(BaseModel):
    """A changed `kind` moves all existing entries of the text between Medication and Supplements."""

    kind: MedKind
    display_text: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"kind": "supplement"}})


class MedsCreate(BaseModel):
    """Medication and supplements in one input ("zn, mg, omega+fe, prestarium"). `classify` answers
    the items returned in `needs_classification` (text_norm -> kind)."""

    text: str = Field(max_length=2000)
    classify: dict[str, MedKind] | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"text": "prestarium, zn", "classify": {"zn": "supplement"}}},
    )


class MedToClassify(BaseModel):
    text: str
    text_norm: str


class MedsResult(BaseModel):
    schema_version: str = "1.0"
    created: list[Entry]
    needs_classification: list[MedToClassify]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "created": [],
                "needs_classification": [{"text": "emanera", "text_norm": "emanera"}],
            }
        }
    )


# --- Measurements (food-005 FR-2) ------------------------------------------------------------


class WeightCreate(BaseModel):
    kg: float
    measured_at: str | None = _TIME
    note: str | None = _NOTE
    id: str | None = _ID
    # Without a time on today's day, use the current local time of the user.
    fill_time: bool = False

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"kg": 80.6, "measured_at": "07:00"}})


class WeightUpdate(BaseModel):
    """Only the sent fields change; null clears `measured_at` / `note`."""

    kg: float | None = None
    measured_at: str | None = _TIME
    note: str | None = _NOTE

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"kg": 80.2}})


class BloodPressureCreate(BaseModel):
    """Either `raw` ("130/85", "130/85 72", "130/85 72 7:30") or `systolic` + `diastolic`
    (+ `pulse`, `measured_at`). Errors: 422 `bp_format` / `bp_range` / `time_format`."""

    raw: str | None = Field(default=None, max_length=50)
    systolic: int | None = None
    diastolic: int | None = None
    pulse: int | None = None
    measured_at: str | None = _TIME
    note: str | None = _NOTE
    id: str | None = _ID
    # Without a time on today's day, use the current local time of the user.
    fill_time: bool = False

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"raw": "130/85 72 7:30"}})


class BloodPressureUpdate(BaseModel):
    """Only the sent fields change. `raw` replaces systolic, diastolic, pulse and time at once."""

    raw: str | None = Field(default=None, max_length=50)
    systolic: int | None = None
    diastolic: int | None = None
    pulse: int | None = None
    measured_at: str | None = _TIME
    note: str | None = _NOTE

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"pulse": 70, "note": "po káve"}})


# --- Overview: calendar and days list (food-008) ---------------------------------------------

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
# max(stool, gas): 1–3 ok, 4–6 mid, 7–10 bad, no values none.
Severity = Literal["ok", "mid", "bad", "none"]


class CalendarDay(BaseModel):
    date: str
    stool: int | None
    gas: int | None
    severity: Severity
    # Not deleted entries of every category.
    entry_count: int


class CalendarMonth(BaseModel):
    schema_version: str = "1.0"
    month: str
    today: str
    days: list[CalendarDay]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "month": "2026-10",
                "today": "2026-10-24",
                "days": [{"date": "2026-10-20", "stool": 2, "gas": 5, "severity": "mid", "entry_count": 7}],
            }
        }
    )


class DaySummary(BaseModel):
    date: str
    stool: int | None
    gas: int | None
    severity: Severity
    sleep_quality: int | None
    weights: list[float]
    # "130/85" or "130/85 72" with pulse.
    bp: list[str]
    # First food texts in section order (breakfast … unassigned).
    food_preview: list[str]
    entry_count: int


class DayList(BaseModel):
    schema_version: str = "1.0"
    page: int
    page_size: int
    total: int
    days: list[DaySummary]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "page": 1,
                "page_size": 30,
                "total": 1,
                "days": [{
                    "date": "2026-10-20", "stool": 4, "gas": 6, "severity": "mid", "sleep_quality": 2,
                    "weights": [80.6], "bp": ["130/85 72"], "food_preview": ["toasty", "kafe", "ryža"],
                    "entry_count": 9,
                }],
            }
        }
    )
