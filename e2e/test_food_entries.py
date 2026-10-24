"""food-005: quick entry of items (split, quantity chip, focus), delete, inline edit, quantity popover,
sport intensity, notes, blood pressure and weight; mobile tap targets."""
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from playwright.sync_api import expect

from conftest import login


def _days_ago(n: int) -> str:
    return (datetime.now(ZoneInfo("Europe/Bratislava")).date() - timedelta(days=n)).isoformat()


def _open_day(page, date: str) -> None:
    page.goto("/food/")
    page.get_by_test_id("new-day-date").fill(date)
    page.get_by_test_id("new-day-submit").click()
    page.wait_for_url(f"**/food/day/{date}/")


def _settled(page) -> None:
    """Waits until htmx has finished swapping and processing new content (its hx-* attributes work)."""
    page.wait_for_function("!document.querySelector('.htmx-request, .htmx-swapping, .htmx-settling, .htmx-added')")


def _add(page, category: str, text: str, expected_count: int) -> None:
    field = page.get_by_test_id(f"add-{category}")
    field.fill(text)
    field.press("Enter")
    expect(page.get_by_test_id(f"section-{category}").get_by_test_id("entry")).to_have_count(expected_count)
    _settled(page)


def _assert_clean(console_errors, failed_responses):
    assert console_errors == []
    assert failed_responses == []


def test_quick_add_splits_and_keeps_focus(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(1))
    _add(page, "breakfast", "2 toasty, kafe", 2)
    section = page.get_by_test_id("section-breakfast")
    rows = section.get_by_test_id("entry")
    expect(rows.nth(0).get_by_test_id("entry-qty")).to_have_text("2×")
    expect(rows.nth(0).get_by_test_id("entry-text")).to_have_text("toasty")
    expect(rows.nth(1).get_by_test_id("entry-qty")).to_have_count(0)
    expect(rows.nth(1).get_by_test_id("entry-text")).to_have_text("kafe")
    field = page.get_by_test_id("add-breakfast")
    expect(field).to_be_focused()
    expect(field).to_have_value("")

    # Success criterion: more items in a row only by typing + Enter.
    for i, item in enumerate(("jogurt", "200 g ovsene vlocky", "1/2 banana"), start=3):
        page.keyboard.type(item)
        page.keyboard.press("Enter")
        expect(rows).to_have_count(i)
    expect(field).to_be_focused()
    page.reload()
    expect(rows).to_have_count(5)
    expect(rows.nth(3).get_by_test_id("entry-qty")).to_have_text(re.compile(r"^200 g$"))
    _assert_clean(console_errors, failed_responses)


def test_delete_entry_without_dialog(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(2))
    _add(page, "lunch", "polievka, ryza", 2)
    page.on("dialog", lambda d: (_ for _ in ()).throw(AssertionError("unexpected dialog")))
    rows = page.get_by_test_id("section-lunch").get_by_test_id("entry")
    rows.nth(0).get_by_test_id("entry-delete").click()
    expect(rows).to_have_count(1)
    page.reload()
    expect(rows).to_have_count(1)
    expect(rows.nth(0).get_by_test_id("entry-text")).to_have_text("ryza")
    _assert_clean(console_errors, failed_responses)


def test_inline_edit_and_cancel(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(3))
    _add(page, "dinner", "chlieb", 1)
    row = page.get_by_test_id("section-dinner").get_by_test_id("entry").first

    # Esc cancels.
    row.get_by_test_id("entry-text").click()
    edit = row.get_by_test_id("entry-edit-input")
    expect(edit).to_be_focused()
    edit.fill("zle")
    edit.press("Escape")
    expect(row.get_by_test_id("entry-text")).to_have_text("chlieb")

    row.get_by_test_id("entry-text").click()
    row.get_by_test_id("entry-edit-input").fill("chlieb s maslom")
    row.get_by_test_id("entry-edit-input").press("Enter")
    expect(row.get_by_test_id("entry-text")).to_have_text("chlieb s maslom")
    _settled(page)
    page.reload()
    expect(page.get_by_test_id("section-dinner").get_by_test_id("entry-text")).to_have_text("chlieb s maslom")
    _assert_clean(console_errors, failed_responses)


