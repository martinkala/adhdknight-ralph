"""food-011: import of pasted rows (TSV from Google Sheets) with preview, conflicts and classification."""
from pathlib import Path

import httpx
from playwright.sync_api import expect

from conftest import login

FIXTURE = Path(__file__).resolve().parent.parent / "server" / "tests" / "fixtures" / "food" / "2026.csv"
# Header + 2026-10-23 (stool 6, gas 3) and 2026-10-22 (stool 7, gas 5), two rows each.
TWO_DAYS = "\n".join(FIXTURE.read_text(encoding="utf-8").splitlines()[:5])


class _Api:
    def __init__(self, api_server, email, password):
        r = httpx.post(f"{api_server}/api/v1/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        self.base = f"{api_server}/api/v1/food"
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    def day(self, day: str) -> dict:
        r = httpx.get(f"{self.base}/days/{day}", headers=self.headers)
        assert r.status_code == 200, r.text
        return r.json()

    def create_day(self, day: str, **values) -> None:
        assert httpx.post(f"{self.base}/days", json={"date": day}, headers=self.headers).status_code == 201
        r = httpx.patch(f"{self.base}/days/{day}", json=values, headers=self.headers)
        assert r.status_code == 200, r.text


def _user(page, user_factory, api_server) -> _Api:
    email, password = user_factory()
    api = _Api(api_server, email, password)
    login(page, email, password)
    return api


def _preview(page, text: str) -> None:
    page.goto("/food/")
    page.get_by_test_id("nav-food-import").click()
    page.get_by_test_id("import-input").fill(text)
    page.get_by_test_id("import-preview-submit").click()
    expect(page.get_by_test_id("import-preview")).to_be_visible()


def _classify_meds(page) -> None:
    items = page.get_by_test_id("classify-item")
    for i in range(items.count()):
        items.nth(i).get_by_test_id("classify-medication").click()


def _entry_count(day: dict) -> int:
    return sum(len(entries) for entries in day["entries"].values())


def test_import_two_days_into_calendar(page, user_factory, api_server, console_errors, failed_responses):
    api = _user(page, user_factory, api_server)
    _preview(page, TWO_DAYS)
    expect(page.get_by_test_id("import-day")).to_have_count(2)
    expect(page.get_by_test_id("total-new-days")).to_have_text("2")
    expect(page.get_by_test_id("classify-item")).to_have_count(2)  # emanera, prestarium
    submit = page.get_by_test_id("import-submit")
    expect(submit).to_be_disabled()
    _classify_meds(page)
    expect(submit).to_be_enabled()
    submit.click()

    expect(page.get_by_test_id("import-result")).to_be_visible()
    page.get_by_test_id("import-calendar-link").click()
    page.wait_for_url("**/food/?month=2026-10")
    expect(page.locator('[data-testid=cal-day][data-date="2026-10-23"] [data-testid=cal-dot]')).to_have_attribute(
        "data-severity", "mid")
    expect(page.locator('[data-testid=cal-day][data-date="2026-10-22"] [data-testid=cal-dot]')).to_have_attribute(
        "data-severity", "bad")
    day = api.day("2026-10-23")
    assert [(e["text"], e["quantity"]) for e in day["entries"]["medication"]] == [("emanera", 2), ("prestarium", None)]
    assert console_errors == []
    assert failed_responses == []


def test_conflict_apply_to_all_overwrite(page, user_factory, api_server, console_errors, failed_responses):
    api = _user(page, user_factory, api_server)
    api.create_day("2026-10-23", stool=2, gas=2)
    _preview(page, TWO_DAYS)
    conflicts = page.get_by_test_id("import-conflict")
    expect(conflicts).to_have_count(2)  # stool 2 → 6, gas 2 → 3
    expect(conflicts.first.get_by_test_id("conflict-keep")).to_contain_text("2")
    expect(conflicts.first.get_by_test_id("conflict-import")).to_contain_text("6")
    _classify_meds(page)
    expect(page.get_by_test_id("import-submit")).to_be_disabled()
    conflicts.first.get_by_test_id("conflict-import").click()
    page.get_by_test_id("apply-to-all").click()
    expect(conflicts.nth(1).get_by_test_id("conflict-import")).to_have_attribute("aria-pressed", "true")
    page.get_by_test_id("import-submit").click()
    expect(page.get_by_test_id("import-result")).to_be_visible()

    day = api.day("2026-10-23")
    assert (day["stool"], day["gas"]) == (6, 3)
    assert console_errors == []
    assert failed_responses == []


def test_repeated_import_creates_no_duplicates(page, user_factory, api_server, console_errors, failed_responses):
    api = _user(page, user_factory, api_server)
    _preview(page, TWO_DAYS)
    _classify_meds(page)
    page.get_by_test_id("import-submit").click()
    expect(page.get_by_test_id("import-result")).to_be_visible()
    counts = [_entry_count(api.day(d)) for d in ("2026-10-22", "2026-10-23")]

    _preview(page, TWO_DAYS)
    expect(page.get_by_test_id("total-entries-added")).to_have_text("0")
    expect(page.get_by_test_id("classify-item")).to_have_count(0)  # known from the first import
    expect(page.locator('[data-testid=import-day][data-status="merge"]')).to_have_count(2)
    page.get_by_test_id("import-submit").click()
    expect(page.get_by_test_id("import-entries-added")).to_have_text("0")
    assert [_entry_count(api.day(d)) for d in ("2026-10-22", "2026-10-23")] == counts
    assert console_errors == []
    assert failed_responses == []


def test_import_page_mobile_without_horizontal_scroll(mobile_page, user_factory):
    email, password = user_factory()
    login(mobile_page, email, password)
    mobile_page.goto("/food/import/")
    mobile_page.get_by_test_id("import-input").fill(TWO_DAYS)
    mobile_page.get_by_test_id("import-preview-submit").click()
    expect(mobile_page.get_by_test_id("import-preview")).to_be_visible()
    mobile_page.get_by_test_id("import-day").first.locator("summary").click()
    assert mobile_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    for test_id in ("import-preview-submit", "import-submit", "classify-medication"):
        assert mobile_page.get_by_test_id(test_id).first.bounding_box()["height"] >= 44
