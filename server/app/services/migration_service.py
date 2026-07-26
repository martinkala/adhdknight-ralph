import uuid
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tracking import TrackingDay, ElementValue
from app.models.weights import WeightConfig
from app.schemas.migrate import (
    MigrationDayItem, MigrationWeightItem, MigrationStrategy, MigrationSkipRecord,
)


@dataclass
class MigrationResult:
    migration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    days_imported: int = 0
    days_skipped: int = 0
    weights_imported: int = 0
    skipped: list[MigrationSkipRecord] = field(default_factory=list)


async def process_migration(
    user_id: str,
    days: list[MigrationDayItem],
    weight_config: list[MigrationWeightItem],
    strategy: MigrationStrategy,
    db: AsyncSession,
    app_id: str = "adhd_tracker",
) -> MigrationResult:
    result = MigrationResult()

    for day_item in days:
        stmt = select(TrackingDay).where(
            TrackingDay.user_id == user_id,
            TrackingDay.app_id == app_id,
            TrackingDay.date == day_item.date,
        )
        td_result = await db.execute(stmt)
        existing_day = td_result.scalar_one_or_none()

        if existing_day is not None and strategy == MigrationStrategy.skip_existing:
            result.days_skipped += 1
            result.skipped.append(MigrationSkipRecord(date=day_item.date, reason="already_exists"))
            continue

        if existing_day is None:
            tracking_day = TrackingDay(
                id=str(uuid.uuid4()),
                user_id=user_id,
                app_id=app_id,
                date=day_item.date,
                is_complete=day_item.is_complete,
            )
            db.add(tracking_day)
            await db.flush()
        else:
            # mobile_source_of_truth: overwrite
            tracking_day = existing_day
            tracking_day.is_complete = day_item.is_complete
            # Delete existing element values
            for ev in list(tracking_day.values):
                await db.delete(ev)
            await db.flush()

        for ev_item in day_item.values:
            ev = ElementValue(
                id=str(uuid.uuid4()),
                tracking_day_id=tracking_day.id,
                element_key=ev_item.element_key,
                value_binary=ev_item.value_binary,
                value_scale=ev_item.value_scale,
            )
            db.add(ev)

        result.days_imported += 1

    # Import weight config
    for wc_item in weight_config:
        stmt = select(WeightConfig).where(
            WeightConfig.user_id == user_id,
            WeightConfig.app_id == app_id,
            WeightConfig.element_key == wc_item.element_key,
        )
        wc_result = await db.execute(stmt)
        existing_wc = wc_result.scalar_one_or_none()
        if existing_wc is None:
            wc = WeightConfig(
                id=str(uuid.uuid4()),
                user_id=user_id,
                app_id=app_id,
                element_key=wc_item.element_key,
                weight_default=wc_item.weight_default,
                weight_personal=wc_item.weight_personal,
            )
            db.add(wc)
            result.weights_imported += 1
        else:
            existing_wc.weight_default = wc_item.weight_default
            existing_wc.weight_personal = wc_item.weight_personal
            result.weights_imported += 1

    await db.commit()
    return result
