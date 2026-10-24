"""food-009: JSON / CSV export and the changes endpoint, user isolation."""
import csv
import io
import json
import uuid
from datetime import datetime, timezone

import pytest

from app.dependencies import get_now
from app.main import app
from app.services.food_constants import ALL_CATEGORIES

PASSWORD = "secure123"
BASE = "/api/v1/food"
FAKE_NOW = datetime(2026, 10, 24, 16, 0, tzinfo=timezone.utc)
CSV_HEADER = ["date", "record_type", "category", "text", "quantity", "unit", "intensity", "value",
              "systolic", "diastolic", "pulse", "measured_at", "note"]


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


async def _post(async_client, h, path: str, body: dict, expected: int = 201) -> dict:
    r = await async_client.post(f"{BASE}{path}", json=body, headers=h)
    assert r.status_code == expected, r.text
    return r.json()


async def _day(async_client, h, date: str, **values) -> None:
    await _post(async_client, h, "/days", {"date": date})
    if values:
        r = await async_client.patch(f"{BASE}/days/{date}", json=values, headers=h)
        assert r.status_code == 200, r.text


async def _entries(async_client, h, date: str, category: str, text: str, **extra) -> list[dict]:
    return (await _post(async_client, h, f"/days/{date}/entries", {"category": category, "text": text, **extra}))[
        "created"]


async def _sample(async_client, h) -> None:
    """2026-10-20 (deleted), 2026-10-22 and 2026-10-23 with data, 2026-10-24 empty."""
    await _day(async_client, h, "2026-10-20", stool=9)
    await _entries(async_client, h, "2026-10-20", "lunch", "zmazany obed")
    await async_client.delete(f"{BASE}/days/2026-10-20", headers=h)

    await _day(async_client, h, "2026-10-22", sleep_quality=3)
    await _entries(async_client, h, "2026-10-22", "dinner", "polievka")

    await _day(async_client, h, "2026-10-23", stool=6, gas=3)
    await _entries(async_client, h, "2026-10-23", "breakfast", "ryza")
    await _entries(async_client, h, "2026-10-23", "afternoon_snack", "2 jablko, .5 l kofoly")
    gone = await _entries(async_client, h, "2026-10-23", "lunch", "zmazane")
    await async_client.delete(f"{BASE}/entries/{gone[0]['id']}", headers=h)
    await _entries(async_client, h, "2026-10-23", "sport", "bike 30 km", intensity=3)
    await _entries(async_client, h, "2026-10-23", "note", 'bolest "hlavy", vecer')
    await _post(async_client, h, "/days/2026-10-23/weights", {"kg": 80.6})
    await _post(async_client, h, "/days/2026-10-23/blood-pressures", {"raw": "125/90 70 7:30"})

    await _day(async_client, h, "2026-10-24")


async def _export(async_client, h, **params):
    r = await async_client.get(f"{BASE}/export", params=params, headers=h)
    assert r.status_code == 200, r.text
    return r


# --- JSON export -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_json_export_range_order_and_no_deleted(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)

    r = await _export(async_client, h, format="json", **{"from": "2026-10-20", "to": "2026-10-23"})
    assert r.headers["content-type"].startswith("application/json")
    assert r.headers["content-disposition"] == 'attachment; filename="food-diary-2026-10-20-2026-10-23.json"'
    body = r.json()
    assert body["schema_version"] == "1.0" and body["app_id"] == "food_diary"
    assert body["exported_at"].startswith("2026-10-24T16:00:00")
    assert [d["date"] for d in body["days"]] == ["2026-10-22", "2026-10-23"]

    day = body["days"][1]
    assert (day["sleep_quality"], day["stool"], day["gas"]) == (None, 6, 3)
    assert day["entries"]["breakfast"] == [{"text": "ryza", "quantity": None, "unit": None, "intensity": None}]
    assert day["entries"]["afternoon_snack"] == [
        {"text": "jablko", "quantity": 2, "unit": None, "intensity": None},
        {"text": "kofoly", "quantity": 0.5, "unit": "l", "intensity": None},
    ]
    assert day["entries"]["lunch"] == []
    assert day["entries"]["sport"] == [{"text": "bike 30 km", "quantity": None, "unit": None, "intensity": 3}]
    assert day["weights"] == [{"kg": 80.6, "measured_at": None, "note": None}]
    assert day["blood_pressures"] == [
        {"systolic": 125, "diastolic": 90, "pulse": 70, "measured_at": "07:30", "note": None}
    ]
    assert '"id"' not in json.dumps(body)  # no internal IDs

    # Without a range: everything, file name from the first and last exported day.
    r = await _export(async_client, h)
    assert [d["date"] for d in r.json()["days"]] == ["2026-10-22", "2026-10-23", "2026-10-24"]
    assert 'filename="food-diary-2026-10-22-2026-10-24.json"' in r.headers["content-disposition"]
    r = await _export(async_client, h, **{"from": "2026-10-23"})
    assert [d["date"] for d in r.json()["days"]] == ["2026-10-23", "2026-10-24"]


