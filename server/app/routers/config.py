from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from app.services.entities_config_service import load_entities_raw, load_entities_version

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class EntitiesVersionResponse(BaseModel):
    app_id: str
    version: str


# Public — this is shared, non-sensitive app configuration (not user data), and needs to be
# reachable even before login so the offline-first startup check works for anonymous users.
@router.get("/entities/version", response_model=EntitiesVersionResponse)
async def get_entities_version(app_id: str = Query(default="adhd_tracker")):
    return EntitiesVersionResponse(app_id=app_id, version=load_entities_version(app_id))


@router.get("/entities", response_class=PlainTextResponse)
async def get_entities(app_id: str = Query(default="adhd_tracker")):
    return PlainTextResponse(load_entities_raw(app_id), media_type="application/x-yaml")
