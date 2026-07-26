from datetime import date as dt, datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.compute import EntityNodeInput


class ElementValueSyncItem(BaseModel):
    element_key: str
    value_binary: int = 0
    value_scale: int | None = None
    note: str | None = None
    updated_at: datetime

    model_config = ConfigDict(extra="ignore")


class DaySyncItem(BaseModel):
    date: str
    is_complete: bool = False
    updated_at: datetime
    values: list[ElementValueSyncItem] = []

    model_config = ConfigDict(extra="ignore")


class BatchSyncRequest(BaseModel):
    schema_version: str = "1.0"
    app_id: str = "adhd_tracker"
    device_id: str | None = None
    # Optional: the client's current (active-only) entity tree — {key: {weight, impact,
    # parent, scale, scale_min, scale_max}}. When provided, the server recomputes and
    # persists a DailyIndex per synced day (see sync_service.process_batch_sync); when
    # omitted, sync behaves exactly as before (no index computed/stored).
    entity_config: dict[str, EntityNodeInput] | None = None
    days: list[DaySyncItem]

    model_config = ConfigDict(extra="ignore")


class ConflictRecord(BaseModel):
    date: str
    element_key: str | None = None
    resolution: str


class SyncSummary(BaseModel):
    days_received: int
    records_sent: int
    records_accepted: int
    records_conflicted: int
    records_rejected: int


class BatchSyncResponse(BaseModel):
    schema_version: str = "1.0"
    sync_id: str
    summary: SyncSummary
    conflicts: list[ConflictRecord] = []
    computed_indices: list[dict] = []