@pytest.mark.asyncio
async def test_json_export_all_categories_and_numbers(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)
    body = (await _export(async_client, h)).json()
    for day in body["days"]:
        assert list(day["entries"]) == list(ALL_CATEGORIES)
    day = body["days"][1]
    assert isinstance(day["stool"], int) and isinstance(day["weights"][0]["kg"], float)
    assert isinstance(day["entries"]["afternoon_snack"][0]["quantity"], (int, float))
    assert isinstance(day["blood_pressures"][0]["systolic"], int)
    assert body["days"][2]["entries"] == {category: [] for category in ALL_CATEGORIES}


@pytest.mark.asyncio
async def test_export_validates_range(async_client, fake_now):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/export", params={"from": "2026-10-24", "to": "2026-10-01"}, headers=h)
    assert r.status_code == 422 and r.json()["detail"] == "invalid_range"
    r = await async_client.get(f"{BASE}/export", params={"from": "2026-02-30"}, headers=h)
    assert r.status_code == 422
    r = await async_client.get(f"{BASE}/export", params={"format": "xml"}, headers=h)
    assert r.status_code == 422
    r = await async_client.get(f"{BASE}/export")
    assert r.status_code == 401
    # Empty account: empty days, file name falls back to today.
    r = await _export(async_client, h)
    assert r.json()["days"] == []
    assert 'filename="food-diary-2026-10-24-2026-10-24.json"' in r.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_isolation(async_client, fake_now):
    a = await _register(async_client)
    b = await _register(async_client)
    await _sample(async_client, a)
    await _day(async_client, b, "2026-10-23", stool=1)
    await _entries(async_client, b, "2026-10-23", "breakfast", "tajne jedlo B")

    body = (await _export(async_client, a)).json()
    assert "tajne jedlo B" not in json.dumps(body)
    assert body["days"][1]["stool"] == 6
    text = (await _export(async_client, a, format="csv")).text
    assert "tajne jedlo B" not in text

    body = (await _export(async_client, b)).json()
    assert [d["date"] for d in body["days"]] == ["2026-10-23"]
    assert "ryza" not in json.dumps(body)


# --- CSV export ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_csv_export_format(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)
    r = await _export(async_client, h, format="csv", **{"from": "2026-10-23", "to": "2026-10-23"})
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"] == 'attachment; filename="food-diary-2026-10-23-2026-10-23.csv"'
    raw = r.content
    assert raw.startswith("﻿".encode("utf-8"))

    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    assert reader.fieldnames == CSV_HEADER
    rows = list(reader)
    by_type = {}
    for row in rows:
        by_type.setdefault(row["record_type"], []).append(row)
    assert [(r["category"], r["value"]) for r in by_type["day_value"]] == [("stool", "6"), ("gas", "3")]
    entry = {r["text"]: r for r in by_type["entry"]}
    assert (entry["kofoly"]["quantity"], entry["kofoly"]["unit"]) == ("0.5", "l")
    assert (entry["jablko"]["quantity"], entry["jablko"]["unit"]) == ("2", "")
    assert entry["bike 30 km"]["intensity"] == "3"
    assert entry["ryza"]["quantity"] == "" and entry["ryza"]["value"] == ""
    assert by_type["weight"][0]["value"] == "80.6"
    bp = by_type["blood_pressure"][0]
    assert (bp["systolic"], bp["diastolic"], bp["pulse"], bp["measured_at"]) == ("125", "90", "70", "07:30")


