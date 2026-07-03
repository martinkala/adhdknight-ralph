import pytest
from datetime import datetime, timedelta, timezone

BASE_TIME = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)


async def _register_and_token(async_client, email="sync@example.com", password="secure123"):
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": password})
    return reg.json()["access_token"]


def _make_batch(days_count: int, base_time=BASE_TIME) -> dict:
    days = []
    for i in range(days_count):
        date = (base_time + timedelta(days=i)).strftime("%Y-%m-%d")
        days.append({
            "date": date,
            "is_complete": True,
            "updated_at": (base_time + timedelta(days=i)).isoformat(),
            "values": [
                {
                    "element_key": "sleep",
                    "value_binary": 1,
                    "value_scale": 4,
                    "updated_at": (base_time + timedelta(days=i)).isoformat(),
                }
            ],
        })
    return {"schema_version": "1.0", "device_id": "test-device", "days": days}


@pytest.mark.asyncio
async def test_batch_sync_3_days(async_client):
    token = await _register_and_token(async_client, "sync3@example.com")
    payload = _make_batch(3)
    response = await async_client.post(
        "/api/v1/sync/batch",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["days_received"] == 3
    assert data["summary"]["records_accepted"] == 3
    assert data["summary"]["records_conflicted"] == 0
    assert "sync_id" in data


@pytest.mark.asyncio
async def test_batch_sync_without_auth(async_client):
    payload = _make_batch(1)
    response = await async_client.post("/api/v1/sync/batch", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_sync_conflict_server_wins(async_client):
    token = await _register_and_token(async_client, "conflict@example.com")
    old_time = BASE_TIME - timedelta(days=1)
    # First sync: newer time
    payload1 = {
        "schema_version": "1.0",
        "device_id": "device-A",
        "days": [{
            "date": "2026-06-28",
            "is_complete": True,
            "updated_at": BASE_TIME.isoformat(),
            "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 5, "updated_at": BASE_TIME.isoformat()}],
        }],
    }
    await async_client.post("/api/v1/sync/batch", json=payload1, headers={"Authorization": f"Bearer {token}"})

    # Second sync: older time → should conflict, server wins
    payload2 = {
        "schema_version": "1.0",
        "device_id": "device-B",
        "days": [{
            "date": "2026-06-28",
            "is_complete": True,
            "updated_at": old_time.isoformat(),
            "values": [{"element_key": "sleep", "value_binary": 0, "value_scale": None, "updated_at": old_time.isoformat()}],
        }],
    }
    response = await async_client.post("/api/v1/sync/batch", json=payload2, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["records_conflicted"] == 1
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["resolution"] == "server_wins"


@pytest.mark.asyncio
async def test_sync_status(async_client):
    token = await _register_and_token(async_client, "status@example.com")
    await async_client.post("/api/v1/sync/batch", json=_make_batch(2), headers={"Authorization": f"Bearer {token}"})
    response = await async_client.get("/api/v1/sync/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_days_synced"] == 2
