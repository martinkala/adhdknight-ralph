"""food-007: medication and supplements in one input; unknown items are classified once in a dialog,
known items go straight to their section; the dictionary page moves entries between sections."""
from playwright.sync_api import expect

from conftest import login
from test_food_entries import _assert_clean, _days_ago, _open_day, _settled


def _meds_rows(page, kind: str):
    return page.get_by_test_id(f"section-{kind}").get_by_test_id("entry")


def _meds_texts(page, kind: str):
    return _meds_rows(page, kind).get_by_test_id("entry-text")


def _add_meds(page, text: str) -> None:
    _settled(page)
    field = page.get_by_test_id("add-meds")
    field.fill(text)
    field.press("Enter")


def test_classify_once_then_known(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(2))
    _add_meds(page, "prestarium, zn")
    dialog = page.get_by_test_id("classify-dialog")
    expect(dialog).to_be_visible()
    items = dialog.get_by_test_id("classify-item")
    expect(items).to_have_count(2)
    # Nothing is stored before the answer; the text stays in the field.
    expect(_meds_rows(page, "medication")).to_have_count(0)
    expect(page.get_by_test_id("add-meds")).to_have_value("prestarium, zn")
    submit = dialog.get_by_test_id("classify-submit")
    expect(submit).to_be_disabled()
    items.nth(0).get_by_test_id("classify-medication").click()
    expect(submit).to_be_disabled()
    items.nth(1).get_by_test_id("classify-supplement").click()
    submit.click()

    expect(dialog).to_have_count(0)
    expect(_meds_texts(page, "medication")).to_have_text(["prestarium"])
    expect(_meds_texts(page, "supplement")).to_have_text(["zn"])
    field = page.get_by_test_id("add-meds")
    expect(field).to_have_value("")
    expect(field).to_be_focused()

    # Another day: known items are stored without a dialog.
    _open_day(page, _days_ago(1))
    _add_meds(page, "zn, prestarium")
    expect(_meds_texts(page, "medication")).to_have_text(["prestarium"])
    expect(_meds_texts(page, "supplement")).to_have_text(["zn"])
    expect(page.get_by_test_id("classify-dialog")).to_have_count(0)
    expect(page.get_by_test_id("add-meds")).to_have_value("")
    _assert_clean(console_errors, failed_responses)


def test_cancel_keeps_text_and_saves_nothing(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    _open_day(page, _days_ago(1))
    _add_meds(page, "emanera")
    dialog = page.get_by_test_id("classify-dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_test_id("classify-cancel").click()
    expect(page.get_by_test_id("classify-dialog")).to_have_count(0)
    field = page.get_by_test_id("add-meds")
    expect(field).to_have_value("emanera")
    expect(field).to_be_focused()
    page.reload()
    expect(_meds_rows(page, "medication")).to_have_count(0)
    expect(_meds_rows(page, "supplement")).to_have_count(0)

    # Esc closes the dialog too; asking again works.
    _add_meds(page, "emanera")
    expect(page.get_by_test_id("classify-dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_test_id("classify-dialog")).to_have_count(0)
    page.get_by_test_id("add-meds").press("Enter")
    dialog = page.get_by_test_id("classify-dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_test_id("classify-medication").click()
    dialog.get_by_test_id("classify-submit").click()
    expect(_meds_texts(page, "medication")).to_have_text(["emanera"])
    _assert_clean(console_errors, failed_responses)


def test_dictionary_change_moves_entries(logged_in_page, console_errors, failed_responses):
    page = logged_in_page
    day = _days_ago(1)
    _open_day(page, day)
    _add_meds(page, "zn")
    dialog = page.get_by_test_id("classify-dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_test_id("classify-supplement").click()
    dialog.get_by_test_id("classify-submit").click()
    expect(_meds_texts(page, "supplement")).to_have_text(["zn"])

    page.get_by_test_id("meds-dictionary-link").click()
    page.wait_for_url("**/food/settings/meds/")
    dictionary = page.get_by_test_id("meds-dictionary")
    row = dictionary.get_by_test_id("dict-item")
    expect(row).to_have_count(1)
    expect(row.get_by_test_id("dict-text")).to_contain_text("zn")
    expect(row.get_by_test_id("dict-kind-supplement")).to_have_attribute("aria-pressed", "true")
    row.get_by_test_id("dict-kind-medication").click()
    expect(page.get_by_test_id("dict-item").get_by_test_id("dict-kind-medication")).to_have_attribute("aria-pressed", "true")

    page.goto(f"/food/day/{day}/")
    expect(_meds_texts(page, "medication")).to_have_text(["zn"])
    expect(_meds_rows(page, "supplement")).to_have_count(0)

    # The move action on the entry changes the dictionary as well.
    _meds_rows(page, "medication").first.get_by_test_id("entry-move").click()
    expect(_meds_texts(page, "supplement")).to_have_text(["zn"])
    expect(_meds_rows(page, "medication")).to_have_count(0)

    page.get_by_test_id("nav-food-meds").click()
    page.wait_for_url("**/food/settings/meds/")
    _settled(page)
    page.get_by_test_id("dict-item").get_by_test_id("dict-delete").click()
    expect(page.get_by_test_id("dictionary-empty")).to_be_visible()
    _assert_clean(console_errors, failed_responses)


def test_mobile_classify_dialog(mobile_page, user_factory):
    page = mobile_page
    login(page, *user_factory())
    _open_day(page, _days_ago(1))
    _add_meds(page, "omega+fe+D, prestarium")
    dialog = page.get_by_test_id("classify-dialog")
    expect(dialog).to_be_visible()
    expect(dialog.get_by_test_id("classify-item")).to_have_count(4)
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    for testid in ("classify-medication", "classify-supplement"):
        box = dialog.get_by_test_id(testid).first.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, (testid, box)
    items = dialog.get_by_test_id("classify-item")
    for i in range(3):
        items.nth(i).get_by_test_id("classify-supplement").click()
    items.nth(3).get_by_test_id("classify-medication").click()
    dialog.get_by_test_id("classify-submit").click()
    expect(_meds_texts(page, "supplement")).to_have_text(["omega", "fe", "D"])
    expect(_meds_texts(page, "medication")).to_have_text(["prestarium"])
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    box = _meds_rows(page, "medication").first.get_by_test_id("entry-move").bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44
