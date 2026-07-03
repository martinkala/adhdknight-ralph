import pytest

DAILY_PAYLOAD = {
    "schema_version": "1.0",
    "date": "2026-06-30",
    "entity_config": {
        "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
        "overall_feeling": {"weight": 13.0, "impact": 1, "parent": None, "scale": True},
    },
    "values": [
        {"element_key": "sleep", "value_binary": 1, "value_scale": 4},
        {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5},
    ],
    "active_keys": ["sleep", "overall_feeling"],
}


@pytest.mark.asyncio
async def test_compute_daily_returns_correct_index(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=DAILY_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["index_value"] is not None
    assert abs(data["index_value"] - 86.61) < 0.02


@pytest.mark.asyncio
async def test_compute_daily_empty_values_returns_null_index(async_client):
    payload = {**DAILY_PAYLOAD, "values": [], "active_keys": []}
    response = await async_client.post("/api/v1/compute/daily", json=payload)
    assert response.status_code == 200
    assert response.json()["index_value"] is None


@pytest.mark.asyncio
async def test_compute_range_three_days(async_client):
    payload = {
        "schema_version": "1.0",
        "entity_config": {
            "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
        },
        "days": [
            {
                "date": "2026-06-28",
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 5}],
                "active_keys": ["sleep"],
            },
            {"date": "2026-06-29", "values": [], "active_keys": ["sleep"]},
            {
                "date": "2026-06-30",
                "values": [{"element_key": "sleep", "value_binary": 1, "value_scale": 3}],
                "active_keys": ["sleep"],
            },
        ],
    }
    response = await async_client.post("/api/v1/compute/range", json=payload)
    assert response.status_code == 200
    data = response.json()
    results = data["results"]
    assert len(results) == 3
    assert results[1]["status"] == "no_data"
    assert results[1]["index_value"] is None
    assert results[0]["index_value"] == 100.0
    assert data["summary"]["days_no_data"] == 1


@pytest.mark.asyncio
async def test_schema_version_in_response(async_client):
    response = await async_client.post("/api/v1/compute/daily", json=DAILY_PAYLOAD)
    assert response.json()["schema_version"] == "1.0"


@pytest.mark.asyncio
async def test_android_integration_endpoint(async_client):
    response = await async_client.get("/api/v1/compute/android-integration")
    assert response.status_code == 200
    data = response.json()
    assert "recommended_strategy" in data
    assert "computation_points" in data
