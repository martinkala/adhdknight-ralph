"""food-009: export page downloads CSV and JSON with the user's entries."""
import csv
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from playwright.sync_api import expect

from conftest import login


def _user_with_entry(page, user_factory, api_server) -> str:
    email, password = user_factory()
    r = httpx.post(f"{api_server}/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    base = f"{api_server}/api/v1/food"
    today = datetime.now(ZoneInfo("Europe/Bratislava")).date().isoformat()
    assert httpx.post(f"{base}/days", json={"date": today}, headers=headers).status_code == 201
    r = httpx.post(f"{base}/days/{today}/entries", json={"category": "lunch", "text": "2 rožky, \"šunka\""},
                   headers=headers)
    assert r.status_code == 201, r.text
    login(page, email, password)
    return today


def _download(page, file_format: str):
    page.get_by_test_id(f"export-format-{file_format}").check()
    with page.expect_download() as info:
        page.get_by_test_id("export-submit").click()
    download = info.value
    with open(download.path(), "rb") as f:
        return download.suggested_filename, f.read()


def test_export_csv_and_json(page, user_factory, api_server, console_errors, failed_responses):
    today = _user_with_entry(page, user_factory, api_server)
    page.goto("/food/")
    page.get_by_test_id("nav-food-export").click()
    expect(page.get_by_test_id("export-form")).to_be_visible()

    name, content = _download(page, "csv")
    assert name == f"food-diary-{today}-{today}.csv"
    assert content.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline="")))
    assert {(r["text"], r["quantity"]) for r in rows} == {("rožky", "2"), ('"šunka"', "")}

    name, content = _download(page, "json")
    assert name.endswith(".json")
    body = json.loads(content)
    assert [d["date"] for d in body["days"]] == [today]
    assert [e["text"] for e in body["days"][0]["entries"]["lunch"]] == ["rožky", '"šunka"']

    # A range without days gives an empty, but valid file.
    page.get_by_test_id("export-from").fill("2020-01-01")
    page.get_by_test_id("export-to").fill("2020-01-31")
    name, content = _download(page, "json")
    assert name == "food-diary-2020-01-01-2020-01-31.json"
    assert json.loads(content)["days"] == []

    assert console_errors == []
    assert failed_responses == []


def test_export_page_mobile_without_horizontal_scroll(mobile_page, user_factory):
    email, password = user_factory()
    login(mobile_page, email, password)
    mobile_page.goto("/food/export/")
    expect(mobile_page.get_by_test_id("export-form")).to_be_visible()
    assert mobile_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    box = mobile_page.get_by_test_id("export-submit").bounding_box()
    assert box["height"] >= 44
