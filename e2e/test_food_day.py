"""food-004: open today, add a day, day values autosave, day screen on mobile, deleting a day."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import expect

from conftest import login


def _today() -> str:
    # New users have the default timezone (constitution B4).
    return datetime.now(ZoneInfo("Europe/Bratislava")).date().isoformat()


def _days_ago(n: int) -> str:
    return (datetime.now(ZoneInfo("Europe/Bratislava")).date() - timedelta(days=n)).isoformat()


def _add_day(page, date: str) -> None:
    page.goto("/food/")
    page.get_by_test_id("new-day-date").fill(date)
    page.get_by_test_id("new-day-submit").click()
    page.wait_for_url(f"**/food/day/{date}/")


def test_today_creates_and_reopens_same_day(logged_in_page, base_url):
    page = logged_in_page
    today = _today()
    page.goto("/food/")
    page.get_by_test_id("open-today").click()
    expect(page).to_have_url(f"{base_url}/food/day/{today}/")
    expect(page.get_by_test_id("day-title")).to_have_attribute("data-date", today)

    page.goto("/food/")
    page.get_by_test_id("open-today").click()
    expect(page).to_have_url(f"{base_url}/food/day/{today}/")
    expect(page.get_by_test_id("section-breakfast")).to_be_visible()
    # Only one day exists: no neighbours to navigate to.
    expect(page.get_by_test_id("prev-day")).to_have_attribute("aria-disabled", "true")


def test_add_existing_day_shows_error(logged_in_page):
    page = logged_in_page
    date = _days_ago(3)
    _add_day(page, date)
    page.goto("/food/")
    page.get_by_test_id("new-day-date").fill(date)
    page.get_by_test_id("new-day-submit").click()
    expect(page.get_by_test_id("error-day-exists")).to_be_visible()
    page.get_by_test_id("existing-day-link").click()
    page.wait_for_url(f"**/food/day/{date}/")


def test_prev_next_navigation(logged_in_page):
    page = logged_in_page
    older, newer = _days_ago(5), _days_ago(2)
    _add_day(page, older)
    _add_day(page, newer)
    page.get_by_test_id("prev-day").click()
    page.wait_for_url(f"**/food/day/{older}/")
    page.get_by_test_id("next-day").click()
    page.wait_for_url(f"**/food/day/{newer}/")


def _click_value(page, testid: str, pressed: str) -> None:
    page.get_by_test_id(testid).click()
    expect(page.get_by_test_id(testid)).to_have_attribute("aria-pressed", pressed)
    expect(page.get_by_test_id("save-status")).not_to_be_empty()


def test_day_values_autosave_and_toggle(logged_in_page, console_errors):
    page = logged_in_page
    _add_day(page, _days_ago(1))
    _click_value(page, "sleep-2", "true")
    _click_value(page, "stool-4", "true")
    _click_value(page, "gas-6", "true")

    page.reload()
    expect(page.get_by_test_id("sleep-2")).to_have_attribute("aria-pressed", "true")
    expect(page.get_by_test_id("stool-4")).to_have_attribute("aria-pressed", "true")
    expect(page.get_by_test_id("gas-6")).to_have_attribute("aria-pressed", "true")

    # Tapping the selected value again clears it.
    _click_value(page, "sleep-2", "false")
    page.reload()
    for v in (1, 2, 3):
        expect(page.get_by_test_id(f"sleep-{v}")).to_have_attribute("aria-pressed", "false")
    expect(page.get_by_test_id("stool-4")).to_have_attribute("aria-pressed", "true")
    page.wait_for_load_state("networkidle")
    assert console_errors == []


def test_day_screen_mobile_layout(mobile_page, user_factory):
    page = mobile_page
    login(page, *user_factory())
    page.goto("/food/")
    page.get_by_test_id("open-today").click()
    page.wait_for_url(f"**/food/day/{_today()}/")
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    buttons = page.locator(".value-btn")
    assert buttons.count() == 23
    for i in range(buttons.count()):
        box = buttons.nth(i).bounding_box()
        assert box["height"] >= 44, (i, box)
    for testid in ("delete-day", "prev-day", "next-day"):
        assert page.get_by_test_id(testid).bounding_box()["height"] >= 44


def test_delete_day_cancel_and_wrong_date(logged_in_page):
    page = logged_in_page
    date = _days_ago(4)
    _add_day(page, date)

    # Cancel in step 1.
    page.get_by_test_id("delete-day").click()
    expect(page.get_by_test_id("delete-day-confirm-1")).to_be_visible()
    page.get_by_test_id("delete-day-cancel-1").click()
    expect(page.get_by_test_id("delete-day-confirm-1")).to_be_hidden()

    # Wrong date keeps the button disabled; cancel in step 2.
    page.get_by_test_id("delete-day").click()
    page.get_by_test_id("delete-day-continue").click()
    expect(page.get_by_test_id("delete-day-confirm-2")).to_be_visible()
    page.get_by_test_id("delete-day-confirm-input").fill("2000-01-01")
    expect(page.get_by_test_id("delete-day-submit")).to_be_disabled()
    page.get_by_test_id("delete-day-confirm-input").fill(date[:-1])
    expect(page.get_by_test_id("delete-day-submit")).to_be_disabled()
    page.get_by_test_id("delete-day-cancel-2").click()
    expect(page.get_by_test_id("delete-day-confirm-2")).to_be_hidden()

    page.reload()
    expect(page.get_by_test_id("day-title")).to_have_attribute("data-date", date)


def test_delete_day_two_confirmations(logged_in_page, base_url):
    page = logged_in_page
    date = _days_ago(6)
    _add_day(page, date)
    page.get_by_test_id("delete-day").click()
    expect(page.get_by_test_id("delete-day-confirm-1")).to_contain_text(str(int(date[8:])))
    page.get_by_test_id("delete-day-continue").click()
    page.get_by_test_id("delete-day-confirm-input").fill(date)
    expect(page.get_by_test_id("delete-day-submit")).to_be_enabled()
    page.get_by_test_id("delete-day-submit").click()
    # Back to the calendar month of the deleted day (food-008).
    expect(page).to_have_url(f"{base_url}/food/?month={date[:7]}")
    expect(page.get_by_test_id("flash-success")).to_be_visible()

    response = page.goto(f"/food/day/{date}/")
    assert response.status == 404
    expect(page.get_by_test_id("create-day")).to_be_visible()
