"""food-007: medication dictionary (CRUD, moving entries on a kind change) and the common meds input
with `needs_classification` (constitution D7). Isolation: A's dictionary is invisible to B."""
import uuid

import pytest

PASSWORD = "secure123"
BASE = "/api/v1/food"
DAY = "2026-10-01"
DAY2 = "2026-10-02"


async def _user(async_client, *days: str) -> dict:
    email = f"meds-{uuid.uuid4().hex[:10]}@example.com"
    r = await async_client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    for date in days or (DAY,):
        r = await async_client.post(f"{BASE}/days", json={"date": date}, headers=h)
        assert r.status_code == 201, r.text
    return h


async def _dictionary(async_client, h) -> list[tuple]:
    r = await async_client.get(f"{BASE}/med-dictionary", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["schema_version"] == "1.0"
    return [(i["text_norm"], i["display_text"], i["kind"], i["usage_count"]) for i in r.json()["items"]]


async def _meds(async_client, h, text, classify=None, date=DAY):
    body = {"text": text} if classify is None else {"text": text, "classify": classify}
    return await async_client.post(f"{BASE}/days/{date}/meds", json=body, headers=h)


async def _sections(async_client, h, date=DAY) -> dict:
    r = await async_client.get(f"{BASE}/days/{date}", headers=h)
    assert r.status_code == 200
    entries = r.json()["entries"]
    return {k: [(e["text"], e["quantity"]) for e in entries[k]] for k in ("medication", "supplement")}


async def _put(async_client, h, text_norm, kind, **extra):
    return await async_client.put(f"{BASE}/med-dictionary/{text_norm}", json={"kind": kind, **extra}, headers=h)


# --- FR-1: dictionary API --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dictionary_crud(async_client):
    h = await _user(async_client)
    assert await _dictionary(async_client, h) == []
    r = await _put(async_client, h, "zn", "supplement")
    assert r.status_code == 200, r.text
    assert r.json() == {"schema_version": "1.0", "text_norm": "zn", "display_text": "zn", "kind": "supplement",
                        "usage_count": 0}
    r = await _put(async_client, h, "Prestárium", "medication", display_text="Prestárium")
    assert r.json()["text_norm"] == "prestarium"
    assert await _dictionary(async_client, h) == [
        ("prestarium", "Prestárium", "medication", 0), ("zn", "zn", "supplement", 0),
    ]
    r = await _put(async_client, h, "zn", "medication")
    assert r.json()["kind"] == "medication"
    assert r.json()["display_text"] == "zn"

    r = await async_client.delete(f"{BASE}/med-dictionary/zn", headers=h)
    assert r.status_code == 204
    assert await _dictionary(async_client, h) == [("prestarium", "Prestárium", "medication", 0)]
    r = await async_client.delete(f"{BASE}/med-dictionary/zn", headers=h)
    assert r.status_code == 404
    assert r.json()["detail"] == "dictionary_item_not_found"
    # Saving a deleted item restores it.
    assert (await _put(async_client, h, "zn", "supplement")).status_code == 200
    assert ("zn", "zn", "supplement", 0) in await _dictionary(async_client, h)


@pytest.mark.asyncio
async def test_dictionary_validation(async_client):
    h = await _user(async_client)
    assert (await _put(async_client, h, "zn", "vitamin")).status_code == 422
    assert (await _put(async_client, h, "%20", "medication")).status_code == 422
    r = await async_client.put(f"{BASE}/med-dictionary/zn", json={"kind": "medication", "x": 1}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_kind_change_moves_existing_entries(async_client):
    h = await _user(async_client, DAY, DAY2)
    await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "medication", "text": "prestarium"},
                            headers=h)
    for date in (DAY, DAY2):
        r = await async_client.post(f"{BASE}/days/{date}/entries", json={"category": "supplement", "text": "Zn, mg"},
                                    headers=h)
        assert r.status_code == 201
    assert ("zn", "Zn", "supplement", 2) in await _dictionary(async_client, h)

    r = await _put(async_client, h, "zn", "medication")
    assert r.json()["usage_count"] == 2
    for date in (DAY, DAY2):
        sections = await _sections(async_client, h, date)
        assert ("Zn", None) in sections["medication"]
        assert sections["supplement"] == [("mg", None)]
    # Moved entries go to the end of the target section.
    r = await async_client.get(f"{BASE}/days/{DAY}", headers=h)
    meds = r.json()["entries"]["medication"]
    assert [(e["text"], e["position"]) for e in meds] == [("prestarium", 0), ("Zn", 1)]

    await _put(async_client, h, "zn", "supplement")
    assert (await _sections(async_client, h))["supplement"] == [("mg", None), ("Zn", None)]