@pytest.mark.asyncio
async def test_csv_escapes_commas_and_quotes(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)
    text = (await _export(async_client, h, format="csv")).content.decode("utf-8-sig")
    assert '"bolest ""hlavy"", vecer"' in text
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    notes = [r["text"] for r in rows if r["category"] == "note"]
    assert notes == ['bolest "hlavy", vecer']


@pytest.mark.asyncio
async def test_csv_row_count(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)
    body = (await _export(async_client, h)).json()
    expected = sum(
        sum(len(items) for items in day["entries"].values()) + len(day["weights"]) + len(day["blood_pressures"])
        + sum(day[field] is not None for field in ("sleep_quality", "stool", "gas"))
        for day in body["days"]
    )
    # 2026-10-22: sleep + polievka; 2026-10-23: stool, gas, 5 entries, weight, pressure.
    assert expected == 2 + 9
    text = (await _export(async_client, h, format="csv")).content.decode("utf-8-sig")
    assert len(list(csv.DictReader(io.StringIO(text, newline="")))) == expected


# --- Changes ---------------------------------------------------------------------------------


async def _changes(async_client, h, **params) -> dict:
    r = await async_client.get(f"{BASE}/changes", params=params, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _ids(changes: dict, kind: str) -> set[str]:
    return {item["id"] for item in changes[kind]}


@pytest.mark.asyncio
async def test_changes_returns_created_updated_and_deleted_entry(async_client, fake_now):
    h = await _register(async_client)
    t0 = (await _changes(async_client, h))["server_time"]
    await _day(async_client, h, "2026-10-23")
    entry = (await _entries(async_client, h, "2026-10-23", "breakfast", "toasty"))[0]
    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"quantity": 2}, headers=h)
    assert r.status_code == 200
    r = await async_client.delete(f"{BASE}/entries/{entry['id']}", headers=h)
    assert r.status_code == 204

    body = await _changes(async_client, h, since=t0)
    assert body["schema_version"] == "1.0" and body["has_more"] is False
    [change] = body["entries"]
    assert change["id"] == entry["id"] and change["quantity"] == 2
    assert change["deleted_at"] is not None and change["updated_at"] >= change["deleted_at"]
    assert change["day_id"] == body["days"][0]["id"] and body["days"][0]["date"] == "2026-10-23"
    # The deleted entry is not in a normal read.
    day = (await async_client.get(f"{BASE}/days/2026-10-23", headers=h)).json()
    assert day["entries"]["breakfast"] == []


@pytest.mark.asyncio
async def test_changes_since_server_time_is_empty(async_client, fake_now):
    h = await _register(async_client)
    await _sample(async_client, h)
    first = await _changes(async_client, h)
    assert first["has_more"] is False and len(first["entries"]) == 8 and len(first["days"]) == 4
    body = await _changes(async_client, h, since=first["server_time"])
    assert all(body[kind] == [] for kind in ("days", "entries", "weights", "blood_pressures", "med_dictionary"))
    assert body["has_more"] is False


