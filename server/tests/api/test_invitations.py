from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.models.invitation import Invitation
from app.models.user import User
from app.services.invitation_service import create_invitation, hash_token


@pytest.fixture
def invite_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "registration_mode", "invite")


def _payload(email: str, token: str | None = None) -> dict:
    body = {"email": email, "password": "secure123"}
    if token is not None:
        body["invite_token"] = token
    return body


@pytest.mark.asyncio
async def test_register_without_token_in_invite_mode(async_client, invite_mode):
    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-none@example.com"))
    assert r.status_code == 403
    assert r.json() == {"detail": "invite_required"}


@pytest.mark.asyncio
async def test_valid_token_registers_once(async_client, db_session, invite_mode):
    token, invitation = await create_invitation(db_session, days=7, note="friend")
    await db_session.commit()

    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-ok@example.com", token))
    assert r.status_code == 201

    await db_session.refresh(invitation)
    user = (await db_session.execute(select(User).where(User.email == "inv-ok@example.com"))).scalar_one()
    assert invitation.used_at is not None
    assert invitation.used_by_user_id == user.id

    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-ok2@example.com", token))
    assert r.status_code == 403
    assert r.json() == {"detail": "invite_invalid"}
    assert (await db_session.execute(select(User).where(User.email == "inv-ok2@example.com"))).first() is None


@pytest.mark.asyncio
async def test_expired_token(async_client, db_session, invite_mode):
    token, invitation = await create_invitation(db_session, days=7)
    invitation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-expired@example.com", token))
    assert r.status_code == 403
    assert r.json() == {"detail": "invite_invalid"}


@pytest.mark.asyncio
async def test_unknown_token(async_client, invite_mode):
    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-unknown@example.com", "nope"))
    assert r.status_code == 403
    assert r.json() == {"detail": "invite_invalid"}


@pytest.mark.asyncio
async def test_open_mode_registers_without_token(async_client):
    assert get_settings().registration_mode == "open"
    r = await async_client.post("/api/v1/auth/register", json=_payload("inv-open@example.com"))
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_only_hash_is_stored(db_session):
    token, invitation = await create_invitation(db_session)
    await db_session.commit()
    row = (await db_session.execute(select(Invitation).where(Invitation.id == invitation.id))).scalar_one()
    assert row.token_hash == hash_token(token)
    assert token not in row.token_hash
