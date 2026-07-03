import pytest


async def _register_and_token(async_client, email="migrate@example.com", password="secure123"):
    reg = await async_client.post("/api/v1/auth/register", json={"email": email, "password": password})
    return reg.json()["access_token"]


def _make_migrate_payload(n_days: int, strategy: str = "mobile_source_of_truth") -> dict:
    return {
        "schema_version": "1.0",
        "source": "android",
        "migration_strategy": strategy,
        "days": [
            {
                "date": f"2026-06-{i+1:02d}",
                "is_complete": True,
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 4}],
            }
            for i in range(n_days)
        ],
        "weight_config": [
            {"element_key": "sleep", "weight_default": 15.0},
        ],
    }


@pytest.mark.asyncio
async def test_migrate_5_days(async_client):
    token = await _register_and_token(async_client, "mig1@example.com")
    payload = _make_migrate_payload(5)
    response = await async_client.post("/api/v1/migrate", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["days_received"] == 5
    assert data["summary"]["days_imported"] == 5
    assert data["summary"]["days_skipped"] == 0
    assert data["summary"]["weights_imported"] == 1
    assert "migration_id" in data


@pytest.mark.asyncio
async def test_migrate_skip_existing(async_client):
    token = await _register_and_token(async_client, "mig2@example.com")
    # First migration: import 5 days
    await async_client.post("/api/v1/migrate", json=_make_migrate_payload(5, "skip_existing"),
                            headers={"Authorization": f"Bearer {token}"})
    # Second migration: 5 + 2 new days, skip strategy
    payload = _make_migrate_payload(7, "skip_existing")
    response = await async_client.post("/api/v1/migrate", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["days_imported"] == 2  # only the 2 new days
    assert data["summary"]["days_skipped"] == 5


@pytest.mark.asyncio
async def test_migrate_without_auth(async_client):
    response = await async_client.post("/api/v1/migrate", json=_make_migrate_payload(1))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_migrate_invalid_strategy(async_client):
    token = await _register_and_token(async_client, "mig3@example.com")
    payload = _make_migrate_payload(1)
    payload["migration_strategy"] = "not_a_strategy"
    response = await async_client.post("/api/v1/migrate", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_migrate_weight_config(async_client):
    token = await _register_and_token(async_client, "mig4@example.com")
    payload = _make_migrate_payload(1)
    payload["weight_config"] = [
        {"element_key": "sleep", "weight_default": 15.0, "weight_personal": 18.0},
        {"element_key": "overall_feeling", "weight_default": 13.0},
    ]
    response = await async_client.post("/api/v1/migrate", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["summary"]["weights_imported"] == 2
