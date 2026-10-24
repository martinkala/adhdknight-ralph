"""food-005: entries API (add with splitting / quantities / merging, update, delete, quantities),
measurements API (weights, blood pressures) and user isolation."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.dependencies import get_now
from app.main import app
from app.models.food import FoodEntry

PASSWORD = "secure123"
BASE = "/api/v1/food"
DAY = "2026-10-01"
# 2026-10-24T05:30Z is 07:30 in Europe/Bratislava (CEST, UTC+2).
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


async def _user_with_day(async_client, date: str = DAY) -> dict:
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days", json={"date": date}, headers=h)
    assert r.status_code == 201, r.text
    return h


async def _add(async_client, h, category, text, date=DAY, **extra):
    return await async_client.post(f"{BASE}/days/{date}/entries", json={"category": category, "text": text, **extra},
                                   headers=h)


async def _entries(async_client, h, category, date=DAY):
    r = await async_client.get(f"{BASE}/days/{date}", headers=h)
    return r.json()["entries"][category]


def _short(entries):
    return [(e["text"], e["quantity"], e["unit"]) for e in entries]


# --- Entries ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_splits_and_parses_quantity(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "breakfast", "2 toasty, kafe")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert _short(body["created"]) == [("toasty", 2, None), ("kafe", None, None)]
    assert [e["position"] for e in body["created"]] == [0, 1]
    assert _short(await _entries(async_client, h, "breakfast")) == [("toasty", 2, None), ("kafe", None, None)]


@pytest.mark.asyncio
async def test_new_entries_go_to_end_of_section(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "lunch", "polievka, ryza")
    await _add(async_client, h, "dinner", "chlieb")
    r = await _add(async_client, h, "lunch", "200g kuracie")
    assert _short(r.json()["created"]) == [("kuracie", 200, "g")]
    entries = await _entries(async_client, h, "lunch")
    assert [e["text"] for e in entries] == ["polievka", "ryza", "kuracie"]
    assert [e["position"] for e in entries] == [0, 1, 2]


@pytest.mark.asyncio
async def test_add_merges_duplicates(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "medication", "emanera , prestarium, emanera")
    assert r.status_code == 201
    assert _short(r.json()["created"]) == [("emanera", 2, None), ("prestarium", None, None)]


@pytest.mark.asyncio
async def test_note_is_not_split(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "note", "rano prujem, unava")
    assert r.status_code == 201
    assert _short(r.json()["created"]) == [("rano prujem, unava", None, None)]
    r = await _add(async_client, h, "note", "  2 lines \n\n second  line ")
    assert r.json()["created"][0]["text"] == "2 lines\nsecond line"


@pytest.mark.asyncio
async def test_explicit_quantity_is_not_parsed(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "afternoon_snack", "2 toasty", quantity=0.5, unit="l")
    assert _short(r.json()["created"]) == [("2 toasty", 0.5, "l")]
    r = await _add(async_client, h, "afternoon_snack", "jablko", quantity=3, unit="ks")
    assert _short(r.json()["created"]) == [("jablko", 3, None)]


@pytest.mark.asyncio
async def test_intensity_only_for_sport(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "lunch", "ryza", intensity=3)
    assert r.status_code == 422 and r.json() == {"detail": "intensity_not_allowed"}
    for value in (1, 5):
        r = await _add(async_client, h, "sport", "eBike 60 km", intensity=value)
        assert r.status_code == 201 and r.json()["created"][0]["intensity"] == value
    for value in (0, 6):
        r = await _add(async_client, h, "sport", "beh", intensity=value)
        assert r.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("payload, detail", [
    ({"category": "brunch", "text": "x"}, "unknown_category"),
    ({"category": "lunch", "text": " , ,"}, "empty_text"),
    ({"category": "note", "text": "   "}, "empty_text"),
    ({"category": "lunch", "text": "x" * 201}, "text_too_long"),
    ({"category": "lunch", "text": "x", "quantity": 1, "unit": "cup"}, "invalid_unit"),
    ({"category": "lunch", "text": "x", "unit": "g"}, "unit_without_quantity"),
    ({"category": "lunch", "text": "a, b", "id": str(uuid.uuid4())}, "id_requires_single_entry"),
])
async def test_add_validation(async_client, payload, detail):
    h = await _user_with_day(async_client)
    r = await async_client.post(f"{BASE}/days/{DAY}/entries", json=payload, headers=h)
    assert r.status_code == 422
    assert r.json() == {"detail": detail}


@pytest.mark.asyncio
async def test_add_with_client_id(async_client):
    h = await _user_with_day(async_client)
    entry_id = str(uuid.uuid4())
    r = await _add(async_client, h, "lunch", "ryza", id=entry_id)
    assert r.status_code == 201 and r.json()["created"][0]["id"] == entry_id
    r = await _add(async_client, h, "lunch", "ryza", id=entry_id)
    assert r.status_code == 409 and r.json() == {"detail": "id_exists"}


@pytest.mark.asyncio
async def test_add_to_missing_or_deleted_day(async_client):
    h = await _user_with_day(async_client)
    r = await _add(async_client, h, "lunch", "ryza", date="2026-09-01")
    assert r.status_code == 404
    await async_client.delete(f"{BASE}/days/{DAY}", headers=h)
    r = await _add(async_client, h, "lunch", "ryza")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_text_recomputes_text_norm(async_client, db_session):
    h = await _user_with_day(async_client)
    entry = (await _add(async_client, h, "lunch", "2 rizoto")).json()["created"][0]
    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"text": "  Šošovica,  3 kúsky "}, headers=h)
    assert r.status_code == 200, r.text
    # No splitting and no quantity parsing when editing.
    assert r.json()["text"] == "Šošovica, 3 kúsky"
    assert r.json()["quantity"] == 2
    row = (await db_session.execute(select(FoodEntry).where(FoodEntry.id == entry["id"]))).scalar_one()
    await db_session.refresh(row)
    assert row.text_norm == "sosovica, 3 kusky"


@pytest.mark.asyncio
async def test_patch_quantity_and_unit(async_client):
    h = await _user_with_day(async_client)
    entry = (await _add(async_client, h, "lunch", "kofola")).json()["created"][0]
    url = f"{BASE}/entries/{entry['id']}"
    r = await async_client.patch(url, json={"quantity": 0.5, "unit": "l"}, headers=h)
    assert (r.json()["quantity"], r.json()["unit"]) == (0.5, "l")
    r = await async_client.patch(url, json={"unit": "ml"}, headers=h)
    assert (r.json()["quantity"], r.json()["unit"]) == (0.5, "ml")
    r = await async_client.patch(url, json={"quantity": None}, headers=h)
    assert (r.json()["quantity"], r.json()["unit"]) == (None, None)
    r = await async_client.patch(url, json={"unit": "g"}, headers=h)
    assert r.status_code == 422 and r.json() == {"detail": "unit_without_quantity"}
    r = await async_client.patch(url, json={"text": "  "}, headers=h)
    assert r.status_code == 422 and r.json() == {"detail": "empty_text"}


@pytest.mark.asyncio
async def test_patch_moves_category_to_end(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "dinner", "chlieb, maslo")
    entry = (await _add(async_client, h, "lunch", "ryza")).json()["created"][0]
    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"category": "dinner"}, headers=h)
    assert r.status_code == 200
    assert r.json()["category"] == "dinner" and r.json()["position"] == 2
    assert await _entries(async_client, h, "lunch") == []
    assert [e["text"] for e in await _entries(async_client, h, "dinner")] == ["chlieb", "maslo", "ryza"]
    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"category": "brunch"}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_intensity(async_client):
    h = await _user_with_day(async_client)
    sport = (await _add(async_client, h, "sport", "beh", intensity=2)).json()["created"][0]
    r = await async_client.patch(f"{BASE}/entries/{sport['id']}", json={"intensity": 4}, headers=h)
    assert r.json()["intensity"] == 4
    r = await async_client.patch(f"{BASE}/entries/{sport['id']}", json={"intensity": None}, headers=h)
    assert r.json()["intensity"] is None
    lunch = (await _add(async_client, h, "lunch", "ryza")).json()["created"][0]
    r = await async_client.patch(f"{BASE}/entries/{lunch['id']}", json={"intensity": 3}, headers=h)
    assert r.status_code == 422 and r.json() == {"detail": "intensity_not_allowed"}


@pytest.mark.asyncio
async def test_delete_entry_is_soft(async_client):
    h = await _user_with_day(async_client)
    entry = (await _add(async_client, h, "lunch", "ryza")).json()["created"][0]
    r = await async_client.delete(f"{BASE}/entries/{entry['id']}", headers=h)
    assert r.status_code == 204
    assert await _entries(async_client, h, "lunch") == []
    r = await async_client.delete(f"{BASE}/entries/{entry['id']}", headers=h)
    assert r.status_code == 404
    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"text": "x"}, headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_quantities_sorted_by_count_without_deleted(async_client):
    h = await _register(async_client)
    for i, text in enumerate(["2 toasty", "2 Toasty", "3 toasty", "2 toasty", "toasty", "100 g toasty"]):
        date = f"2026-09-{i + 1:02d}"
        await async_client.post(f"{BASE}/days", json={"date": date}, headers=h)
        await _add(async_client, h, "breakfast" if i % 2 else "dinner", text, date=date)
    # Deleted entries do not count: 4 x "100 g" of which 3 are deleted.
    await async_client.post(f"{BASE}/days", json={"date": "2026-09-20"}, headers=h)
    for _ in range(3):
        entry = (await _add(async_client, h, "lunch", "100 g toasty", date="2026-09-20")).json()["created"][0]
        await async_client.delete(f"{BASE}/entries/{entry['id']}", headers=h)
    # Other groups do not count.
    await _add(async_client, h, "medication", "5 toasty", date="2026-09-20")

    r = await async_client.get(f"{BASE}/quantities", params={"text": "TOASTY ", "category": "lunch"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert body["options"] == [
        {"quantity": 2, "unit": None, "count": 3},
        # Same count: the more recently used first.
        {"quantity": 100, "unit": "g", "count": 1},
        {"quantity": 3, "unit": None, "count": 1},
    ]
    r = await async_client.get(f"{BASE}/quantities", params={"text": "toasty", "category": "supplement"}, headers=h)
    assert r.json()["options"] == [{"quantity": 5, "unit": None, "count": 1}]
    r = await async_client.get(f"{BASE}/quantities", params={"text": "toasty", "category": "note"}, headers=h)
    assert r.json()["options"] == []
    r = await async_client.get(f"{BASE}/quantities", params={"text": "toasty", "category": "x"}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_quantities_limited_to_five(async_client):
    h = await _user_with_day(async_client)
    for n in range(1, 8):
        await _add(async_client, h, "lunch", f"{n} knedle")
    r = await async_client.get(f"{BASE}/quantities", params={"text": "knedle", "category": "lunch"}, headers=h)
    assert len(r.json()["options"]) == 5


# --- Measurements ----------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("raw, expected", [
    ("130/85", (130, 85, None, None)),
    ("130/85 72", (130, 85, 72, None)),
    ("130/85 72 7:30", (130, 85, 72, "07:30")),
    ("130 / 85  72  07:30", (130, 85, 72, "07:30")),
    ("130/85 7:30", (130, 85, None, "07:30")),
])
async def test_blood_pressure_raw_formats(async_client, raw, expected):
    h = await _user_with_day(async_client)
    r = await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json={"raw": raw, "note": " po kave "},
                                headers=h)
    assert r.status_code == 201, r.text
    bp = r.json()
    assert (bp["systolic"], bp["diastolic"], bp["pulse"], bp["measured_at"]) == expected
    assert bp["note"] == "po kave"


@pytest.mark.asyncio
@pytest.mark.parametrize("payload, detail", [
    ({"raw": "145/02"}, "bp_range"),
    ({"raw": "85/130"}, "bp_range"),
    ({"raw": "130/85 250"}, "bp_range"),
    ({"raw": "130-85"}, "bp_format"),
    ({"raw": "130/85 72 25:00"}, "bp_format"),
    ({"raw": ""}, "bp_format"),
    ({}, "bp_format"),
    ({"systolic": 130}, "bp_format"),
    ({"systolic": 300, "diastolic": 80}, "bp_range"),
    ({"systolic": 120, "diastolic": 80, "measured_at": "7.30"}, "time_format"),
])
async def test_blood_pressure_errors(async_client, payload, detail):
    h = await _user_with_day(async_client)
    r = await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json=payload, headers=h)
    assert r.status_code == 422
    assert r.json() == {"detail": detail}
    day = (await async_client.get(f"{BASE}/days/{DAY}", headers=h)).json()
    assert day["blood_pressures"] == []


@pytest.mark.asyncio
async def test_blood_pressure_fields_and_ordering(async_client):
    h = await _user_with_day(async_client)
    url = f"{BASE}/days/{DAY}/blood-pressures"
    await async_client.post(url, json={"raw": "120/80"}, headers=h)
    await async_client.post(url, json={"systolic": 140, "diastolic": 90, "pulse": 80, "measured_at": "18:05"},
                            headers=h)
    await async_client.post(url, json={"raw": "130/85 72 7:30"}, headers=h)
    day = (await async_client.get(f"{BASE}/days/{DAY}", headers=h)).json()
    assert [(bp["systolic"], bp["measured_at"]) for bp in day["blood_pressures"]] == [
        (130, "07:30"), (140, "18:05"), (120, None),
    ]


@pytest.mark.asyncio
async def test_fill_time_only_today(async_client, fake_now):
    h = await _user_with_day(async_client, "2026-10-24")
    await async_client.post(f"{BASE}/days", json={"date": "2026-10-23"}, headers=h)
    r = await async_client.post(f"{BASE}/days/2026-10-24/blood-pressures", json={"raw": "130/85", "fill_time": True},
                                headers=h)
    assert r.json()["measured_at"] == "07:30"
    r = await async_client.post(f"{BASE}/days/2026-10-24/blood-pressures",
                                json={"raw": "130/85 6:00", "fill_time": True}, headers=h)
    assert r.json()["measured_at"] == "06:00"
    r = await async_client.post(f"{BASE}/days/2026-10-23/blood-pressures", json={"raw": "130/85", "fill_time": True},
                                headers=h)
    assert r.json()["measured_at"] is None
    r = await async_client.post(f"{BASE}/days/2026-10-24/weights", json={"kg": 80, "fill_time": True}, headers=h)
    assert r.json()["measured_at"] == "07:30"


@pytest.mark.asyncio
async def test_patch_and_delete_blood_pressure(async_client):
    h = await _user_with_day(async_client)
    bp = (await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json={"raw": "130/85 72 7:30"},
                                  headers=h)).json()
    url = f"{BASE}/blood-pressures/{bp['id']}"
    r = await async_client.patch(url, json={"pulse": 70, "note": "po kave"}, headers=h)
    assert (r.json()["pulse"], r.json()["note"], r.json()["systolic"]) == (70, "po kave", 130)
    r = await async_client.patch(url, json={"raw": "125/80 65 8:00"}, headers=h)
    assert (r.json()["systolic"], r.json()["diastolic"], r.json()["pulse"], r.json()["measured_at"]) == \
        (125, 80, 65, "08:00")
    r = await async_client.patch(url, json={"diastolic": 130}, headers=h)
    assert r.status_code == 422 and r.json() == {"detail": "bp_range"}
    r = await async_client.patch(url, json={"measured_at": None, "note": None}, headers=h)
    assert r.json()["measured_at"] is None and r.json()["note"] is None
    assert (await async_client.delete(url, headers=h)).status_code == 204
    assert (await async_client.get(f"{BASE}/days/{DAY}", headers=h)).json()["blood_pressures"] == []
    assert (await async_client.delete(url, headers=h)).status_code == 404


@pytest.mark.asyncio
async def test_two_blood_pressures_in_one_day(async_client):
    h = await _user_with_day(async_client)
    for raw in ("130/85 72 7:30", "125/80 68 20:00"):
        r = await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json={"raw": raw}, headers=h)
        assert r.status_code == 201
    day = (await async_client.get(f"{BASE}/days/{DAY}", headers=h)).json()
    assert len(day["blood_pressures"]) == 2


@pytest.mark.asyncio
async def test_weight_add_validate_patch_delete(async_client):
    h = await _user_with_day(async_client)
    url = f"{BASE}/days/{DAY}/weights"
    r = await async_client.post(url, json={"kg": 80.64, "measured_at": "7:05", "note": "rano"}, headers=h)
    assert r.status_code == 201, r.text
    weight = r.json()
    assert (weight["kg"], weight["measured_at"], weight["note"]) == (80.6, "07:05", "rano")
    for kg in (19.9, 300.1, -1):
        r = await async_client.post(url, json={"kg": kg}, headers=h)
        assert r.status_code == 422 and r.json() == {"detail": "weight_range"}
    r = await async_client.post(url, json={"kg": 80, "measured_at": "x"}, headers=h)
    assert r.status_code == 422 and r.json() == {"detail": "time_format"}

    w_url = f"{BASE}/weights/{weight['id']}"
    r = await async_client.patch(w_url, json={"kg": 81.25, "measured_at": None}, headers=h)
    assert (r.json()["kg"], r.json()["measured_at"]) == (81.3, None)
    r = await async_client.patch(w_url, json={"kg": 500}, headers=h)
    assert r.status_code == 422
    assert (await async_client.delete(w_url, headers=h)).status_code == 204
    assert (await async_client.get(f"{BASE}/days/{DAY}", headers=h)).json()["weights"] == []


@pytest.mark.asyncio
async def test_measurement_on_missing_day(async_client):
    h = await _register(async_client)
    r = await async_client.post(f"{BASE}/days/{DAY}/weights", json={"kg": 80}, headers=h)
    assert r.status_code == 404
    r = await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json={"raw": "120/80"}, headers=h)
    assert r.status_code == 404


# --- Isolation (constitution A1) -------------------------------------------------------------


@pytest.mark.asyncio
async def test_isolation_entries(async_client):
    a = await _user_with_day(async_client)
    b = await _user_with_day(async_client)
    entry = (await _add(async_client, a, "breakfast", "2 toasty")).json()["created"][0]

    r = await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"text": "hacked"}, headers=b)
    assert r.status_code == 404
    r = await async_client.delete(f"{BASE}/entries/{entry['id']}", headers=b)
    assert r.status_code == 404
    assert _short(await _entries(async_client, a, "breakfast")) == [("toasty", 2, None)]

    # B cannot add to A's day (B's own day with the same date is a different day).
    await async_client.delete(f"{BASE}/days/{DAY}", headers=b)
    r = await _add(async_client, b, "lunch", "x")
    assert r.status_code == 404

    # quantities only count the user's own entries.
    r = await async_client.get(f"{BASE}/quantities", params={"text": "toasty", "category": "breakfast"}, headers=b)
    assert r.json()["options"] == []
    r = await async_client.get(f"{BASE}/quantities", params={"text": "toasty", "category": "breakfast"}, headers=a)
    assert r.json()["options"] == [{"quantity": 2, "unit": None, "count": 1}]


@pytest.mark.asyncio
async def test_isolation_quantities_ignore_other_user(async_client):
    a = await _user_with_day(async_client)
    b = await _user_with_day(async_client)
    await _add(async_client, a, "lunch", "3 knedle")
    for _ in range(3):
        await _add(async_client, b, "lunch", "5 knedle")
    r = await async_client.get(f"{BASE}/quantities", params={"text": "knedle", "category": "lunch"}, headers=a)
    assert r.json()["options"] == [{"quantity": 3, "unit": None, "count": 1}]


@pytest.mark.asyncio
async def test_isolation_measurements(async_client):
    a = await _user_with_day(async_client)
    b = await _user_with_day(async_client)
    weight = (await async_client.post(f"{BASE}/days/{DAY}/weights", json={"kg": 80}, headers=a)).json()
    bp = (await async_client.post(f"{BASE}/days/{DAY}/blood-pressures", json={"raw": "130/85"}, headers=a)).json()

    for url, change in ((f"{BASE}/weights/{weight['id']}", {"kg": 90}),
                        (f"{BASE}/blood-pressures/{bp['id']}", {"pulse": 90})):
        assert (await async_client.patch(url, json=change, headers=b)).status_code == 404
        assert (await async_client.delete(url, headers=b)).status_code == 404
    day = (await async_client.get(f"{BASE}/days/{DAY}", headers=a)).json()
    assert day["weights"][0]["kg"] == 80 and day["blood_pressures"][0]["pulse"] is None
    assert (await async_client.get(f"{BASE}/days/{DAY}", headers=b)).json()["weights"] == []
