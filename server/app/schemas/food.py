"""Pydantic schemas of the Food diary API (`/api/v1/food`)."""
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.food_constants import (
    DIGESTION_MAX,
    DIGESTION_MIN,
    SLEEP_QUALITY_MAX,
    SLEEP_QUALITY_MIN,
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
                        "quantity": 2, "unit": None, "intensity": None, "position": 0,
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
