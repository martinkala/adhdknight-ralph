import pytest


@pytest.mark.asyncio
async def test_health_ok(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "timestamp" in data