def _api_token(api_server, email, password) -> str:
    r = httpx.post(f"{api_server}/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_quantity_popover_orders_by_frequency(page, user_factory, api_server, console_errors, failed_responses):
    email, password = user_factory()
    headers = {"Authorization": f"Bearer {_api_token(api_server, email, password)}"}
    for n, text in ((10, "2 toasty"), (9, "2 toasty"), (8, "3 toasty"), (7, "2 toasty")):
        date = _days_ago(n)
        assert httpx.post(f"{api_server}/api/v1/food/days", json={"date": date}, headers=headers).status_code == 201
        r = httpx.post(f"{api_server}/api/v1/food/days/{date}/entries",
                       json={"category": "breakfast", "text": text}, headers=headers)
        assert r.status_code == 201

    login(page, email, password)
    _open_day(page, _days_ago(1))
    _add(page, "breakfast", "toasty", 1)
    row = page.get_by_test_id("section-breakfast").get_by_test_id("entry").first
    row.get_by_test_id("entry-qty-add").click()
    popover = page.get_by_test_id("qty-popover")
    expect(popover).to_be_visible()
    expect(popover.get_by_test_id("qty-option")).to_have_text(["2×", "3×"])
    _settled(page)

    popover.get_by_test_id("qty-option").nth(1).click()
    expect(row.get_by_test_id("entry-qty")).to_have_text("3×")
    expect(page.get_by_test_id("qty-popover")).to_have_count(0)
    _settled(page)

    # Manual quantity, then no quantity.
    row.get_by_test_id("entry-qty").click()
    _settled(page)
    page.get_by_test_id("qty-input").fill("0,5")
    page.get_by_test_id("qty-unit").select_option("l")
    page.get_by_test_id("qty-save").click()
    expect(row.get_by_test_id("entry-qty")).to_have_text(re.compile(r"^0[.,]5 l$"))
    _settled(page)
    row.get_by_test_id("entry-qty").click()
    _settled(page)
    page.get_by_test_id("qty-none").click()
    expect(row.get_by_test_id("entry-qty")).to_have_count(0)
    page.reload()
    expect(page.get_by_test_id("section-breakfast").get_by_test_id("entry-qty-add")).to_have_count(1)
    _assert_clean(console_errors, failed_responses)


def test_sport_intensity_and_notes(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(4))
    _add(page, "sport", "eBike 60 km", 1)
    row = page.get_by_test_id("section-sport").get_by_test_id("entry").first
    expect(row.get_by_test_id("entry-text")).to_have_text("eBike 60 km")
    with page.expect_response(lambda r: r.request.method == "PATCH"):
        row.get_by_test_id("entry-intensity").select_option("3")

    note = page.get_by_test_id("add-note")
    note.fill("rano prujem, unava")
    note.press("Shift+Enter")
    note.type("vecer ok")
    note.press("Enter")
    notes = page.get_by_test_id("section-note").get_by_test_id("entry")
    expect(notes).to_have_count(1)
    _settled(page)

    page.reload()
    expect(page.get_by_test_id("section-sport").get_by_test_id("entry-intensity")).to_have_value("3")
    expect(page.get_by_test_id("section-sport").get_by_test_id("entry-text")).to_have_text("eBike 60 km")
    assert notes.first.get_by_test_id("entry-text").inner_text() == "rano prujem, unava\nvecer ok"
    notes.first.get_by_test_id("entry-delete").click()
    expect(notes).to_have_count(0)
    _assert_clean(console_errors, failed_responses)


def test_blood_pressure_and_weight(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(5))
    bp = page.get_by_test_id("add-bp")
    bp.fill("130/85 72 7:30")
    bp.press("Enter")
    rows = page.get_by_test_id("bp-row")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text("130/85")
    expect(rows.first).to_contain_text("72")
    expect(rows.first).to_contain_text("07:30")
    expect(bp).to_have_value("")
    _settled(page)

    bp.fill("145/02")
    bp.press("Enter")
    expect(page.get_by_test_id("bp-error")).to_be_visible()
    expect(rows).to_have_count(1)
    expect(bp).to_have_value("145/02")
    _settled(page)

    # Inline edit with a note.
    rows.first.get_by_test_id("bp-text").click()
    rows.first.get_by_test_id("bp-edit-note").fill("po kave")
    rows.first.get_by_test_id("bp-edit-note").press("Enter")
    expect(rows.first).to_contain_text("po kave")
    expect(page.get_by_test_id("bp-error")).to_have_count(0)
    _settled(page)

    weight = page.get_by_test_id("add-weight")
    weight.fill("80,6")
    weight.press("Enter")
    weights = page.get_by_test_id("weight-row")
    expect(weights).to_have_count(1)
    expect(weights.first).to_contain_text(re.compile(r"80[.,]6 kg"))

    page.reload()
    expect(rows.first).to_contain_text("130/85")
    expect(weights.first).to_contain_text(re.compile(r"80[.,]6 kg"))
    weights.first.get_by_test_id("weight-delete").click()
    expect(weights).to_have_count(0)
    assert console_errors == []
    assert failed_responses == []


def test_blood_pressure_today_gets_current_time(logged_in_page):
    page = logged_in_page
    page.goto("/food/")
    page.get_by_test_id("open-today").click()
    page.wait_for_url("**/food/day/*/")
    page.get_by_test_id("add-bp").fill("120/80")
    page.get_by_test_id("add-bp").press("Enter")
    expect(page.get_by_test_id("bp-row").first).to_contain_text(re.compile(r"\d{2}:\d{2}"))


def test_mobile_add_entry_and_tap_targets(mobile_page, user_factory):
    page = mobile_page
    login(page, *user_factory())
    _open_day(page, _days_ago(1))
    _add(page, "lunch", "2 knedle, gulas", 2)
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    row = page.get_by_test_id("section-lunch").get_by_test_id("entry").first
    for testid in ("entry-qty", "entry-delete"):
        box = row.get_by_test_id(testid).bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, (testid, box)
    box = page.get_by_test_id("section-lunch").get_by_test_id("entry-qty-add").bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44
    row.get_by_test_id("entry-delete").click()
    expect(page.get_by_test_id("section-lunch").get_by_test_id("entry")).to_have_count(1)
