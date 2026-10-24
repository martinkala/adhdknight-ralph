"""food-011: import preview / commit (merge, conflicts, classification, one transaction), isolation."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.dependencies import get_now
from app.main import app
from app.services import food_import_merge

PASSWORD = "secure123"
BASE = "/api/v1/food"
FAKE_NOW = datetime(2026, 10, 24, 16, 0, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent.parent / "fixtures" / "food"
# Header + the days 2026-10-23 and 2026-10-22 (two rows each) of 2026.csv.
TWO_DAYS = "\n".join((FIXTURES / "2026.csv").read_text(encoding="utf-8").splitlines()[:5])
CLASSIFY = {"emanera": "medication", "prestarium": "medication"}
HEADER = " \tspanok\tRanajky\toills\tdig problemy (1-10) s/v"


@pytest.fixture(autouse=True)
def fake_now():
    app.dependency_overrides[get_now] = lambda: FAKE_NOW
    yield FAKE_NOW
    app.dependency_overrides.pop(get_now, None)


async def _register(async_client) -> dict:
    email = f"food-{uuid.uuid4().hex[:10]}@example.com"
    r = await async_client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _preview(async_client, h, raw_text: str, expected: int = 200, **extra) -> dict:
    r = await async_client.post(f"{BASE}/import/preview", json={"raw_text": raw_text, **extra}, headers=h)
    assert r.status_code == expected, r.text
    return r.json()


async def _commit(async_client, h, raw_text: str, expected: int = 200, **extra) -> dict:
    r = await async_client.post(f"{BASE}/import/commit", json={"raw_text": raw_text, **extra}, headers=h)
    assert r.status_code == expected, r.text
    return r.json()


async def _export(async_client, h) -> dict:
    r = await async_client.get(f"{BASE}/export", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


async def _day(async_client, h, date: str) -> dict:
    r = await async_client.get(f"{BASE}/days/{date}", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _row(date: str, sleep: str = "", breakfast: str = "", meds: str = "", digestion: str = "") -> str:
    return "\t".join((date, sleep, breakfast, meds, digestion))


@pytest.mark.asyncio
async def test_import_into_empty_account_then_again(async_client):
    h = await _register(async_client)
    preview = await _preview(async_client, h, TWO_DAYS)
    assert preview["schema_version"] == "1.0" and preview["format"] == "tsv"
    assert [(d["date"], d["status"]) for d in preview["days"]] == [("2026-10-22", "new"), ("2026-10-23", "new")]
    assert {m["text_norm"] for m in preview["needs_classification"]} == {"emanera", "prestarium"}
    day = preview["days"][1]
    assert day["add"]["values"] == {"stool": 6, "gas": 3}
    assert day["add"]["entries"]["dinner"] == [
        {"text": "toasty", "quantity": 2.0, "unit": None, "intensity": None},
        {"text": "zemiaky jogurt", "quantity": None, "unit": None, "intensity": None},
    ]
    assert day["add"]["blood_pressures"][0]["systolic"] == 125
    assert preview["totals"]["new_days"] == 2
    assert (await _export(async_client, h))["days"] == []  # preview stores nothing

    result = await _commit(async_client, h, TWO_DAYS, classify=CLASSIFY)
    assert result["dates"] == ["2026-10-22", "2026-10-23"]
    stored = await _day(async_client, h, "2026-10-23")
    assert (stored["stool"], stored["gas"]) == (6, 3)
    assert [(e["text"], e["quantity"]) for e in stored["entries"]["medication"]] == [("emanera", 2), ("prestarium", None)]
    assert [w["kg"] for w in stored["weights"]] == [80.6]
    added = result["totals"]["entries_added"] + result["totals"]["measurements_added"]
    assert result["totals"]["entries_added"] > 0

    again = await _preview(async_client, h, TWO_DAYS)
    assert [d["status"] for d in again["days"]] == ["merge", "merge"]
    assert again["needs_classification"] == []  # the dictionary knows them now
    assert again["totals"]["duplicates_skipped"] == added
    result = await _commit(async_client, h, TWO_DAYS)
    assert result["totals"]["entries_added"] == 0
    assert result["totals"]["measurements_added"] == 0
    assert result["totals"]["values_filled"] == 0 and result["totals"]["conflicts"] == 0
    assert (await _day(async_client, h, "2026-10-23"))["entries"] == stored["entries"]


@pytest.mark.asyncio
async def test_conflict_needs_a_resolution(async_client):
    h = await _register(async_client)
    await _commit(async_client, h, HEADER + "\n" + _row("2026-10-20", sleep="2", breakfast="ryza", digestion="3/4"))
    raw = HEADER + "\n" + _row("2026-10-20", sleep="2", breakfast="ryza, kafe", digestion="5/4")

    preview = await _preview(async_client, h, raw)
    day = preview["days"][0]
    assert day["status"] == "merge"
    assert day["conflicts"] == [{"date": "2026-10-20", "field": "stool", "existing": 3, "incoming": 5}]
    assert day["duplicates_skipped"] == 1
    assert list(day["add"]["entries"]) == ["breakfast"] and day["add"]["entries"]["breakfast"][0]["text"] == "kafe"

    body = await _commit(async_client, h, raw, expected=409)
    assert body["detail"] == "unresolved"
    assert body["preview"]["totals"]["conflicts"] == 1
    stored = await _day(async_client, h, "2026-10-20")
    assert stored["stool"] == 3 and [e["text"] for e in stored["entries"]["breakfast"]] == ["ryza"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra, stool", [
    ({"resolutions": [{"date": "2026-10-20", "field": "stool", "choice": "import"}]}, 5),
    ({"resolutions": [{"date": "2026-10-20", "field": "stool", "choice": "keep"}]}, 3),
    ({"default_resolution": "import"}, 5),
])
async def test_conflict_resolutions(async_client, extra, stool):
    h = await _register(async_client)
    await _commit(async_client, h, HEADER + "\n" + _row("2026-10-20", digestion="3/4"))
    raw = HEADER + "\n" + _row("2026-10-20", sleep="3", digestion="5/4")
    await _commit(async_client, h, raw, **extra)
    stored = await _day(async_client, h, "2026-10-20")
    assert (stored["sleep_quality"], stored["stool"], stored["gas"]) == (3, stool, 4)


@pytest.mark.asyncio
async def test_default_resolution_applies_to_all_conflicts(async_client):
    h = await _register(async_client)
    await _commit(async_client, h, HEADER + "\n" + _row("2026-10-20", sleep="1", digestion="3/4"))
    raw = HEADER + "\n" + _row("2026-10-20", sleep="3", digestion="5/6")
    resolution = [{"date": "2026-10-20", "field": "stool", "choice": "keep"}]
    await _commit(async_client, h, raw, expected=409, resolutions=resolution)
    await _commit(async_client, h, raw, resolutions=resolution, default_resolution="import")
    stored = await _day(async_client, h, "2026-10-20")
    assert (stored["sleep_quality"], stored["stool"], stored["gas"]) == (3, 3, 6)


@pytest.mark.asyncio
async def test_unclassified_medication(async_client):
    h = await _register(async_client)
    raw = HEADER + "\n" + _row("2026-10-20", meds="omega+fe, emanera")
    body = await _commit(async_client, h, raw, expected=409)
    assert {m["text_norm"] for m in body["preview"]["needs_classification"]} == {"omega", "fe", "emanera"}
    assert (await _export(async_client, h))["days"] == []

    classify = {"omega": "supplement", "fe": "supplement", "emanera": "medication"}
    await _commit(async_client, h, raw, classify=classify)
    stored = await _day(async_client, h, "2026-10-20")
    assert [e["text"] for e in stored["entries"]["supplement"]] == ["omega", "fe"]
    assert [e["text"] for e in stored["entries"]["medication"]] == ["emanera"]
    r = await async_client.get(f"{BASE}/med-dictionary", headers=h)
    assert {(i["text_norm"], i["kind"]) for i in r.json()["items"]} == set(classify.items())


@pytest.mark.asyncio
async def test_error_while_saving_rolls_back(async_client, monkeypatch):
    h = await _register(async_client)
    await _commit(async_client, h, HEADER + "\n" + _row("2026-10-19", breakfast="ryza", digestion="2/2"))
    before = await _export(async_client, h)

    async def broken_stage(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(food_import_merge.med_dictionary, "stage", broken_stage)
    raw = "\n".join((HEADER, _row("2026-10-19", sleep="2", breakfast="kafe"),
                     _row("2026-10-20", breakfast="toasty", meds="emanera")))
    with pytest.raises(RuntimeError):
        await _commit(async_client, h, raw, classify={"emanera": "medication"})
    monkeypatch.undo()
    after = await _export(async_client, h)
    assert after["days"] == before["days"]


@pytest.mark.asyncio
async def test_merge_only_with_own_data(async_client):
    a = await _register(async_client)
    b = await _register(async_client)
    raw = HEADER + "\n" + _row("2026-10-20", breakfast="tajne jedlo", digestion="3/3", meds="emanera")
    await _commit(async_client, a, raw, classify={"emanera": "medication"})

    preview = await _preview(async_client, b, raw)
    assert preview["days"][0]["status"] == "new"
    assert preview["days"][0]["duplicates_skipped"] == 0 and preview["days"][0]["conflicts"] == []
    assert preview["needs_classification"] == [{"text": "emanera", "text_norm": "emanera"}]  # A's dictionary is not used
    raw_b = HEADER + "\n" + _row("2026-10-20", breakfast="tajne jedlo", digestion="7/7")
    await _commit(async_client, b, raw_b)
    assert (await _day(async_client, b, "2026-10-20"))["stool"] == 7
    stored_a = await _day(async_client, a, "2026-10-20")
    assert stored_a["stool"] == 3 and len(stored_a["entries"]["breakfast"]) == 1


@pytest.mark.asyncio
async def test_json_round_trip(async_client):
    a = await _register(async_client)
    raw = "\n".join((
        TWO_DAYS,
        "2026-10-21\t\t2\t2x babovka, .5 l kofoly\t\t\t\t\t\tzn\tbolest\t130/85 72 7:30, 120/80\t1/1\thlava\t\t80,3\tbeh\tpozn",
    ))
    await _commit(async_client, a, raw, classify={**CLASSIFY, "zn": "supplement"})
    r = await async_client.post(f"{BASE}/days", json={"date": "2026-10-24"}, headers=a)  # an empty day
    assert r.status_code == 201
    entry = (await _day(async_client, a, "2026-10-21"))["entries"]["sport"][0]
    await async_client.patch(f"{BASE}/entries/{entry['id']}", json={"intensity": 4}, headers=a)
    r = await async_client.post(f"{BASE}/days/2026-10-21/weights", json={"kg": 80.1, "measured_at": "06:15",
                                                                         "note": "rano"}, headers=a)
    assert r.status_code == 201
    exported = await _export(async_client, a)

    b = await _register(async_client)
    result = await _commit(async_client, b, json.dumps(exported), format="json")
    assert result["dates"] == ["2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24"]
    again = await _export(async_client, b)
    exported.pop("exported_at")
    again.pop("exported_at")
    assert again == exported


@pytest.mark.asyncio
async def test_input_errors(async_client):
    h = await _register(async_client)
    body = await _preview(async_client, h, (FIXTURES / "2025.csv").read_text(encoding="utf-8"), expected=422)
    assert body["detail"] == "unsupported_format_legacy"
    body = await _preview(async_client, h, "{not json", expected=422)
    assert body["detail"] == "invalid_json"
    body = await _preview(async_client, h, "x" * (1024 * 1024 + 1), expected=413)
    assert body["detail"] == "input_too_large"
    await _preview(async_client, h, "a", format="xml", expected=422)
    r = await async_client.post(f"{BASE}/import/preview", json={"raw_text": TWO_DAYS})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_preview_reports_issues_and_future_days(async_client):
    h = await _register(async_client)
    raw = "\n".join((
        " \tRanajky\tpresure\tkalorie",
        "2026-10-25\tryza\t\t",
        "2026-10-20\tryza\t145/02\t2000",
        "2026-10-19\t\t\t",
    ))
    preview = await _preview(async_client, h, raw)
    assert [d["date"] for d in preview["days"]] == ["2026-10-20"]
    assert preview["days"][0]["add"]["blood_pressures"] == []
    assert {(i["date"], i["code"]) for i in preview["issues"]} == {("2026-10-25", "future_date"),
                                                                    ("2026-10-20", "bp_range")}
    assert preview["unknown_columns"] == ["kalorie"]
    assert preview["skipped_empty_days"] == ["2026-10-19"]


@pytest.mark.asyncio
async def test_openapi_has_import(async_client):
    paths = (await async_client.get("/openapi.json")).json()["paths"]
    assert "post" in paths[f"{BASE}/import/preview"] and "post" in paths[f"{BASE}/import/commit"]


@pytest.mark.asyncio
async def test_data_sample_meds_after_classification(async_client):
    h = await _register(async_client)
    raw = (FIXTURES / "data_sample.txt").read_text(encoding="utf-8")
    preview = await _preview(async_client, h, raw)
    assert preview["format"] == "csv"
    assert {m["text_norm"] for m in preview["needs_classification"]} == {"zn", "mg", "omega", "fe", "d",
                                                                         "prestarium", "emanera"}
    classify = {"zn": "supplement", "mg": "supplement", "omega": "supplement", "fe": "supplement", "d": "supplement",
                "prestarium": "medication", "emanera": "medication"}
    await _commit(async_client, h, raw, classify=classify)
    day = await _day(async_client, h, "2026-07-06")
    assert [e["text"] for e in day["entries"]["supplement"]] == ["zn", "mg", "omega", "fe", "D"]
    assert [e["text"] for e in day["entries"]["medication"]] == ["prestarium", "emanera"]
    day = await _day(async_client, h, "2026-07-10")
    assert [(e["text"], e["quantity"]) for e in day["entries"]["breakfast"]] == [
        ("salamy chleba", None), ("sunka", None), ("nealko piva", 2)]
