import uuid
from dataclasses import dataclass, field
from datetime import timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tracking import TrackingDay, ElementValue
from app.schemas.sync import DaySyncItem, ConflictRecord


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
) -> SyncResult:
    result = SyncResult()
    result.records_sent = sum(len(d.values) for d in days)

    for day_item in days:
        # Get or create TrackingDay
        stmt = select(TrackingDay).where(
            TrackingDay.user_id == user_id,
            TrackingDay.date == day_item.date,
        )
        td_result = await db.execute(stmt)
        tracking_day = td_result.scalar_one_or_none()

        if tracking_day is None:
            tracking_day = TrackingDay(
                id=str(uuid.uuid4()),
                user_id=user_id,
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

    await db.commit()
    return result
