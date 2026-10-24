"""food-008: calendar and days list API, user isolation."""
import uuid
from datetime import datetime, timezone

import pytest

from app.dependencies import get_now
from app.main import app
from app.services.food_overview import severity

PASSWORD = "secure123"
BASE = "/api/v1/food"
# 2026-10-24T05:30Z is 07:30 on 2026-10-24 in Europe/Bratislava.
FAKE_NOW = datetime(2026, 10, 24, 5, 30, tzinfo=timezone.utc)


@pytest.fixture
def fake_now():
    app.dependency_overrides[get_now] = lambda: FAKE_NOW
    yield FAKE_NOW
    app.dependency_overrides.pop(get_now, None)


async def _register(async_client) -> dict:
    email = f"food-{uuid.uuid4().hex[:10]}@example.com"
    r = await async_client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _day(async_client, h, date: str, **values) -> None:
    r = await async_client.post(f"{BASE}/days", json={"date": date}, headers=h)
    assert r.status_code == 201, r.text
    if values:
        r = await async_client.patch(f"{BASE}/days/{date}", json=values, headers=h)
        assert r.status_code == 200, r.text


async def _entries(async_client, h, date: str, category: str, text: str) -> None:
    r = await async_client.post(f"{BASE}/days/{date}/entries", json={"category": category, "text": text}, headers=h)
    assert r.status_code == 201, r.text


def test_severity_bands():
    assert severity(None, None) == "none"
    assert severity(2, 3) == "ok"
    assert severity(4, 1) == "mid"
    assert severity(None, 6) == "mid"
    assert severity(2, 9) == "bad"
    assert severity(7, None) == "bad"


@pytest.mark.asyncio
async def test_calendar_returns_only_days_of_month(async_client, fake_now):
    h = await _register(async_client)
    await _day(async_client, h, "2026-09-30")
    await _day(async_client, h, "2026-10-01", stool=2, gas=3)
    await _day(async_client, h, "2026-10-15", stool=4, gas=1)
    await _day(async_client, h, "2026-10-20")
    await _day(async_client, h, "2026-10-24")
    await _entries(async_client, h, "2026-10-15", "breakfast", "toasty, kafe")
    await _entries(async_client, h, "2026-10-15", "note", "bolesť hlavy")
    await async_client.delete(f"{BASE}/days/2026-10-20", headers=h)

    r = await async_client.get(f"{BASE}/calendar", params={"month": "2026-10"}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert body["month"] == "2026-10" and body["today"] == "2026-10-24"
    assert body["days"] == [
        {"date": "2026-10-01", "stool": 2, "gas": 3, "severity": "ok", "entry_count": 0},
        {"date": "2026-10-15", "stool": 4, "gas": 1, "severity": "mid", "entry_count": 3},
        {"date": "2026-10-24", "stool": None, "gas": None, "severity": "none", "entry_count": 0},
    ]

    r = await async_client.get(f"{BASE}/calendar", params={"month": "2026-09"}, headers=h)
    assert [d["date"] for d in r.json()["days"]] == ["2026-09-30"]


@pytest.mark.asyncio
async def test_calendar_defaults_to_current_month(async_client, fake_now):
    h = await _register(async_client)
    await _day(async_client, h, "2026-10-02")
    r = await async_client.get(f"{BASE}/calendar", headers=h)
    assert r.status_code == 200
    assert r.json()["month"] == "2026-10"
    assert [d["date"] for d in r.json()["days"]] == ["2026-10-02"]


@pytest.mark.asyncio
@pytest.mark.parametrize("month", ["2026-13", "2026-1", "2026-00", "abc", "2026-10-01"])
async def test_calendar_invalid_month(async_client, month):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/calendar", params={"month": month}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_days_list_summary(async_client):
    h = await _register(async_client)
    await _day(async_client, h, "2026-10-10", stool=4, gas=6, sleep_quality=2)
    await _entries(async_client, h, "2026-10-10", "dinner", "ryža")
    await _entries(async_client, h, "2026-10-10", "medication", "prestarium")
    await _entries(async_client, h, "2026-10-10", "breakfast", "2 toasty, kafe")
    await _entries(async_client, h, "2026-10-10", "unassigned", "a, b, c, d, e, f")
    r = await async_client.post(f"{BASE}/days/2026-10-10/weights", json={"kg": 80.6}, headers=h)
    assert r.status_code == 201
    r = await async_client.post(f"{BASE}/days/2026-10-10/blood-pressures", json={"raw": "130/85 72 7:30"}, headers=h)
    assert r.status_code == 201
    await async_client.post(f"{BASE}/days/2026-10-10/blood-pressures", json={"raw": "120/80 6:00"}, headers=h)

    r = await async_client.get(f"{BASE}/days", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert (body["page"], body["page_size"], body["total"]) == (1, 30, 1)
    day = body["days"][0]
    assert day["date"] == "2026-10-10"
    assert (day["stool"], day["gas"], day["severity"], day["sleep_quality"]) == (4, 6, "mid", 2)
    assert day["weights"] == [80.6]
    assert day["bp"] == ["120/80", "130/85 72"]
    # Section order, first 8 food texts, no medication.
    assert day["food_preview"] == ["toasty", "kafe", "ryža", "a", "b", "c", "d", "e"]
    assert day["entry_count"] == 10


@pytest.mark.asyncio
async def test_days_list_pagination(async_client):
    h = await _register(async_client)
    dates = [f"2026-09-{n:02d}" for n in range(1, 6)]
    for date in dates:
        await _day(async_client, h, date)
    await _day(async_client, h, "2026-09-06")
    await async_client.delete(f"{BASE}/days/2026-09-06", headers=h)

    r = await async_client.get(f"{BASE}/days", params={"page": 1, "page_size": 2}, headers=h)
    body = r.json()
    assert body["total"] == 5
    assert [d["date"] for d in body["days"]] == ["2026-09-05", "2026-09-04"]
    r = await async_client.get(f"{BASE}/days", params={"page": 3, "page_size": 2}, headers=h)
    assert [d["date"] for d in r.json()["days"]] == ["2026-09-01"]
    r = await async_client.get(f"{BASE}/days", params={"page": 4, "page_size": 2}, headers=h)
    assert r.json()["days"] == [] and r.json()["total"] == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
async def test_days_list_invalid_paging(async_client, params):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/days", params=params, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_overview_isolation(async_client):
    a = await _register(async_client)
    b = await _register(async_client)
    await _day(async_client, a, "2026-08-10", stool=9)
    await _entries(async_client, a, "2026-08-10", "lunch", "tajné jedlo")
    await _day(async_client, b, "2026-08-11")

    r = await async_client.get(f"{BASE}/calendar", params={"month": "2026-08"}, headers=b)
    assert [d["date"] for d in r.json()["days"]] == ["2026-08-11"]
    r = await async_client.get(f"{BASE}/days", headers=b)
    body = r.json()
    assert body["total"] == 1
    assert [d["date"] for d in body["days"]] == ["2026-08-11"]
    assert "tajné jedlo" not in r.text


@pytest.mark.asyncio
async def test_overview_requires_auth(async_client):
    assert (await async_client.get(f"{BASE}/calendar")).status_code in (401, 403)
    assert (await async_client.get(f"{BASE}/days")).status_code in (401, 403)
