import pytest
from datetime import date, timedelta, datetime, timezone

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
FAR_FUTURE = "2099-01-01"

NOW = datetime.now(timezone.utc)

_BASE_ENTITY_CONFIG = {
    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
    "overall_feeling": {"weight": 13.0, "impact": 1, "parent": None, "scale": True},
}

_BASE_VALUES = [
    {"element_key": "sleep", "value_binary": 1, "value_scale": 3},
    {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 3},
]


def _daily_payload(date_str: str) -> dict:
    return {
        "schema_version": "1.0",
        "date": date_str,
        "entity_config": _BASE_ENTITY_CONFIG,
        "values": _BASE_VALUES,
        "active_keys": ["sleep", "overall_feeling"],
    }


async def _register_and_token(async_client, email: str) -> str:
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": "secure123"})
    return reg.json()["access_token"]


def _sync_payload(date_str: str) -> dict:
    return {
        "schema_version": "1.0",
        "device_id": "test-device",
        "days": [{
            "date": date_str,
            "is_complete": True,
            "updated_at": NOW.isoformat(),
            "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 3, "updated_at": NOW.isoformat()}],
        }],
    }


@pytest.mark.asyncio
async def test_compute_daily_today_returns_200(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=_daily_payload(TODAY))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_compute_daily_yesterday_returns_200(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=_daily_payload(YESTERDAY))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_compute_daily_tomorrow_returns_422(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=_daily_payload(TOMORROW))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_compute_daily_far_future_returns_422(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=_daily_payload(FAR_FUTURE))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sync_batch_tomorrow_returns_422(async_client):
    token = await _register_and_token(async_client, "futuredate1@example.com")
    response = await async_client.post(
        "/api/v1/sync/batch",
        json=_sync_payload(TOMORROW),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sync_batch_today_returns_200(async_client):
    token = await _register_and_token(async_client, "futuredate2@example.com")
    response = await async_client.post(
        "/api/v1/sync/batch",
        json=_sync_payload(TODAY),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
