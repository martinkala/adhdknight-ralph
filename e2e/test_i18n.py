"""food-010: language switch on the account page and on login, smoke test of the food UI in cs and en."""
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from conftest import login, set_user_language

NAV = {"sk": ("Účet", "Denník"), "cs": ("Účet", "Deník"), "en": ("Account", "Diary")}
BREAKFAST = {"sk": "Raňajky", "cs": "Snídaně", "en": "Breakfast"}


def _yesterday() -> str:
    return (datetime.now(ZoneInfo("Europe/Bratislava")).date() - timedelta(days=1)).isoformat()


def _settled(page) -> None:
    page.wait_for_function("!document.querySelector('.htmx-request, .htmx-swapping, .htmx-settling, .htmx-added')")


def test_switch_to_en_survives_logout(page, user_factory, api_server):
    email, password = user_factory()
    set_user_language(api_server, email, password, "sk")  # independent of E2E_LANGUAGE
    login(page, email, password)
    expect(page.locator("html")).to_have_attribute("lang", "sk")

    page.get_by_test_id("nav-account").click()
    page.get_by_test_id("language-select").select_option("en")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    expect(page.get_by_test_id("account-message")).to_have_text("The language was changed.")
    expect(page.get_by_test_id("language-select")).to_have_value("en")

    page.goto("/food/")
    expect(page.get_by_test_id("nav-account")).to_have_text("Account")
    expect(page.get_by_test_id("nav-food-home")).to_have_text("Diary")
    page.get_by_test_id("open-today").click()
    expect(page.get_by_test_id("section-breakfast").locator("h3")).to_have_text("Breakfast")

    page.get_by_test_id("nav-logout").click()
    page.wait_for_url(re.compile(r"/login/"))
    # The cookie keeps the login page in English, the account brings it back after login.
    expect(page.locator("html")).to_have_attribute("lang", "en")
    page.context.clear_cookies()
    login(page, email, password)
    page.goto("/food/")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    expect(page.get_by_test_id("nav-account")).to_have_text("Account")


def test_login_page_language_switch(page):
    page.goto("/login/")
    expect(page.locator("html")).to_have_attribute("lang", "sk")
    page.get_by_test_id("lang-cs").click()
    expect(page.locator("html")).to_have_attribute("lang", "cs")
    expect(page.get_by_test_id("login-submit")).to_have_text("Přihlásit se")
    expect(page.get_by_test_id("lang-cs")).to_have_attribute("aria-pressed", "true")
    page.goto("/register/")
    expect(page.locator("html")).to_have_attribute("lang", "cs")
    page.get_by_test_id("lang-en").click()
    expect(page).to_have_url(re.compile(r"/register/$"))
    expect(page.locator("html")).to_have_attribute("lang", "en")


@pytest.mark.parametrize("language", ["cs", "en"])
def test_food_smoke_in_language(language, mobile_page, user_factory, api_server):
    """Main food flows by data-testid in another language, on a 360 px wide phone."""
    page = mobile_page
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    email, password = user_factory()
    set_user_language(api_server, email, password, language)
    login(page, email, password)

    page.goto("/food/")
    expect(page.locator("html")).to_have_attribute("lang", language)
    expect(page.get_by_test_id("calendar")).to_be_visible()
    page.get_by_test_id("new-day-date").fill(_yesterday())
    page.get_by_test_id("new-day-submit").click()
    page.wait_for_url(f"**/food/day/{_yesterday()}/")
    expect(page.get_by_test_id("section-breakfast").locator("h3")).to_have_text(BREAKFAST[language])

    field = page.get_by_test_id("add-breakfast")
    field.fill("2 toasty, 0,5 l kofola")
    field.press("Enter")
    rows = page.get_by_test_id("section-breakfast").get_by_test_id("entry")
    expect(rows).to_have_count(2)
    expect(rows.nth(0).get_by_test_id("entry-qty")).to_have_text("2×")
    expect(rows.nth(1).get_by_test_id("entry-qty")).to_have_text("0,5 l" if language == "cs" else "0.5 l")
    _settled(page)

    page.get_by_test_id("stool-3").click()
    expect(page.get_by_test_id("stool-3")).to_have_attribute("aria-pressed", "true")
    page.get_by_test_id("add-bp").fill("130/85 72")
    page.get_by_test_id("add-bp").press("Enter")
    expect(page.get_by_test_id("bp-row")).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth") <= 360

    for path, testid in (("/food/list/", "list-day"), ("/food/export/", "export-form"),
                         ("/food/settings/meds/", "meds-dictionary"), ("/account/", "language-select")):
        page.goto(path)
        expect(page.get_by_test_id(testid).first).to_be_visible()
        expect(page.locator("html")).to_have_attribute("lang", language)
        assert page.evaluate("document.documentElement.scrollWidth") <= 360
    assert errors == []
