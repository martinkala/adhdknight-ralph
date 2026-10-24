"""food-004: Day API (create / restore, read, day values, delete) and user isolation."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.dependencies import get_now
from app.main import app
from app.models.food import FoodDay, FoodEntry, FoodWeight
from app.services.food_constants import ALL_CATEGORIES

PASSWORD = "secure123"
BASE = "/api/v1/food"
# 2026-10-24T22:30Z is already 2026-10-25 in Europe/Bratislava (CEST, UTC+2).
FAKE_NOW = datetime(2026, 10, 24, 22, 30, tzinfo=timezone.utc)


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


@pytest.mark.asyncio
async def test_create_day_returns_empty_detail(async_client):
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert body["date"] == "2026-10-01"
    assert body["sleep_quality"] is None and body["stool"] is None and body["gas"] is None
    assert set(body["entries"]) == set(ALL_CATEGORIES)
    assert all(v == [] for v in body["entries"].values())
    assert body["weights"] == [] and body["blood_pressures"] == []


@pytest.mark.asyncio
async def test_create_day_without_date_uses_today(async_client, fake_now):
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days", json={}, headers=h)
    assert r.status_code == 201
    assert r.json()["date"] == "2026-10-25"


@pytest.mark.asyncio
async def test_create_day_with_client_id(async_client):
    h = await _register(async_client)
    day_id = str(uuid.uuid4())
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-01", "id": day_id}, headers=h)
    assert r.status_code == 201 and r.json()["id"] == day_id
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-02", "id": day_id}, headers=h)
    assert r.status_code == 409 and r.json() == {"detail": "id_exists"}


@pytest.mark.asyncio
async def test_create_existing_day_conflict(async_client):
    h = await _register(async_client)
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    assert r.status_code == 409
    assert r.json() == {"detail": "day_exists"}


@pytest.mark.asyncio
async def test_create_future_day_rejected(async_client, fake_now):
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-26"}, headers=h)
    assert r.status_code == 422
    assert r.json() == {"detail": "future_date"}
    # Today in Bratislava is allowed even though it is still 2026-10-24 in UTC.
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-25"}, headers=h)
    assert r.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["2026-13-01", "2026-02-30", "26-10-01", "today", "2026-10-1"])
async def test_create_day_invalid_format(async_client, bad):
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days", json={"date": bad}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_missing_day_404(async_client):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/days/2026-10-01", headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_day_values_and_clear(async_client):
    h = await _register(async_client)
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    r = await async_client.patch(f"{BASE}/days/2026-10-01", json={"sleep_quality": 2, "stool": 4, "gas": 6}, headers=h)
    assert r.status_code == 200, r.text
    assert (r.json()["sleep_quality"], r.json()["stool"], r.json()["gas"]) == (2, 4, 6)
    # Only sent fields change; null clears.
    r = await async_client.patch(f"{BASE}/days/2026-10-01", json={"sleep_quality": None}, headers=h)
    assert (r.json()["sleep_quality"], r.json()["stool"], r.json()["gas"]) == (None, 4, 6)
    r = await async_client.get(f"{BASE}/days/2026-10-01", headers=h)
    assert (r.json()["sleep_quality"], r.json()["stool"], r.json()["gas"]) == (None, 4, 6)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"sleep_quality": 0}, {"sleep_quality": 4}, {"stool": 0}, {"stool": 11}, {"gas": 11}, {"unknown": 1},
])
async def test_patch_day_out_of_range(async_client, payload):
    h = await _register(async_client)
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    r = await async_client.patch(f"{BASE}/days/2026-10-01", json=payload, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_missing_day_404(async_client):
    h = await _register(async_client)
    r = await async_client.patch(f"{BASE}/days/2026-10-01", json={"stool": 1}, headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_day_soft_deletes_children(async_client, db_session):
    h = await _register(async_client)
    day = (await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)).json()
    entry = FoodEntry(day_id=day["id"], user_id=await _user_id_of_day(db_session, day["id"]),
                      category="lunch", text="ryza", text_norm="ryza", position=0)
    weight = FoodWeight(day_id=day["id"], user_id=entry.user_id, kg=80)
    db_session.add_all([entry, weight])
    await db_session.commit()

    r = await async_client.delete(f"{BASE}/days/2026-10-01", headers=h)
    assert r.status_code == 204
    assert (await async_client.get(f"{BASE}/days/2026-10-01", headers=h)).status_code == 404
    assert (await async_client.delete(f"{BASE}/days/2026-10-01", headers=h)).status_code == 404
    await db_session.refresh(entry)
    await db_session.refresh(weight)
    assert entry.deleted_at is not None and weight.deleted_at is not None


async def _user_id_of_day(db, day_id: str) -> str:
    return (await db.execute(select(FoodDay.user_id).where(FoodDay.id == day_id))).scalar_one()


@pytest.mark.asyncio
async def test_recreate_deleted_day_restores_it_empty(async_client, db_session):
    h = await _register(async_client)
    day = (await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)).json()
    await async_client.patch(f"{BASE}/days/2026-10-01", json={"sleep_quality": 3, "stool": 2}, headers=h)
    db_session.add(FoodEntry(day_id=day["id"], user_id=await _user_id_of_day(db_session, day["id"]),
                             category="lunch", text="ryza", text_norm="ryza", position=0))
    await db_session.commit()
    await async_client.delete(f"{BASE}/days/2026-10-01", headers=h)

    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == day["id"]
    assert body["sleep_quality"] is None and body["stool"] is None
    assert body["entries"]["lunch"] == []


@pytest.mark.asyncio
async def test_prev_and_next_skip_missing_and_deleted_days(async_client):
    h = await _register(async_client)
    for d in ("2026-10-01", "2026-10-03", "2026-10-05", "2026-10-07"):
        await async_client.post(f"{BASE}/days", json={"date": d}, headers=h)
    await async_client.delete(f"{BASE}/days/2026-10-07", headers=h)
    body = (await async_client.get(f"{BASE}/days/2026-10-03", headers=h)).json()
    assert (body["prev_date"], body["next_date"]) == ("2026-10-01", "2026-10-05")
    body = (await async_client.get(f"{BASE}/days/2026-10-05", headers=h)).json()
    assert (body["prev_date"], body["next_date"]) == ("2026-10-03", None)
    body = (await async_client.get(f"{BASE}/days/2026-10-01", headers=h)).json()
    assert body["prev_date"] is None


@pytest.mark.asyncio
async def test_today_uses_user_timezone(async_client, fake_now):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/today", headers=h)
    assert r.status_code == 200
    assert r.json() == {"schema_version": "1.0", "date": "2026-10-25", "exists": False}
    await async_client.post(f"{BASE}/days", json={}, headers=h)
    assert (await async_client.get(f"{BASE}/today", headers=h)).json()["exists"] is True


@pytest.mark.asyncio
async def test_day_endpoints_require_auth(async_client):
    assert (await async_client.get(f"{BASE}/today")).status_code == 401
    assert (await async_client.post(f"{BASE}/days", json={})).status_code == 401
    assert (await async_client.get(f"{BASE}/days/2026-10-01")).status_code == 401


@pytest.mark.asyncio
async def test_isolation_between_users(async_client):
    a = await _register(async_client)
    b = await _register(async_client)
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=a)
    await async_client.patch(f"{BASE}/days/2026-10-01", json={"stool": 3}, headers=a)

    assert (await async_client.get(f"{BASE}/days/2026-10-01", headers=b)).status_code == 404
    assert (await async_client.patch(f"{BASE}/days/2026-10-01", json={"stool": 9}, headers=b)).status_code == 404
    assert (await async_client.delete(f"{BASE}/days/2026-10-01", headers=b)).status_code == 404
    assert (await async_client.get(f"{BASE}/days/2026-10-01", headers=a)).json()["stool"] == 3

    # B creates the same date independently; A's day stays untouched.
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-01"}, headers=b)
    assert r.status_code == 201 and r.json()["stool"] is None
    await async_client.delete(f"{BASE}/days/2026-10-01", headers=b)
    assert (await async_client.get(f"{BASE}/days/2026-10-01", headers=a)).status_code == 200

    # Navigation never points at the other user's days.
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-05"}, headers=b)
    body = (await async_client.get(f"{BASE}/days/2026-10-01", headers=a)).json()
    assert body["next_date"] is None


@pytest.mark.asyncio
async def test_openapi_contains_day_endpoints(async_client):
    spec = (await async_client.get("/openapi.json")).json()
    for path in ("/api/v1/food/today", "/api/v1/food/days", "/api/v1/food/days/{date}"):
        assert path in spec["paths"]
    assert {"get", "patch", "delete"} <= set(spec["paths"]["/api/v1/food/days/{date}"])
    assert "DayDetail" in spec["components"]["schemas"]
