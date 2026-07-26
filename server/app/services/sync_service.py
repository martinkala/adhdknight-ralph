import json
import uuid
from dataclasses import dataclass, field
from datetime import date as dt, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tracking import TrackingDay, ElementValue, DailyIndex
from app.schemas.sync import DaySyncItem, ConflictRecord
from app.schemas.compute import EntityNodeInput
from app.services.index_calculator import compute_daily


@dataclass
class SyncResult:
    sync_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    records_sent: int = 0
    records_accepted: int = 0
    records_conflicted: int = 0
    records_rejected: int = 0
    conflicts: list[ConflictRecord] = field(default_factory=list)
    computed_indices: list[dict] = field(default_factory=list)


async def process_batch_sync(
    user_id: str,
    days: list[DaySyncItem],
    device_id: str | None,
    db: AsyncSession,
    app_id: str = "adhd_tracker",
    entity_config: dict[str, EntityNodeInput] | None = None,
) -> SyncResult:
    result = SyncResult()
    result.records_sent = sum(len(d.values) for d in days)
    config_dict = {k: v.model_dump() for k, v in entity_config.items()} if entity_config else None

    for day_item in days:
        if dt.fromisoformat(day_item.date) > dt.today():
            result.records_rejected += len(day_item.values)
            result.conflicts.append(ConflictRecord(date=day_item.date, resolution="rejected_future_date"))
            continue

        # Get or create TrackingDay — scoped per app_id so different apps sharing the same
        # account don't collide on (user_id, date).
        stmt = select(TrackingDay).where(
            TrackingDay.user_id == user_id,
            TrackingDay.app_id == app_id,
            TrackingDay.date == day_item.date,
        )
        td_result = await db.execute(stmt)
        tracking_day = td_result.scalar_one_or_none()

        if tracking_day is None:
            tracking_day = TrackingDay(
                id=str(uuid.uuid4()),
                user_id=user_id,
                app_id=app_id,
                date=day_item.date,
                is_complete=day_item.is_complete,
                updated_at=day_item.updated_at,
                device_id=device_id,
            )
            db.add(tracking_day)
            await db.flush()

        for ev_item in day_item.values:
            # Get or create ElementValue — LWW by updated_at
            stmt2 = select(ElementValue).where(
                ElementValue.tracking_day_id == tracking_day.id,
                ElementValue.element_key == ev_item.element_key,
            )
            ev_result = await db.execute(stmt2)
            existing = ev_result.scalar_one_or_none()

            if existing is None:
                new_ev = ElementValue(
                    id=str(uuid.uuid4()),
                    tracking_day_id=tracking_day.id,
                    element_key=ev_item.element_key,
                    value_binary=ev_item.value_binary,
                    value_scale=ev_item.value_scale,
                    note=ev_item.note,
                    updated_at=ev_item.updated_at,
                )
                db.add(new_ev)
                result.records_accepted += 1
            else:
                # Normalize timezone for comparison (SQLite returns naive datetimes)
                existing_ts = existing.updated_at
                if existing_ts.tzinfo is None:
                    existing_ts = existing_ts.replace(tzinfo=timezone.utc)
                incoming_ts = ev_item.updated_at
                if incoming_ts.tzinfo is None:
                    incoming_ts = incoming_ts.replace(tzinfo=timezone.utc)

                if incoming_ts > existing_ts:
                    # LWW: incoming is newer → accept
                    existing.value_binary = ev_item.value_binary
                    existing.value_scale = ev_item.value_scale
                    existing.note = ev_item.note
                    existing.updated_at = ev_item.updated_at
                    result.records_accepted += 1
                else:
                    # Server is newer → conflict, server wins
                    result.records_conflicted += 1
                    result.conflicts.append(
                        ConflictRecord(
                            date=day_item.date,
                            element_key=ev_item.element_key,
                            resolution="server_wins",
                        )
                    )

        if config_dict is not None:
            await db.flush()
            await _compute_and_store_daily_index(db, tracking_day, config_dict, result)

    await db.commit()
    return result


async def _compute_and_store_daily_index(
    db: AsyncSession,
    tracking_day: TrackingDay,
    config_dict: dict[str, dict],
    result: SyncResult,
) -> None:
    # Recompute from the authoritative, post-LWW state in the DB — not from the incoming
    # batch — so a rejected/conflicted value doesn't leak into the stored index.
    ev_stmt = select(ElementValue).where(ElementValue.tracking_day_id == tracking_day.id)
    ev_result = await db.execute(ev_stmt)
    current_values = [
        {"element_key": ev.element_key, "value_binary": ev.value_binary, "value_scale": ev.value_scale}
        for ev in ev_result.scalars().all()
    ]

    computed = compute_daily(current_values, config_dict, list(config_dict.keys()))
    if computed is None:
        return

    detail_json = json.dumps([d.__dict__ for d in computed.detail])

    di_stmt = select(DailyIndex).where(DailyIndex.tracking_day_id == tracking_day.id)
    di_result = await db.execute(di_stmt)
    daily_index = di_result.scalar_one_or_none()

    if daily_index is None:
        daily_index = DailyIndex(
            id=str(uuid.uuid4()),
            tracking_day_id=tracking_day.id,
            index_value=computed.index_value,
            detail_json=detail_json,
        )
        db.add(daily_index)
    else:
        daily_index.index_value = computed.index_value
        daily_index.detail_json = detail_json
        daily_index.computed_at = datetime.now(timezone.utc)

    result.computed_indices.append({"date": tracking_day.date, "index_value": computed.index_value})
