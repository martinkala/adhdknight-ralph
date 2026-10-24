"""food-008: month calendar (severity dots, creating a day by tap, future days, mobile grid) and days list."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from playwright.sync_api import expect

from conftest import login


def _today() -> date:
    # New users have the default timezone (constitution B4).
    return datetime.now(ZoneInfo("Europe/Bratislava")).date()


def _prev_month() -> str:
    return (_today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")


class _Api:
    def __init__(self, api_server, email, password):
        r = httpx.post(f"{api_server}/api/v1/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        self.base = f"{api_server}/api/v1/food"
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    def day(self, day: str, **values) -> None:
        r = httpx.post(f"{self.base}/days", json={"date": day}, headers=self.headers)
        assert r.status_code == 201, r.text
        if values:
            r = httpx.patch(f"{self.base}/days/{day}", json=values, headers=self.headers)
            assert r.status_code == 200, r.text


def _user(page, user_factory, api_server) -> _Api:
    email, password = user_factory()
    api = _Api(api_server, email, password)
    login(page, email, password)
    return api


def _assert_clean(console_errors, failed_responses):
    assert console_errors == []
    assert failed_responses == []


def test_calendar_severity_dots(page, user_factory, api_server, console_errors, failed_responses):
    api = _user(page, user_factory, api_server)
    month = _prev_month()
    api.day(f"{month}-02", stool=2, gas=3)
    api.day(f"{month}-03", stool=4, gas=1)
    api.day(f"{month}-04", stool=2, gas=9)
    api.day(f"{month}-05")

    page.goto("/food/")
    page.get_by_test_id("cal-prev").click()
    page.wait_for_url(f"**/food/?month={month}")
    expect(page.get_by_test_id("cal-dot")).to_have_count(4)
    for day, severity in (("02", "ok"), ("03", "mid"), ("04", "bad"), ("05", "none")):
        cell = page.locator(f'[data-testid="cal-day"][data-date="{month}-{day}"]')
        expect(cell.get_by_test_id("cal-dot")).to_have_attribute("data-severity", severity)
    expect(page.locator(f'[data-testid="cal-day"][data-date="{month}-04"] [data-testid="cal-dot"]')) \
        .to_have_attribute("aria-label", "Stool 2, gas 9")
    expect(page.get_by_test_id("cal-legend")).to_be_visible()

    # Tap opens the existing day; going back returns to its month.
    page.locator(f'[data-testid="cal-day"][data-date="{month}-03"]').click()
    page.wait_for_url(f"**/food/day/{month}-03/")
    page.get_by_test_id("back-to-calendar").click()
    page.wait_for_url(f"**/food/?month={month}")
    _assert_clean(console_errors, failed_responses)


def test_tap_on_missing_day_creates_it(page, user_factory, api_server, console_errors, failed_responses):
    _user(page, user_factory, api_server)
    month = _prev_month()
    page.goto(f"/food/?month={month}")
    expect(page.get_by_test_id("cal-dot")).to_have_count(0)
    page.locator(f'[data-testid="cal-day"][data-date="{month}-10"]').click()
    page.wait_for_url(f"**/food/day/{month}-10/")
    expect(page.get_by_test_id("day-title")).to_have_attribute("data-date", f"{month}-10")

    page.goto(f"/food/?month={month}")
    expect(page.get_by_test_id("cal-dot")).to_have_count(1)
    expect(page.locator(f'[data-testid="cal-day"][data-date="{month}-10"]')).to_have_attribute(
        "href", f"/food/day/{month}-10/")
    _assert_clean(console_errors, failed_responses)


def test_future_days_and_next_month_disabled(page, user_factory, api_server, console_errors, failed_responses):
    _user(page, user_factory, api_server)
    today = _today()
    page.goto("/food/")
    expect(page.get_by_test_id("calendar")).to_be_visible()
    expect(page.get_by_test_id("cal-next")).to_have_attribute("aria-disabled", "true")
    assert page.get_by_test_id("cal-next").evaluate("el => el.tagName") == "SPAN"
    tomorrow = today + timedelta(days=1)
    if tomorrow.month == today.month:
        future = page.locator(f'[data-testid="cal-day"][data-date="{tomorrow.isoformat()}"]')
        assert future.evaluate("el => el.tagName") == "SPAN"
        assert future.evaluate("el => el.closest('a, button') === null")
    today_cell = page.locator(f'[data-testid="cal-day"][data-date="{today.isoformat()}"]')
    expect(today_cell).to_have_attribute("aria-current", "date")
    # A future month in the URL falls back to the current month.
    next_month = (today.replace(day=28) + timedelta(days=5)).strftime("%Y-%m")
    page.goto(f"/food/?month={next_month}")
    expect(page.get_by_test_id("cal-title")).to_have_attribute("data-month", today.strftime("%Y-%m"))
    _assert_clean(console_errors, failed_responses)


def test_calendar_mobile_layout(mobile_page, user_factory):
    page = mobile_page
    login(page, *user_factory())
    page.goto("/food/")
    cells = page.get_by_test_id("cal-day")
    expect(cells.first).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    for i in range(cells.count()):
        box = cells.nth(i).bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, (i, box)
    for testid in ("cal-prev", "cal-next", "view-calendar", "view-list", "open-today"):
        box = page.get_by_test_id(testid).bounding_box()
        assert box["height"] >= 44, (testid, box)


def test_list_pagination(page, user_factory, api_server, console_errors, failed_responses):
    api = _user(page, user_factory, api_server)
    today = _today()
    dates = [(today - timedelta(days=n)).isoformat() for n in range(35)]
    for day in dates:
        api.day(day)
    r = httpx.post(f"{api.base}/days/{dates[0]}/entries", json={"category": "lunch", "text": "ryža, kura"},
                   headers=api.headers)
    assert r.status_code == 201
    httpx.patch(f"{api.base}/days/{dates[0]}", json={"stool": 4, "gas": 6}, headers=api.headers)

    page.goto("/food/")
    page.get_by_test_id("view-list").click()
    page.wait_for_url("**/food/list/")
    rows = page.get_by_test_id("list-day")
    expect(rows).to_have_count(30)
    assert [rows.nth(i).get_attribute("data-date") for i in range(30)] == dates[:30]
    expect(rows.first.get_by_test_id("list-digestion")).to_have_text("4/6")
    expect(rows.first.get_by_test_id("list-preview")).to_have_text("ryža, kura")

    page.get_by_test_id("list-next-page").click()
    page.wait_for_url("**/food/list/?page=2")
    expect(rows).to_have_count(5)
    assert [rows.nth(i).get_attribute("data-date") for i in range(5)] == dates[30:]
    expect(page.get_by_test_id("list-next-page")).to_have_count(0)

    rows.first.click()
    page.wait_for_url(f"**/food/day/{dates[30]}/")
    _assert_clean(console_errors, failed_responses)
