"""E2E harness: starts the real FastAPI server and Django web console against throwaway
SQLite databases and drives them with Playwright. Selectors must use data-testid only."""
import hashlib
import os
import secrets
import signal
import socket
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
VENV = os.environ.get("VENV_NAME", ".venv")
SERVER_DIR = ROOT / "server"
WEB_DIR = ROOT / "web_app"
STARTUP_TIMEOUT = 20.0
TEST_PASSWORD = "e2e-password-123"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(url: str, proc: subprocess.Popen, log_path: Path) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        try:
            if httpx.get(url, timeout=1.0).status_code < 500:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"{url} did not come up in {STARTUP_TIMEOUT}s\n--- {log_path.name} ---\n{log_path.read_text()}")


def _stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    # Each server runs in its own process group, so children die with it too.
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


# Server logs are printed in the terminal summary when any test failed (fixture teardown output is captured).
_LOG_PATHS: list[Path] = []


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if exitstatus == 0:
        return
    for path in _LOG_PATHS:
        if path.exists():
            terminalreporter.write_sep("-", path.name)
            terminalreporter.write(path.read_text())


def _start(cmd: list[str], cwd: Path, env: dict, log_path: Path) -> subprocess.Popen:
    _LOG_PATHS.append(log_path)
    log = open(log_path, "w")
    return subprocess.Popen(
        cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
    )


@pytest.fixture(scope="session")
def api_env(tmp_path_factory) -> dict:
    """Environment of the API server; also used to run server CLI scripts against the same DB."""
    tmp = tmp_path_factory.mktemp("api")
    return {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp / 'api.db'}",
        "SECRET_KEY": "e2e-test-secret-key",
        "REGISTRATION_MODE": "invite",
        "ENVIRONMENT": "test",
        "E2E_API_DIR": str(tmp),
    }


@pytest.fixture(scope="session")
def api_db_path(api_env) -> Path:
    return Path(api_env["E2E_API_DIR"]) / "api.db"


@pytest.fixture(scope="session")
def api_server(api_env):
    tmp = Path(api_env["E2E_API_DIR"])
    subprocess.run(
        [str(SERVER_DIR / VENV / "bin" / "alembic"), "upgrade", "head"],
        cwd=SERVER_DIR, env=api_env, check=True, capture_output=True,
    )
    port = _free_port()
    log_path = tmp / "api.log"
    proc = _start(
        [str(SERVER_DIR / VENV / "bin" / "uvicorn"), "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        SERVER_DIR, api_env, log_path,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_for(f"{url}/api/v1/health", proc, log_path)
        yield url
    finally:
        _stop(proc)


@pytest.fixture(scope="session")
def web_server(api_server, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("web")
    env = {
        **os.environ,
        "FASTAPI_URL": api_server,
        "DJANGO_DEBUG": "true",
        "DJANGO_SQLITE_PATH": str(tmp / "web.sqlite3"),
    }
    env.pop("DJANGO_DATABASE_URL", None)
    python = str(WEB_DIR / VENV / "bin" / "python")
    subprocess.run([python, "manage.py", "migrate", "-v", "0"], cwd=WEB_DIR, env=env, check=True, capture_output=True)
    port = _free_port()
    log_path = tmp / "web.log"
    proc = _start(
        [python, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        WEB_DIR, env, log_path,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_for(f"{url}/login/", proc, log_path)
        yield url
    finally:
        _stop(proc)


@pytest.fixture(scope="session")
def base_url(web_server):
    """Lets Playwright resolve relative URLs (page.goto("/food/")) against the web console."""
    return web_server


def create_invitation_in_db(db_path: Path, days: int = 7) -> str:
    """Inserts an invitation row directly (same format as app.services.invitation_service) and returns the token."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO invitations (id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), hashlib.sha256(token.encode()).hexdigest(),
             now.strftime(fmt), (now + timedelta(days=days)).strftime(fmt)),
        )
    return token


@pytest.fixture
def user_factory(api_server, api_db_path):
    """Creates users the same way as production: through a one-time invitation (REGISTRATION_MODE=invite)."""
    def create() -> tuple[str, str]:
        email = f"e2e-{uuid.uuid4().hex[:12]}@example.com"
        token = create_invitation_in_db(api_db_path)
        r = httpx.post(
            f"{api_server}/api/v1/auth/register",
            json={"email": email, "password": TEST_PASSWORD, "invite_token": token},
        )
        assert r.status_code in (200, 201), r.text
        return email, TEST_PASSWORD

    return create


def login(page, email: str, password: str) -> None:
    page.goto("/login/")
    page.get_by_test_id("login-email").fill(email)
    page.get_by_test_id("login-password").fill(password)
    page.get_by_test_id("login-submit").click()
    page.wait_for_url(lambda url: "/login/" not in url)


@pytest.fixture
def console_errors(page):
    """Collects JS errors and console.error messages of `page`."""
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    return errors


@pytest.fixture
def logged_in_page(page, user_factory):
    email, password = user_factory()
    login(page, email, password)
    return page


@pytest.fixture
def mobile_page(browser, base_url):
    context = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, base_url=base_url)
    page = context.new_page()
    yield page
    context.close()
