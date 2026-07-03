from pydantic import BaseModel, ConfigDict


class EntityNodeInput(BaseModel):
    weight: float
    impact: int | None = None
    parent: str | None = None
    scale: bool = False

    model_config = ConfigDict(extra="ignore")


class ElementValueInput(BaseModel):
    element_key: str
    value_binary: int = 0
    value_scale: int | None = None

    model_config = ConfigDict(extra="ignore")


class ComputeDailyRequest(BaseModel):
    schema_version: str = "1.0"
    date: str
    entity_config: dict[str, EntityNodeInput]
    values: list[ElementValueInput]
    active_keys: list[str]

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "date": "2026-06-30",
                "entity_config": {
                    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
                    "overall_feeling": {"weight": 13.0, "impact": 1, "parent": None, "scale": True},
                },
                "values": [
                    {"element_key": "sleep", "value_binary": 1, "value_scale": 4},
                    {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5},
                ],
                "active_keys": ["sleep", "overall_feeling"],
            }
        },
    )


class DetailItem(BaseModel):
    element_key: str
    value_effective: float
    weight: float
    contribution: float
    impact: int


class ComputeDailyResponse(BaseModel):
    schema_version: str = "1.0"
    date: str
    index_value: float | None
    detail: list[DetailItem]
    active_weight_sum: float
    skipped_keys: list[str]


class DayInput(BaseModel):
    date: str
    values: list[ElementValueInput] = []
    active_keys: list[str] = []

    model_config = ConfigDict(extra="ignore")


class ComputeRangeRequest(BaseModel):
    schema_version: str = "1.0"
    entity_config: dict[str, EntityNodeInput]
    days: list[DayInput]

    model_config = ConfigDict(extra="ignore")


class RangeResult(BaseModel):
    date: str
    index_value: float | None
    status: str


class RangeSummary(BaseModel):
    days_requested: int
    days_computed: int
    days_no_data: int
    average_index: float | None


class ComputeRangeResponse(BaseModel):
    schema_version: str = "1.0"
    results: list[RangeResult]
    summary: RangeSummary
