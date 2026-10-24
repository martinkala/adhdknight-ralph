from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.models.sync import SyncRecord, SyncType
from app.models.tracking import DailyIndex, ElementValue, TrackingDay
from app.models.user import User
from app.models.weights import WeightConfig

PASSWORD = "secure123"


async def _register(async_client, email: str) -> dict:
    r = await async_client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _sync_days(async_client, headers: dict, days: int = 2) -> None:
    base = datetime.now(timezone.utc) - timedelta(days=days + 1)
    payload = {
        "schema_version": "1.0",
        "device_id": "dev",
        "days": [
            {
                "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
                "is_complete": True,
                "updated_at": (base + timedelta(days=i)).isoformat(),
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 4,
                            "updated_at": (base + timedelta(days=i)).isoformat()}],
            }
            for i in range(days)
        ],
    }
    r = await async_client.post("/api/v1/sync/batch", json=payload, headers=headers)
    assert r.status_code == 200, r.text


async def _user_row_counts(db, user_id: str) -> dict:
    day_ids = select(TrackingDay.id).where(TrackingDay.user_id == user_id)
    queries = {
        "users": select(func.count()).select_from(User).where(User.id == user_id),
        "tracking_days": select(func.count()).select_from(TrackingDay).where(TrackingDay.user_id == user_id),
        "element_values": select(func.count()).select_from(ElementValue).where(ElementValue.tracking_day_id.in_(day_ids)),
        "daily_indices": select(func.count()).select_from(DailyIndex).where(DailyIndex.tracking_day_id.in_(day_ids)),
        "weight_configs": select(func.count()).select_from(WeightConfig).where(WeightConfig.user_id == user_id),
        "sync_records": select(func.count()).select_from(SyncRecord).where(SyncRecord.user_id == user_id),
    }
    return {name: (await db.execute(q)).scalar_one() for name, q in queries.items()}


async def _user_id(db, email: str) -> str:
    return (await db.execute(select(User.id).where(User.email == email))).scalar_one()


async def _seed_extra_adhd_rows(db, user_id: str) -> None:
    """Sync batch does not write these tables (a 1-element day gets no index), so they are seeded directly."""
    day_ids = (await db.execute(select(TrackingDay.id).where(TrackingDay.user_id == user_id))).scalars().all()
    for day_id in day_ids:
        db.add(DailyIndex(tracking_day_id=day_id, index_value=50.0))
    db.add(SyncRecord(user_id=user_id, sync_type=SyncType.batch, records_sent=2, records_accepted=2))
    db.add(WeightConfig(user_id=user_id, element_key="sleep", weight_default=1.0))
    await db.commit()


# --- change password -------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password(async_client):
    headers = await _register(async_client, "chpw@example.com")
    r = await async_client.post(
        "/api/v1/auth/change-password",
        json={"old_password": PASSWORD, "new_password": "brand-new-pass"},
        headers=headers,
    )
    assert r.status_code == 204
    old = await async_client.post("/api/v1/auth/login", json={"email": "chpw@example.com", "password": PASSWORD})
    assert old.status_code == 401
    new = await async_client.post("/api/v1/auth/login", json={"email": "chpw@example.com", "password": "brand-new-pass"})
    assert new.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(async_client):
    headers = await _register(async_client, "chpw-wrong@example.com")
    r = await async_client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "not-my-password", "new_password": "brand-new-pass"},
        headers=headers,
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "wrong_password"}


@pytest.mark.asyncio
async def test_change_password_too_short(async_client):
    headers = await _register(async_client, "chpw-short@example.com")
    r = await async_client.post(
        "/api/v1/auth/change-password",
        json={"old_password": PASSWORD, "new_password": "short"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_change_password_requires_auth(async_client):
    r = await async_client.post("/api/v1/auth/change-password", json={"old_password": "x", "new_password": "yyyyyyyy"})
    assert r.status_code == 401


# --- delete account --------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_account_removes_all_adhd_data_and_keeps_others(async_client, db_session):
    victim = await _register(async_client, "del-me@example.com")
    other = await _register(async_client, "del-other@example.com")
    await _sync_days(async_client, victim)
    await _sync_days(async_client, other)
    victim_id = await _user_id(db_session, "del-me@example.com")
    other_id = await _user_id(db_session, "del-other@example.com")
    await _seed_extra_adhd_rows(db_session, victim_id)
    await _seed_extra_adhd_rows(db_session, other_id)
    before = await _user_row_counts(db_session, victim_id)
    assert before["tracking_days"] == 2 and before["element_values"] == 2 and before["sync_records"] == 1
    assert before["daily_indices"] == 2 and before["weight_configs"] == 1
    other_before = await _user_row_counts(db_session, other_id)

    r = await async_client.request(
        "DELETE", "/api/v1/user/me", json={"password": PASSWORD, "confirm": "DELETE"}, headers=victim
    )
    assert r.status_code == 204

    assert all(count == 0 for count in (await _user_row_counts(db_session, victim_id)).values())
    assert await _user_row_counts(db_session, other_id) == other_before
    # The deleted user's token no longer works.
    assert (await async_client.get("/api/v1/user/settings", headers=victim)).status_code == 401


@pytest.mark.asyncio
async def test_delete_account_wrong_password(async_client):
    headers = await _register(async_client, "del-wrong@example.com")
    r = await async_client.request(
        "DELETE", "/api/v1/user/me", json={"password": "not-my-password", "confirm": "DELETE"}, headers=headers
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "wrong_password"}


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"password": PASSWORD}, {"password": PASSWORD, "confirm": "yes"}])
async def test_delete_account_requires_confirm(async_client, body):
    headers = await _register(async_client, f"del-confirm-{len(body)}-{body.get('confirm', '')}@example.com")
    r = await async_client.request("DELETE", "/api/v1/user/me", json=body, headers=headers)
    assert r.status_code == 422


# --- settings ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_defaults_and_patch(async_client):
    headers = await _register(async_client, "settings@example.com")
    r = await async_client.get("/api/v1/user/settings", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"schema_version": "1.0", "language": "sk", "timezone": "Europe/Bratislava"}

    r = await async_client.patch("/api/v1/user/settings", json={"language": "en"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["language"] == "en"
    assert (await async_client.get("/api/v1/user/settings", headers=headers)).json()["language"] == "en"


@pytest.mark.asyncio
async def test_settings_invalid_language(async_client):
    headers = await _register(async_client, "settings-de@example.com")
    r = await async_client.patch("/api/v1/user/settings", json={"language": "de"}, headers=headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_settings_are_per_user(async_client):
    a = await _register(async_client, "settings-a@example.com")
    b = await _register(async_client, "settings-b@example.com")
    await async_client.patch("/api/v1/user/settings", json={"language": "cs"}, headers=a)
    assert (await async_client.get("/api/v1/user/settings", headers=b)).json()["language"] == "sk"


@pytest.mark.asyncio
async def test_settings_require_auth(async_client):
    assert (await async_client.get("/api/v1/user/settings")).status_code == 401
