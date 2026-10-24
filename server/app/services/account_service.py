"""Account-level operations of the shared account (food-002): password change, deletion, settings."""
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation
from app.models.sync import SyncRecord
from app.models.tracking import DailyIndex, ElementValue, TrackingDay
from app.models.user import User
from app.models.weights import WeightConfig
from app.monitoring.models import IntegrityWarning, UserDataVolumeSnapshot
from app.services.auth_service import hash_password, verify_password


class WrongPasswordError(Exception):
    pass


async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise WrongPasswordError()
    user.password_hash = hash_password(new_password)
    await db.commit()


async def delete_account(db: AsyncSession, user: User, password: str) -> None:
    """Deletes the user and all data of every app. Explicit deletes (children first) instead of
    relying on ON DELETE CASCADE, which SQLite does not enforce without PRAGMA foreign_keys=ON.
    Food tables must be added here as they appear (food-003+)."""
    if not verify_password(password, user.password_hash):
        raise WrongPasswordError()
    user_id = user.id
    day_ids = select(TrackingDay.id).where(TrackingDay.user_id == user_id)
    statements = [
        delete(ElementValue).where(ElementValue.tracking_day_id.in_(day_ids)),
        delete(DailyIndex).where(DailyIndex.tracking_day_id.in_(day_ids)),
        delete(TrackingDay).where(TrackingDay.user_id == user_id),
        delete(WeightConfig).where(WeightConfig.user_id == user_id),
        delete(SyncRecord).where(SyncRecord.user_id == user_id),
        delete(UserDataVolumeSnapshot).where(UserDataVolumeSnapshot.user_id == user_id),
        delete(IntegrityWarning).where(IntegrityWarning.user_id == user_id),
        update(Invitation).where(Invitation.used_by_user_id == user_id).values(used_by_user_id=None),
        delete(User).where(User.id == user_id),
    ]
    for stmt in statements:
        await db.execute(stmt.execution_options(synchronize_session=False))
    await db.commit()
    db.expunge_all()


async def update_language(db: AsyncSession, user: User, language: str) -> User:
    user.language = language
    await db.commit()
    return user
