"""Invitation-only registration (food-002, constitution B5)."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation


class InvitationError(Exception):
    """`code` is the API detail: invite_required | invite_invalid."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes even for DateTime(timezone=True); they are stored as UTC.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def create_invitation(db: AsyncSession, days: int = 7, note: str | None = None) -> tuple[str, Invitation]:
    """Creates an invitation and returns (plain token, row). Only the hash is persisted."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        token_hash=hash_token(token),
        note=note,
        created_at=now,
        expires_at=now + timedelta(days=days),
    )
    db.add(invitation)
    await db.flush()
    return token, invitation


async def consume_invitation(db: AsyncSession, token: str | None, user_id: str) -> None:
    """Marks the invitation as used by `user_id` within the caller's transaction.
    The conditional UPDATE (`used_at IS NULL`) makes a token usable exactly once even under races."""
    if not token:
        raise InvitationError("invite_required")
    result = await db.execute(select(Invitation).where(Invitation.token_hash == hash_token(token)))
    invitation = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if invitation is None or invitation.used_at is not None or _as_utc(invitation.expires_at) <= now:
        raise InvitationError("invite_invalid")
    claimed = await db.execute(
        update(Invitation)
        .where(Invitation.id == invitation.id, Invitation.used_at.is_(None))
        .values(used_at=now, used_by_user_id=user_id)
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        raise InvitationError("invite_invalid")
