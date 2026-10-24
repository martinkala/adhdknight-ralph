"""food-006: autocomplete suggestions (constitution D5): matching from the start of the text or of a
word without diacritics, grouping by text_norm, ordering by count, groups, deleted data, isolation, speed."""
import time
import uuid
from datetime import datetime, timezone

import pytest

from app.models.food import FoodDay, FoodEntry
from app.services.food_text import normalize

PASSWORD = "secure123"
BASE = "/api/v1/food"
DAY = "2026-10-01"


async def _register(async_client) -> dict:
    email = f"sugg-{uuid.uuid4().hex[:10]}@example.com"
    r = await async_client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _day(async_client, h, date: str = DAY) -> None:
    r = await async_client.post(f"{BASE}/days", json={"date": date}, headers=h)
    assert r.status_code == 201, r.text


async def _user_with_day(async_client, date: str = DAY) -> dict:
    h = await _register(async_client)
    await _day(async_client, h, date)
    return h


async def _add(async_client, h, category, text, date=DAY):
    r = await async_client.post(f"{BASE}/days/{date}/entries", json={"category": category, "text": text}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["created"]


async def _suggest(async_client, h, q="", group="food", **params):
    r = await async_client.get(f"{BASE}/suggestions", params={"group": group, "q": q, **params}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema_version"] == "1.0"
    return [(s["text"], s["count"]) for s in body["suggestions"]]


@pytest.mark.asyncio
async def test_ordered_by_count(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "lunch", "tuniak")
    for category in ("breakfast", "dinner", "unassigned"):
        await _add(async_client, h, category, "toasty")
    await _add(async_client, h, "lunch", "ryza")
    assert await _suggest(async_client, h, "t") == [("toasty", 3), ("tuniak", 1)]


@pytest.mark.asyncio
async def test_groups_spellings_without_diacritics(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "lunch", "Ryža")
    await _add(async_client, h, "dinner", "ryza")
    await _add(async_client, h, "breakfast", "Ryža")
    assert await _suggest(async_client, h, "ryz") == [("Ryža", 3)]
    assert await _suggest(async_client, h, "RYŽ") == [("Ryža", 3)]


@pytest.mark.asyncio
async def test_spelling_tie_uses_most_recent(async_client):
    h = await _user_with_day(async_client)
    await _day(async_client, h, "2026-10-02")
    await _add(async_client, h, "lunch", "Ryža")
    await _add(async_client, h, "lunch", "ryza", date="2026-10-02")
    assert await _suggest(async_client, h, "ryz") == [("ryza", 2)]


@pytest.mark.asyncio
async def test_count_tie_uses_last_use(async_client):
    h = await _user_with_day(async_client)
    await _day(async_client, h, "2026-10-02")
    await _add(async_client, h, "lunch", "tuniak", date="2026-10-02")
    await _add(async_client, h, "lunch", "toasty")
    assert await _suggest(async_client, h, "t") == [("tuniak", 1), ("toasty", 1)]


@pytest.mark.asyncio
async def test_matches_word_start_only(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "lunch", "smazeny tuniak")
    await _add(async_client, h, "dinner", "ryža 1/2 konzervy tuniak")
    assert sorted(await _suggest(async_client, h, "tuniak")) == [("ryža 1/2 konzervy tuniak", 1), ("smazeny tuniak", 1)]
    assert await _suggest(async_client, h, "niak") == []
    assert await _suggest(async_client, h, "smazeny tu") == [("smazeny tuniak", 1)]


@pytest.mark.asyncio
async def test_groups_are_separate(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "medication", "emanera")
    await _add(async_client, h, "supplement", "elektrolyty")
    await _add(async_client, h, "lunch", "egreše")
    await _add(async_client, h, "sport", "eBike 60 km")
    await _add(async_client, h, "note", "energia nizka")
    assert await _suggest(async_client, h, "e", group="food") == [("egreše", 1)]
    assert sorted(await _suggest(async_client, h, "e", group="meds")) == [("elektrolyty", 1), ("emanera", 1)]
    assert await _suggest(async_client, h, "e", group="sport") == [("eBike 60 km", 1)]


@pytest.mark.asyncio
@pytest.mark.parametrize("params", [{"group": "note"}, {"group": "drinks"}])
async def test_unknown_group(async_client, params):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/suggestions", params=params, headers=h)
    assert r.status_code == 422
    assert r.json()["detail"] == "unknown_group"


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, 21])
async def test_limit_range(async_client, limit):
    h = await _register(async_client)
    r = await async_client.get(f"{BASE}/suggestions", params={"group": "food", "limit": limit}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_empty_query_returns_most_used_with_limit(async_client):
    h = await _user_with_day(async_client)
    for i in range(12):
        await _add(async_client, h, "lunch", ", ".join([f"jedlo{i}"] * (i + 1)))  # merged: 1 entry, quantity i+1
    for i in range(12):
        for _ in range(i):
            await _add(async_client, h, "dinner", f"jedlo{i}")
    result = await _suggest(async_client, h)
    assert len(result) == 10
    assert result[0] == ("jedlo11", 12)
    assert [n for _, n in result] == sorted([n for _, n in result], reverse=True)
    assert len(await _suggest(async_client, h, limit=3)) == 3
    assert len(await _suggest(async_client, h, limit=20)) == 12


@pytest.mark.asyncio
async def test_deleted_entries_and_days_are_ignored(async_client):
    h = await _user_with_day(async_client)
    await _day(async_client, h, "2026-10-02")
    created = await _add(async_client, h, "lunch", "toasty, tuniak")
    await _add(async_client, h, "lunch", "toasty")
    await _add(async_client, h, "lunch", "tatarak", date="2026-10-02")
    r = await async_client.delete(f"{BASE}/entries/{created[1]['id']}", headers=h)
    assert r.status_code == 204
    r = await async_client.delete(f"{BASE}/days/2026-10-02", headers=h)
    assert r.status_code == 204, r.text
    assert await _suggest(async_client, h, "t") == [("toasty", 2)]


@pytest.mark.asyncio
async def test_entry_of_deleted_day_is_ignored_even_if_not_deleted(async_client, db_session):
    """Defensive: a not deleted entry of a deleted day is never suggested."""
    h = await _user_with_day(async_client)
    created = await _add(async_client, h, "lunch", "toasty")
    entry = await db_session.get(FoodEntry, created[0]["id"])
    day = await db_session.get(FoodDay, entry.day_id)
    day.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    assert await _suggest(async_client, h, "t") == []


@pytest.mark.asyncio
async def test_wildcards_are_literal(async_client):
    h = await _user_with_day(async_client)
    await _add(async_client, h, "lunch", "jogurt 3% tuku")
    await _add(async_client, h, "lunch", "jogurt 35 tuku")
    await _add(async_client, h, "lunch", "a_b")
    await _add(async_client, h, "lunch", "axb")
    assert await _suggest(async_client, h, "3%") == [("jogurt 3% tuku", 1)]
    assert await _suggest(async_client, h, "%") == []
    assert await _suggest(async_client, h, "a_") == [("a_b", 1)]
    assert await _suggest(async_client, h, "_") == []


@pytest.mark.asyncio
async def test_isolation(async_client):
    a = await _user_with_day(async_client)
    b = await _user_with_day(async_client)
    await _add(async_client, a, "lunch", "toasty")
    for _ in range(3):
        await _add(async_client, b, "lunch", "tajne jedlo B, toasty")
    await _add(async_client, b, "medication", "liek B")
    assert await _suggest(async_client, a, "t") == [("toasty", 1)]
    assert await _suggest(async_client, a) == [("toasty", 1)]
    assert await _suggest(async_client, a, group="meds") == []
    assert await _suggest(async_client, a, "liek", group="meds") == []


@pytest.mark.asyncio
async def test_requires_login(async_client):
    r = await async_client.get(f"{BASE}/suggestions", params={"group": "food"})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_1000_entries_are_fast(async_client, db_session):
    h = await _user_with_day(async_client)
    created = await _add(async_client, h, "breakfast", "kakao")
    day = await db_session.get(FoodDay, (await db_session.get(FoodEntry, created[0]["id"])).day_id)
    words = ["toasty", "tuniak", "ryža", "kafe", "jablko", "rožok", "syr", "šunka", "polievka", "chlieb"]
    for i in range(1000):
        text = f"{words[i % len(words)]} {i % 37}"
        db_session.add(FoodEntry(day_id=day.id, user_id=day.user_id, category="lunch", text=text,
                                 text_norm=normalize(text), position=i))
    await db_session.commit()
    await _suggest(async_client, h, "t")  # warm up
    start = time.perf_counter()
    result = await _suggest(async_client, h, "t")
    empty = await _suggest(async_client, h, "")
    elapsed = (time.perf_counter() - start) / 2
    assert len(result) == 10 and len(empty) == 10
    assert elapsed < 0.3 * 3, f"{elapsed:.3f}s"
