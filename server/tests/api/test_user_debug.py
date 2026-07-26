import pytest
from datetime import datetime, timezone

NOW = datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc)

_ENTITY_CONFIG = {
    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True, "scale_min": -2, "scale_max": 2},
}


async def _register_and_token(async_client, email="debug@example.com", password="secure123"):
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": password})
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_debug_distinguishes_days_with_and_without_index(async_client):
    token = await _register_and_token(async_client, "debug1@example.com")

    # Day without entity_config → synced, but no DailyIndex
    await async_client.post(
        "/api/v1/sync/batch",
        json={
            "schema_version": "1.0",
            "days": [{
                "date": "2026-07-25",
                "is_complete": True,
                "updated_at": NOW.isoformat(),
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 2, "updated_at": NOW.isoformat()}],
            }],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Day with entity_config → DailyIndex computed
    await async_client.post(
        "/api/v1/sync/batch",
        json={
            "schema_version": "1.0",
            "entity_config": _ENTITY_CONFIG,
            "days": [{
                "date": "2026-07-26",
                "is_complete": True,
                "updated_at": NOW.isoformat(),
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 2, "updated_at": NOW.isoformat()}],
            }],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await async_client.get("/api/v1/user/debug", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 2
    assert data["days_with_index"] == 1

    by_date = {d["date"]: d for d in data["days"]}
    assert by_date["2026-07-25"]["has_daily_index"] is False
    assert by_date["2026-07-25"]["index_value"] is None
    assert by_date["2026-07-25"]["element_count"] == 1
    assert by_date["2026-07-26"]["has_daily_index"] is True
    assert by_date["2026-07-26"]["index_value"] is not None


@pytest.mark.asyncio
async def test_debug_requires_auth(async_client):
    response = await async_client.get("/api/v1/user/debug")
    assert response.status_code == 401
