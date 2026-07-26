from datetime import date as dt
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator


class MigrationStrategy(str, Enum):
    mobile_source_of_truth = "mobile_source_of_truth"
    skip_existing = "skip_existing"


class MigrationWeightItem(BaseModel):
    element_key: str
    weight_default: float
    weight_personal: float | None = None


class MigrationElementValue(BaseModel):
    element_key: str
    value_binary: int = 0
    value_scale: int | None = None


class MigrationDayItem(BaseModel):
    date: str
    is_complete: bool = False
    values: list[MigrationElementValue] = []

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: str) -> str:
        if dt.fromisoformat(v) > dt.today():
            raise ValueError("Date cannot be in the future")
        return v

    model_config = ConfigDict(extra="ignore")


class MigrateRequest(BaseModel):
    schema_version: str = "1.0"
    source: str = "android"
    app_id: str = "adhd_tracker"
    migration_strategy: MigrationStrategy
    days: list[MigrationDayItem]
    weight_config: list[MigrationWeightItem] = []


class MigrationSkipRecord(BaseModel):
    date: str
    reason: str


class MigrationSummary(BaseModel):
    days_received: int
    days_imported: int
    days_skipped: int
    weights_imported: int


class MigrateResponse(BaseModel):
    schema_version: str = "1.0"
    migration_id: str
    summary: MigrationSummary
    skipped: list[MigrationSkipRecord] = []
