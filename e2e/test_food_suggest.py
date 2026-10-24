"""food-006: autocomplete on the day screen: search by the last part without quantity, choosing adds
a single item right away or completes a longer input, keyboard choice, inline edit, user isolation."""
import httpx
from playwright.sync_api import expect

from conftest import login
from test_food_entries import _api_token, _assert_clean, _days_ago, _settled


def _seed(api_server, email, password, items_by_day: dict[int, list[tuple[str, str]]]) -> None:
    """Creates past days with entries through the API: {days_ago: [(category, text), ...]}."""
    headers = {"Authorization": f"Bearer {_api_token(api_server, email, password)}"}
    for n, items in items_by_day.items():
        date = _days_ago(n)
        assert httpx.post(f"{api_server}/api/v1/food/days", json={"date": date}, headers=headers).status_code == 201
        for category, text in items:
            r = httpx.post(f"{api_server}/api/v1/food/days/{date}/entries",
                           json={"category": category, "text": text}, headers=headers)
            assert r.status_code == 201, r.text


def _user_with_history(page, user_factory, api_server, items_by_day) -> tuple[str, str]:
    email, password = user_factory()
    _seed(api_server, email, password, items_by_day)
    login(page, email, password)
    return email, password


def _open_new_day(page, n: int) -> None:
    date = _days_ago(n)
    page.goto("/food/")
    page.get_by_test_id("new-day-date").fill(date)
    page.get_by_test_id("new-day-submit").click()
    page.wait_for_url(f"**/food/day/{date}/")


HISTORY = {10: [("breakfast", "toasty, tuniak"), ("lunch", "Ryža")], 9: [("dinner", "toasty")],
           8: [("breakfast", "toasty, kakao"), ("medication", "emanera")]}


def _suggestions(page, category):
    return page.get_by_test_id("section-" + category).get_by_test_id("suggestion")


def test_choose_suggestion_adds_entry(page, user_factory, api_server, console_errors, failed_responses):
    _user_with_history(page, user_factory, api_server, HISTORY)
    _open_new_day(page, 1)
    field = page.get_by_test_id("add-breakfast")
    field.click()
    field.press_sequentially("to")
    options = _suggestions(page, "breakfast")
    expect(options).to_have_text(["toasty"])
    expect(page.get_by_test_id("section-breakfast").get_by_test_id("suggestions")).to_have_attribute("role", "listbox")
    options.first.click()
    rows = page.get_by_test_id("section-breakfast").get_by_test_id("entry")
    expect(rows).to_have_count(1)
    expect(rows.first.get_by_test_id("entry-text")).to_have_text("toasty")
    expect(field).to_be_focused()
    expect(field).to_have_value("")
    expect(_suggestions(page, "breakfast")).to_have_count(0)
    _assert_clean(console_errors, failed_responses)


def test_choose_keeps_quantity(page, user_factory, api_server, console_errors, failed_responses):
    _user_with_history(page, user_factory, api_server, HISTORY)
    _open_new_day(page, 1)
    field = page.get_by_test_id("add-lunch")
    field.click()
    field.press_sequentially("2 to")
    options = _suggestions(page, "lunch")
    expect(options.first).to_have_text("toasty")
    options.first.click()
    rows = page.get_by_test_id("section-lunch").get_by_test_id("entry")
    expect(rows).to_have_count(1)
    expect(rows.first.get_by_test_id("entry-qty")).to_have_text("2×")
    expect(rows.first.get_by_test_id("entry-text")).to_have_text("toasty")
    _assert_clean(console_errors, failed_responses)


def test_choose_in_longer_input_only_completes(page, user_factory, api_server, console_errors, failed_responses):
    _user_with_history(page, user_factory, api_server, HISTORY)
    _open_new_day(page, 1)
    field = page.get_by_test_id("add-dinner")
    field.click()
    field.press_sequentially("kafe, to")
    options = _suggestions(page, "dinner")
    expect(options.first).to_have_text("toasty")
    options.first.click()
    expect(field).to_have_value("kafe, toasty")
    expect(field).to_be_focused()
    rows = page.get_by_test_id("section-dinner").get_by_test_id("entry")
    expect(rows).to_have_count(0)
    field.press("Enter")
    expect(rows).to_have_count(2)
    expect(rows.get_by_test_id("entry-text")).to_have_text(["kafe", "toasty"])
    _assert_clean(console_errors, failed_responses)


