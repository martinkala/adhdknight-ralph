import re

from playwright.sync_api import expect

from conftest import login


def test_login_and_switch_to_food(logged_in_page, base_url):
    page = logged_in_page
    expect(page).to_have_url(f"{base_url}/")
    expect(page.get_by_test_id("app-switch-adhd")).to_have_class(re.compile(r"\bactive\b"))
    page.get_by_test_id("app-switch-food").click()
    expect(page).to_have_url(f"{base_url}/food/")
    expect(page.get_by_test_id("food-home")).to_be_visible()
    expect(page.get_by_test_id("app-switch-food")).to_have_class(re.compile(r"\bactive\b"))


def test_mobile_nav_no_horizontal_scroll(mobile_page, user_factory):
    page = mobile_page
    login(page, *user_factory())
    for path in ("/", "/food/"):
        page.goto(path)
        assert page.evaluate("document.documentElement.scrollWidth") <= 360
        # Menu is collapsed behind the toggle; opening it must not cause horizontal scroll either.
        expect(page.get_by_test_id("nav-logout")).to_be_hidden()
        page.get_by_test_id("nav-toggle").click()
        expect(page.get_by_test_id("nav-logout")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth") <= 360


def test_htmx_loaded_without_console_errors(logged_in_page, console_errors):
    page = logged_in_page
    for path in ("/food/", "/"):
        page.goto(path)
        page.wait_for_load_state("networkidle")
        assert page.evaluate("typeof window.htmx") == "object"
    assert console_errors == []
