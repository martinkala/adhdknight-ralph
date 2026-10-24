from typing import Literal
from pydantic import BaseModel, ConfigDict

Language = Literal["sk", "cs", "en"]


class UserSettingsResponse(BaseModel):
    schema_version: str = "1.0"
    language: Language
    timezone: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"schema_version": "1.0", "language": "sk", "timezone": "Europe/Bratislava"}}
    )


class UserSettingsUpdate(BaseModel):
    language: Language

    model_config = ConfigDict(json_schema_extra={"example": {"language": "en"}})


class DeleteAccountRequest(BaseModel):
    password: str
    # Explicit confirmation that the data of ALL apps (ADHD and Food) will be deleted.
    confirm: Literal["DELETE"]

    model_config = ConfigDict(json_schema_extra={"example": {"password": "secret123", "confirm": "DELETE"}})
