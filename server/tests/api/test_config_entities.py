import pytest
import yaml


@pytest.mark.asyncio
async def test_get_entities_version_default_app(async_client):
    response = await async_client.get("/api/v1/config/entities/version")
    assert response.status_code == 200
    data = response.json()
    assert data["app_id"] == "adhd_tracker"
    assert data["version"] == "1.0"


@pytest.mark.asyncio
async def test_get_entities_version_no_auth_required(async_client):
    # Public config endpoint — must work without an Authorization header
    response = await async_client.get("/api/v1/config/entities/version?app_id=adhd_tracker")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_entities_unknown_app_returns_404(async_client):
    response = await async_client.get("/api/v1/config/entities/version?app_id=food_diary")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_entities_invalid_app_id_rejected(async_client):
    response = await async_client.get("/api/v1/config/entities/version?app_id=../../etc/passwd")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_entities_raw_yaml_is_parseable_and_matches_version(async_client):
    response = await async_client.get("/api/v1/config/entities?app_id=adhd_tracker")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-yaml")

    data = yaml.safe_load(response.text)
    assert data["metadata"]["version"] == "1.0"
    assert "nodes" in data
    assert "overall_feeling" in data["nodes"]
