import pytest

from app.config import get_settings
from app.monitoring.synthetic_checks import check_api_login
import httpx


@pytest.mark.asyncio
async def test_status_requires_operator_key(async_client):
    r = await async_client.get("/internal/monitoring/status")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_status_rejects_wrong_key(async_client):
    r = await async_client.get("/internal/monitoring/status", headers={"x-monitoring-key": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_status_reflects_last_check(async_client, db_session):
    settings = get_settings()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"access_token": "t", "refresh_token": "r", "expires_in": 900})
    )
    await check_api_login(db_session, transport=transport)

    r = await async_client.get(
        "/internal/monitoring/status", headers={"x-monitoring-key": settings.monitoring_api_key}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["last_api_check"]["success"] is True
    assert body["last_api_check"]["consecutive_failures"] == 0
