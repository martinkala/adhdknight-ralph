from datetime import datetime, timezone
from fastapi import APIRouter
from app.db.database import check_db_connection

router = APIRouter(tags=["Health"])

VERSION = "0.1.0"


@router.get("/api/v1/health")
async def health():
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": VERSION,
        "db": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