@pytest.mark.asyncio
async def test_delete_keeps_entries(async_client):
    h = await _user(async_client)
    await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "supplement", "text": "zn"}, headers=h)
    assert (await async_client.delete(f"{BASE}/med-dictionary/zn", headers=h)).status_code == 204
    assert (await _sections(async_client, h))["supplement"] == [("zn", None)]


@pytest.mark.asyncio
async def test_entry_in_med_category_fills_dictionary(async_client):
    h = await _user(async_client)
    r = await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "supplement", "text": "zn"}, headers=h)
    assert r.status_code == 201
    assert r.json()["created"][0]["text_norm"] == "zn"
    assert await _dictionary(async_client, h) == [("zn", "zn", "supplement", 1)]
    # An existing item keeps its kind.
    await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "medication", "text": "ZN"}, headers=h)
    assert await _dictionary(async_client, h) == [("zn", "zn", "supplement", 2)]
    # Other categories do not touch the dictionary.
    await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "lunch", "text": "ryza"}, headers=h)
    assert len(await _dictionary(async_client, h)) == 1


@pytest.mark.asyncio
async def test_dictionary_isolation(async_client):
    a = await _user(async_client)
    b = await _user(async_client)
    await _put(async_client, a, "zn", "supplement")
    await async_client.post(f"{BASE}/days/{DAY}/entries", json={"category": "supplement", "text": "zn"}, headers=a)
    assert await _dictionary(async_client, b) == []
    # B cannot delete A's item; the same text_norm can have another kind for B.
    assert (await async_client.delete(f"{BASE}/med-dictionary/zn", headers=b)).status_code == 404
    assert (await _put(async_client, b, "zn", "medication")).status_code == 200
    assert await _dictionary(async_client, a) == [("zn", "zn", "supplement", 1)]
    assert await _dictionary(async_client, b) == [("zn", "zn", "medication", 0)]
    # B's kind change does not move A's entries.
    assert (await _sections(async_client, a))["supplement"] == [("zn", None)]
    # B's meds input does not use A's dictionary.
    r = await _meds(async_client, a, "zn")
    assert r.status_code == 201
    await _put(async_client, a, "emanera", "medication")
    r = await _meds(async_client, b, "emanera")
    assert r.status_code == 200
    assert r.json()["needs_classification"] == [{"text": "emanera", "text_norm": "emanera"}]


@pytest.mark.asyncio
async def test_dictionary_requires_auth(async_client):
    assert (await async_client.get(f"{BASE}/med-dictionary")).status_code == 401
    assert (await async_client.put(f"{BASE}/med-dictionary/zn", json={"kind": "medication"})).status_code == 401
    assert (await async_client.post(f"{BASE}/days/{DAY}/meds", json={"text": "zn"})).status_code == 401