def test_keyboard_choice_and_escape(page, user_factory, api_server, console_errors, failed_responses):
    _user_with_history(page, user_factory, api_server, HISTORY)
    _open_new_day(page, 1)
    field = page.get_by_test_id("add-breakfast")
    field.click()
    # Focus of an empty field offers the most used items of the group.
    options = _suggestions(page, "breakfast")
    expect(options.first).to_have_text("toasty")
    field.press_sequentially("ryz")
    expect(options).to_have_text(["Ryža"])
    field.press("Escape")
    expect(options).to_have_count(0)
    expect(field).to_have_value("ryz")

    field.fill("")
    field.press_sequentially("t")
    expect(options).to_have_text(["toasty", "tuniak"])
    field.press("ArrowDown")
    expect(field).to_have_attribute("aria-activedescendant", options.first.get_attribute("id"))
    expect(options.first).to_have_attribute("aria-selected", "true")
    field.press("Enter")
    rows = page.get_by_test_id("section-breakfast").get_by_test_id("entry")
    expect(rows).to_have_count(1)
    expect(rows.first.get_by_test_id("entry-text")).to_have_text("toasty")

    # Enter without a chosen suggestion is the normal add.
    _settled(page)
    field.press_sequentially("tu")
    expect(options.first).to_have_text("tuniak")
    field.press("Enter")
    expect(rows).to_have_count(2)
    expect(rows.nth(1).get_by_test_id("entry-text")).to_have_text("tu")
    _assert_clean(console_errors, failed_responses)


def test_groups_and_inline_edit(page, user_factory, api_server, console_errors, failed_responses):
    _user_with_history(page, user_factory, api_server, HISTORY)
    _open_new_day(page, 1)
    meds = page.get_by_test_id("add-medication")
    meds.click()
    meds.press_sequentially("e")
    expect(_suggestions(page, "medication")).to_have_text(["emanera"])
    meds.press("Escape")

    field = page.get_by_test_id("add-lunch")
    field.fill("chlieb")
    field.press("Enter")
    row = page.get_by_test_id("section-lunch").get_by_test_id("entry").first
    expect(row).to_be_visible()
    _settled(page)
    row.get_by_test_id("entry-text").click()
    edit = row.get_by_test_id("entry-edit-input")
    expect(edit).to_be_focused()
    edit.fill("")
    edit.press_sequentially("kak")
    expect(row.get_by_test_id("suggestion")).to_have_text(["kakao"])
    # Esc closes the list first, the edit stays open.
    edit.press("Escape")
    expect(row.get_by_test_id("suggestion")).to_have_count(0)
    expect(edit).to_be_visible()
    edit.press_sequentially("a")
    edit.press("Backspace")
    row.get_by_test_id("suggestion").first.click()
    expect(page.get_by_test_id("section-lunch").get_by_test_id("entry-text")).to_have_text(["kakao"])
    _settled(page)
    page.reload()
    expect(page.get_by_test_id("section-lunch").get_by_test_id("entry-text")).to_have_text(["kakao"])
    _assert_clean(console_errors, failed_responses)


def test_other_user_does_not_see_suggestions(browser, base_url, user_factory, api_server):
    first = browser.new_context(base_url=base_url)
    second = browser.new_context(base_url=base_url)
    try:
        page_a = first.new_page()
        _user_with_history(page_a, user_factory, api_server, {10: [("breakfast", "tajny toast A")]})
        _open_new_day(page_a, 1)
        field_a = page_a.get_by_test_id("add-breakfast")
        field_a.click()
        field_a.press_sequentially("taj")
        expect(_suggestions(page_a, "breakfast")).to_have_text(["tajny toast A"])

        page_b = second.new_page()
        _user_with_history(page_b, user_factory, api_server, {10: [("breakfast", "toast B")]})
        _open_new_day(page_b, 1)
        field_b = page_b.get_by_test_id("add-breakfast")
        with page_b.expect_response(lambda r: "/food/suggestions/" in r.url):
            field_b.click()
        expect(_suggestions(page_b, "breakfast")).to_have_text(["toast B"])
        with page_b.expect_response(lambda r: "/food/suggestions/" in r.url and "q=taj" in r.url):
            field_b.press_sequentially("taj")
        expect(_suggestions(page_b, "breakfast")).to_have_count(0)
    finally:
        first.close()
        second.close()


def test_mobile_shows_at_most_8(mobile_page, user_factory, api_server):
    page = mobile_page
    _user_with_history(page, user_factory, api_server,
                       {10: [("breakfast", ", ".join(f"jedlo {c}" for c in "abcdefghijkl"))]})
    _open_new_day(page, 1)
    field = page.get_by_test_id("add-breakfast")
    field.click()
    field.press_sequentially("jed")
    options = _suggestions(page, "breakfast")
    expect(options).to_have_count(8)
    box = options.first.bounding_box()
    assert box["height"] >= 44
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
