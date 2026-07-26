import pytest
from datetime import datetime, timezone

NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)


async def _register_and_token(async_client, email="multiapp@example.com", password="secure123"):
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": password})
    return reg.json()["access_token"]


def _batch(app_id: str, date_str: str, element_key: str = "sleep") -> dict:
    return {
        "schema_version": "1.0",
        "app_id": app_id,
        "days": [{
            "date": date_str,
            "is_complete": True,
            "updated_at": NOW.isoformat(),
            "values": [{"element_key": element_key, "value_binary": 1, "value_scale": 4, "updated_at": NOW.isoformat()}],
        }],
    }


@pytest.mark.asyncio
async def test_default_app_id_is_adhd_tracker_when_omitted(async_client):
    token = await _register_and_token(async_client, "default-app@example.com")
    payload = {
        "schema_version": "1.0",
        "days": [{
            "date": "2026-07-20",
            "is_complete": True,
            "updated_at": NOW.isoformat(),
            "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 4, "updated_at": NOW.isoformat()}],
        }],
    }
    response = await async_client.post(
        "/api/v1/sync/batch", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["summary"]["records_accepted"] == 1

    status = await async_client.get("/api/v1/sync/status", headers={"Authorization": f"Bearer {token}"})
    assert status.json()["app_id"] == "adhd_tracker"
    assert status.json()["total_days_synced"] == 1


@pytest.mark.asyncio
async def test_two_apps_same_date_same_element_key_do_not_collide(async_client):
    token = await _register_and_token(async_client, "same-day@example.com")

    r1 = await async_client.post(
        "/api/v1/sync/batch",
        json=_batch("adhd_tracker", "2026-07-21", "sleep"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert r1.json()["summary"]["records_accepted"] == 1

    r2 = await async_client.post(
        "/api/v1/sync/batch",
        json=_batch("food_diary", "2026-07-21", "sleep"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    # Must be accepted as a brand-new record, NOT treated as a conflict with adhd_tracker's row
    assert r2.json()["summary"]["records_accepted"] == 1
    assert r2.json()["summary"]["records_conflicted"] == 0


@pytest.mark.asyncio
async def test_sync_status_scoped_per_app(async_client):
    token = await _register_and_token(async_client, "scoped-status@example.com")

    await async_client.post(
        "/api/v1/sync/batch", json=_batch("adhd_tracker", "2026-07-22"),
        headers={"Authorization": f"Bearer {token}"},
    )
    await async_client.post(
        "/api/v1/sync/batch", json=_batch("adhd_tracker", "2026-07-23"),
        headers={"Authorization": f"Bearer {token}"},
    )
    await async_client.post(
        "/api/v1/sync/batch", json=_batch("food_diary", "2026-07-22", "protein_breakfast"),
        headers={"Authorization": f"Bearer {token}"},
    )

    adhd_status = await async_client.get(
        "/api/v1/sync/status", params={"app_id": "adhd_tracker"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert adhd_status.json()["total_days_synced"] == 2

    food_status = await async_client.get(
        "/api/v1/sync/status", params={"app_id": "food_diary"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert food_status.json()["total_days_synced"] == 1


@pytest.mark.asyncio
async def test_user_me_total_days_scoped_per_app(async_client):
    token = await _register_and_token(async_client, "scoped-me@example.com")

    await async_client.post(
        "/api/v1/sync/batch", json=_batch("adhd_tracker", "2026-07-24"),
        headers={"Authorization": f"Bearer {token}"},
    )
    await async_client.post(
        "/api/v1/sync/batch", json=_batch("food_diary", "2026-07-24", "protein_breakfast"),
        headers={"Authorization": f"Bearer {token}"},
    )
    await async_client.post(
        "/api/v1/sync/batch", json=_batch("food_diary", "2026-07-25", "protein_breakfast"),
        headers={"Authorization": f"Bearer {token}"},
    )

    me_adhd = await async_client.get(
        "/api/v1/user/me", params={"app_id": "adhd_tracker"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_adhd.json()["total_days"] == 1

    me_food = await async_client.get(
        "/api/v1/user/me", params={"app_id": "food_diary"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_food.json()["total_days"] == 2

    # Same underlying account — email/created_at identical regardless of app_id
    assert me_adhd.json()["email"] == me_food.json()["email"]