# --- FR-2: common meds input -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_meds_classification_flow(async_client):
    h = await _user(async_client, DAY, DAY2)
    r = await _meds(async_client, h, "prestarium, zn")
    assert r.status_code == 200
    assert r.json() == {"schema_version": "1.0", "created": [], "needs_classification": [
        {"text": "prestarium", "text_norm": "prestarium"}, {"text": "zn", "text_norm": "zn"},
    ]}
    assert await _sections(async_client, h) == {"medication": [], "supplement": []}
    assert await _dictionary(async_client, h) == []

    r = await _meds(async_client, h, "prestarium, zn", {"prestarium": "medication", "zn": "supplement"})
    assert r.status_code == 201, r.text
    assert r.json()["needs_classification"] == []
    assert sorted((e["category"], e["text"]) for e in r.json()["created"]) == [
        ("medication", "prestarium"), ("supplement", "zn"),
    ]
    assert await _sections(async_client, h) == {"medication": [("prestarium", None)], "supplement": [("zn", None)]}
    assert await _dictionary(async_client, h) == [
        ("prestarium", "prestarium", "medication", 1), ("zn", "zn", "supplement", 1),
    ]

    r = await _meds(async_client, h, "zn, prestarium, emanera", date=DAY2)
    assert r.status_code == 200
    assert r.json()["needs_classification"] == [{"text": "emanera", "text_norm": "emanera"}]
    assert await _sections(async_client, h, DAY2) == {"medication": [], "supplement": []}

    r = await _meds(async_client, h, "zn, prestarium, emanera", {"emanera": "medication"}, date=DAY2)
    assert r.status_code == 201
    assert await _sections(async_client, h, DAY2) == {
        "medication": [("prestarium", None), ("emanera", None)], "supplement": [("zn", None)],
    }


@pytest.mark.asyncio
async def test_meds_classify_keys_are_normalized(async_client):
    h = await _user(async_client)
    r = await _meds(async_client, h, "Vitamín D", {"Vitamín  D": "supplement"})
    assert r.status_code == 201
    assert await _dictionary(async_client, h) == [("vitamin d", "Vitamín D", "supplement", 1)]


@pytest.mark.asyncio
async def test_meds_plus_splits_items(async_client):
    h = await _user(async_client)
    classify = {"omega": "supplement", "fe": "supplement", "d": "supplement"}
    r = await _meds(async_client, h, "omega+fe+D", classify)
    assert r.status_code == 201
    assert [e["text"] for e in r.json()["created"]] == ["omega", "fe", "D"]
    r = await _meds(async_client, h, "zn + mg")
    assert [i["text"] for i in r.json()["needs_classification"]] == ["zn", "mg"]


@pytest.mark.asyncio
async def test_meds_repeated_item_is_merged(async_client):
    h = await _user(async_client)
    await _put(async_client, h, "emanera", "medication")
    await _put(async_client, h, "prestarium", "medication")
    r = await _meds(async_client, h, "emanera, prestarium, emanera")
    assert r.status_code == 201
    assert (await _sections(async_client, h))["medication"] == [("emanera", 2.0), ("prestarium", None)]


@pytest.mark.asyncio
async def test_meds_quantity_and_errors(async_client):
    h = await _user(async_client)
    await _put(async_client, h, "mg", "supplement")
    r = await _meds(async_client, h, "2 mg")
    assert r.status_code == 201
    assert (await _sections(async_client, h))["supplement"] == [("mg", 2.0)]
    assert (await _meds(async_client, h, " , + ")).json()["detail"] == "empty_text"
    assert (await _meds(async_client, h, "x" * 201)).json()["detail"] == "text_too_long"
    assert (await _meds(async_client, h, "mg", {"mg": "vitamin"})).status_code == 422
    assert (await _meds(async_client, h, "mg", date="2026-09-01")).status_code == 404


@pytest.mark.asyncio
async def test_meds_other_users_day_is_404(async_client):
    a = await _user(async_client)
    b = await _user(async_client, "2026-09-15")
    await _put(async_client, b, "zn", "supplement")
    r = await _meds(async_client, b, "zn")
    assert r.status_code == 404
    assert (await _sections(async_client, a))["supplement"] == []
