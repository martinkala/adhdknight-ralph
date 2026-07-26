from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.migrate import MigrateRequest, MigrateResponse, MigrationSummary
from app.services.migration_service import process_migration

router = APIRouter(prefix="/api/v1/migrate", tags=["migrate"])


@router.post("", response_model=MigrateResponse, status_code=200)
async def migrate(
    body: MigrateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await process_migration(
        user_id=current_user.id,
        days=body.days,
        weight_config=body.weight_config,
        strategy=body.migration_strategy,
        db=db,
        app_id=body.app_id,
    )
    return MigrateResponse(
        migration_id=result.migration_id,
        summary=MigrationSummary(
            days_received=len(body.days),
            days_imported=result.days_imported,
            days_skipped=result.days_skipped,
            weights_imported=result.weights_imported,
        ),
        skipped=result.skipped,
    )
