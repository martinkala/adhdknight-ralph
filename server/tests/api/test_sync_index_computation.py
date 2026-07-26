import pytest
from datetime import datetime, timezone

NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)

_ENTITY_CONFIG = {
    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True, "scale_min": -2, "scale_max": 2},
    "physical_activity": {"weight": 13.0, "impact": 1, "parent": None, "scale": True, "scale_min": 1, "scale_max": 3},
    "overall_feeling": {"weight": 5.0, "impact": 1, "parent": None, "scale": True, "scale_min": -2, "scale_max": 2},
}


async def _register_and_token(async_client, email="index-compute@example.com", password="secure123"):
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": password})
    return reg.json()["access_token"]


def _batch_with_config(date_str: str) -> dict:
    return {
        "schema_version": "1.0",
        "entity_config": _ENTITY_CONFIG,
        "days": [{
            "date": date_str,
            "is_complete": True,
            "updated_at": NOW.isoformat(),
            "values": [
                {"element_key": "sleep", "value_binary": 1, "value_scale": 2, "updated_at": NOW.isoformat()},
                {"element_key": "physical_activity", "value_binary": 1, "value_scale": 3, "updated_at": NOW.isoformat()},
                {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 2, "updated_at": NOW.isoformat()},
            ],
        }],
    }


@pytest.mark.asyncio
async def test_sync_without_entity_config_stores_no_index(async_client):
    token = await _register_and_token(async_client, "no-config@example.com")
    payload = {
        "schema_version": "1.0",
        "days": [{
            "date": "2026-07-20",
            "is_complete": True,
            "updated_at": NOW.isoformat(),
            "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 2, "updated_at": NOW.isoformat()}],
        }],
    }
    response = await async_client.post(
        "/api/v1/sync/batch", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["computed_indices"] == []

    history = await async_client.get("/api/v1/user/history?days=30", headers={"Authorization": f"Bearer {token}"})
    assert history.json()["days"][0]["index_value"] is None


@pytest.mark.asyncio
async def test_sync_with_entity_config_computes_and_persists_index(async_client):
    token = await _register_and_token(async_client, "with-config@example.com")
    response = await async_client.post(
        "/api/v1/sync/batch", json=_batch_with_config("2026-07-21"), headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["computed_indices"]) == 1
    assert body["computed_indices"][0]["date"] == "2026-07-21"
    # All three elements at their scale maximum → 100
    assert body["computed_indices"][0]["index_value"] == pytest.approx(100.0, abs=0.01)

    history = await async_client.get("/api/v1/user/history?days=30", headers={"Authorization": f"Bearer {token}"})
    day = next(d for d in history.json()["days"] if d["date"] == "2026-07-21")
    assert day["index_value"] == pytest.approx(100.0, abs=0.01)
    assert len(day["detail"]) == 3


@pytest.mark.asyncio
async def test_resync_recomputes_index_in_place(async_client):
    token = await _register_and_token(async_client, "resync-config@example.com")
    await async_client.post(
        "/api/v1/sync/batch", json=_batch_with_config("2026-07-22"), headers={"Authorization": f"Bearer {token}"}
    )

    # Second sync: sleep drops to its minimum
    payload = _batch_with_config("2026-07-22")
    later = datetime(2026, 7, 26, 13, 0, 0, tzinfo=timezone.utc)
    payload["days"][0]["values"][0] = {
        "element_key": "sleep", "value_binary": 1, "value_scale": -2, "updated_at": later.isoformat()
    }
    payload["days"][0]["updated_at"] = later.isoformat()

    response = await async_client.post(
        "/api/v1/sync/batch", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    new_index = response.json()["computed_indices"][0]["index_value"]
    assert new_index < 100.0

    history = await async_client.get("/api/v1/user/history?days=30", headers={"Authorization": f"Bearer {token}"})
    days = [d for d in history.json()["days"] if d["date"] == "2026-07-22"]
    # Exactly one DailyIndex row for this day, not duplicated across syncs
    assert len(days) == 1
    assert days[0]["index_value"] == pytest.approx(new_index, abs=0.01)