@pytest.mark.asyncio
async def test_every_change_updates_updated_at(async_client, fake_now):
    h = await _register(async_client)
    await _day(async_client, h, "2026-10-23")
    entry = (await _entries(async_client, h, "2026-10-23", "lunch", "ryza"))[0]
    weight = await _post(async_client, h, "/days/2026-10-23/weights", {"kg": 80})
    bp = await _post(async_client, h, "/days/2026-10-23/blood-pressures", {"raw": "120/80"})
    await _post(async_client, h, "/days/2026-10-23/meds", {"text": "zn", "classify": {"zn": "supplement"}})

    async def changed(action) -> dict:
        since = (await _changes(async_client, h))["server_time"]
        r = await action()
        assert r.status_code in (200, 201, 204), r.text
        return await _changes(async_client, h, since=since)

    body = await changed(lambda: async_client.patch(f"{BASE}/days/2026-10-23", json={"gas": 2}, headers=h))
    assert body["days"][0]["gas"] == 2
    body = await changed(lambda: async_client.patch(f"{BASE}/weights/{weight['id']}", json={"kg": 79.5}, headers=h))
    assert _ids(body, "weights") == {weight["id"]}
    body = await changed(lambda: async_client.delete(f"{BASE}/weights/{weight['id']}", headers=h))
    assert body["weights"][0]["deleted_at"] is not None
    body = await changed(
        lambda: async_client.patch(f"{BASE}/blood-pressures/{bp['id']}", json={"pulse": 70}, headers=h))
    assert body["blood_pressures"][0]["pulse"] == 70
    body = await changed(lambda: async_client.put(f"{BASE}/med-dictionary/zn", json={"kind": "medication"},
                                                  headers=h))
    assert body["med_dictionary"][0]["kind"] == "medication"
    assert [e["category"] for e in body["entries"]] == ["medication"]  # moved entry changed too
    body = await changed(lambda: async_client.delete(f"{BASE}/med-dictionary/zn", headers=h))
    assert body["med_dictionary"][0]["deleted_at"] is not None
    body = await changed(lambda: async_client.patch(f"{BASE}/entries/{entry['id']}", json={"text": "cestoviny"},
                                                    headers=h))
    assert body["entries"][0]["text"] == "cestoviny"

    # Deleting the day is a tombstone for the day and all its alive children.
    body = await changed(lambda: async_client.delete(f"{BASE}/days/2026-10-23", headers=h))
    assert body["days"][0]["deleted_at"] is not None
    assert {e["id"] for e in body["entries"]} >= {entry["id"]}
    assert all(e["deleted_at"] for e in body["entries"])
    assert _ids(body, "blood_pressures") == {bp["id"]}
    assert body["weights"] == []  # already deleted before

    # Restoring the day is a change as well.
    body = await changed(lambda: async_client.post(f"{BASE}/days", json={"date": "2026-10-23"}, headers=h))
    assert body["days"][0]["deleted_at"] is None


@pytest.mark.asyncio
async def test_changes_pagination(async_client, fake_now):
    h = await _register(async_client)
    await _day(async_client, h, "2026-10-23")
    for i in range(7):
        await _entries(async_client, h, "2026-10-23", "lunch", f"jedlo {i}")

    seen: list[str] = []
    since = None
    for _ in range(10):
        params = {"limit": 3} | ({"since": since} if since else {})
        body = await _changes(async_client, h, **params)
        items = body["days"] + body["entries"]
        assert len(items) <= 3
        seen += [item["id"] for item in items]
        since = body["server_time"]
        if not body["has_more"]:
            break
    assert len(seen) == len(set(seen)) == 8


@pytest.mark.asyncio
async def test_changes_page_keeps_group_with_same_timestamp(async_client, fake_now):
    h = await _register(async_client)
    await _day(async_client, h, "2026-10-23")
    await _entries(async_client, h, "2026-10-23", "lunch", "a, b, c, d")
    since = (await _changes(async_client, h))["server_time"]
    await async_client.delete(f"{BASE}/days/2026-10-23", headers=h)  # 5 rows, one timestamp

    body = await _changes(async_client, h, since=since, limit=2)
    assert len(body["days"]) == 1 and len(body["entries"]) == 4 and body["has_more"] is True
    body = await _changes(async_client, h, since=body["server_time"], limit=2)
    assert body["days"] == [] and body["entries"] == [] and body["has_more"] is False


@pytest.mark.asyncio
async def test_changes_isolation(async_client, fake_now):
    a = await _register(async_client)
    b = await _register(async_client)
    await _sample(async_client, a)
    await _post(async_client, a, "/days/2026-10-23/meds", {"text": "zn", "classify": {"zn": "supplement"}})
    body = await _changes(async_client, b)
    assert all(body[kind] == [] for kind in ("days", "entries", "weights", "blood_pressures", "med_dictionary"))
    await _day(async_client, b, "2026-10-23")
    body = await _changes(async_client, b)
    assert len(body["days"]) == 1 and body["entries"] == []
    a_body = await _changes(async_client, a)
    assert body["days"][0]["id"] not in _ids(a_body, "days")


@pytest.mark.asyncio
async def test_openapi_has_export_schemas(async_client):
    spec = (await async_client.get("/openapi.json")).json()
    assert "/api/v1/food/export" in spec["paths"] and "/api/v1/food/changes" in spec["paths"]
    assert "FoodExport" in spec["components"]["schemas"]
    assert "FoodChanges" in spec["components"]["schemas"]
