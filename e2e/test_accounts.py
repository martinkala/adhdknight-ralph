"""food-002: invite-only registration, change password and account deletion through the web console."""
import re
import subprocess
import uuid
from urllib.parse import urlparse

import httpx
from playwright.sync_api import expect

from conftest import SERVER_DIR, TEST_PASSWORD, VENV, login


def _invite_link_via_cli(api_env) -> str:
    out = subprocess.run(
        [str(SERVER_DIR / VENV / "bin" / "python"), "scripts/create_invitation.py", "--note", "e2e"],
        cwd=SERVER_DIR, env=api_env, check=True, capture_output=True, text=True,
    ).stdout
    match = re.search(r"^(http\S+/register/\?invite=\S+)$", out, re.MULTILINE)
    assert match, out
    parsed = urlparse(match.group(1))
    return f"{parsed.path}?{parsed.query}"


def test_register_requires_invitation(page, api_server):
    page.goto("/register/")
    expect(page.get_by_test_id("invite-required")).to_be_visible()
    expect(page.get_by_test_id("register-email")).to_have_count(0)
    r = httpx.post(f"{api_server}/api/v1/auth/register",
                   json={"email": "no-invite@example.com", "password": TEST_PASSWORD})
    assert r.status_code == 403 and r.json() == {"detail": "invite_required"}


def test_invitation_registration_and_login(page, api_env, api_server, base_url):
    link = _invite_link_via_cli(api_env)
    email = f"e2e-invite-{uuid.uuid4().hex[:10]}@example.com"

    page.goto(link)
    page.get_by_test_id("register-email").fill(email)
    page.get_by_test_id("register-password").fill(TEST_PASSWORD)
    page.get_by_test_id("register-submit").click()
    expect(page.get_by_test_id("register-success")).to_be_visible()

    login(page, email, TEST_PASSWORD)
    expect(page).to_have_url(f"{base_url}/")

    # The same invitation cannot be used twice.
    page.goto("/logout/")
    page.goto(link)
    page.get_by_test_id("register-email").fill(f"second-{email}")
    page.get_by_test_id("register-password").fill(TEST_PASSWORD)
    page.get_by_test_id("register-submit").click()
    expect(page.get_by_test_id("register-error")).to_contain_text("Pozvánka je neplatná")


def test_change_password_and_delete_account(page, user_factory, api_server):
    email, password = user_factory()
    login(page, email, password)

    page.goto("/account/")
    form = page.get_by_test_id("change-password-form")
    form.get_by_test_id("old-password").fill(password)
    form.get_by_test_id("new-password").fill("changed-password-1")
    form.get_by_test_id("change-password-submit").click()
    expect(page.get_by_test_id("account-message")).to_contain_text("Heslo bolo zmenené.")
    assert httpx.post(f"{api_server}/api/v1/auth/login",
                      json={"email": email, "password": password}).status_code == 401

    section = page.get_by_test_id("delete-account")
    expect(section).to_contain_text("ADHD aj Food")
    section.get_by_test_id("delete-account-password").fill("changed-password-1")
    section.get_by_test_id("delete-account-confirm").check()
    section.get_by_test_id("delete-account-submit").click()
    expect(page.get_by_test_id("account-deleted")).to_be_visible()

    page.goto("/account/")
    expect(page.get_by_test_id("login-email")).to_be_visible()
    assert httpx.post(f"{api_server}/api/v1/auth/login",
                      json={"email": email, "password": "changed-password-1"}).status_code == 401
