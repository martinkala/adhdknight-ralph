import httpx
import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.config import get_settings
from app.monitoring.models import MonitoringCheckResult, MonitoringTarget
from app.monitoring.synthetic_checks import (
    check_api_login,
    check_web_console_login,
    get_consecutive_failures,
)


@pytest_asyncio.fixture(autouse=True)
async def _clear_monitoring_checks(db_session):
    """check_*_login commits directly (so escalation queries see prior checks within the
    same run), which bypasses conftest.py's per-test rollback — clear state explicitly so
    consecutive-failure counting isn't polluted by other tests in this file."""
    await db_session.execute(delete(MonitoringCheckResult))
    await db_session.commit()
    yield


_LOGIN_PAGE_HTML = '<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="abc123"></form>'
# Mirrors base.html's <style> block defining .alert-error as a CSS rule on every page —
# regression coverage for a bug where the check matched that CSS text as if it were a
# rendered error, failing every check even on success.
_DASHBOARD_HTML = (
    '<style>.alert-error { background: #ffebee; color: #c62828; }</style>'
    '<h2>Dashboard</h2><div class="chart-wrap"></div>'
)
_ERROR_STATE_HTML = '<div class="alert alert-error">Server nie je dostupný. Skúste neskôr.</div>'
_EMPTY_STATE_HTML = '<div class="alert alert-info">Zatiaľ nemáte žiadne dáta.</div>'


def _api_transport(status_code: int, body: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=body)
    return httpx.MockTransport(handler)


def _web_transport(dashboard_response: httpx.Response):
    """Simulates the real flow: GET the login page (for the CSRF token), POST credentials
    (Django redirects to `/` on success), then GET `/` returns `dashboard_response`."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/login/":
            return httpx.Response(200, text=_LOGIN_PAGE_HTML)
        if request.method == "POST" and request.url.path == "/login/":
            return httpx.Response(302, headers={"Location": "/"})
        if request.method == "GET" and request.url.path == "/":
            return dashboard_response
        raise AssertionError(f"unexpected request: {request.method} {request.url}")
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_successful_api_login_records_success(db_session):
    settings = get_settings()
    transport = _api_transport(200, {"access_token": "t", "refresh_token": "r", "expires_in": 900})
    result = await check_api_login(db_session, transport=transport)
    assert result.target == MonitoringTarget.api
    assert result.success is True
    assert result.error_detail is None


@pytest.mark.asyncio
async def test_failed_api_login_records_failure_with_detail(db_session):
    transport = _api_transport(401, {"detail": "Invalid credentials"})
    result = await check_api_login(db_session, transport=transport)
    assert result.target == MonitoringTarget.api
    assert result.success is False
    assert result.error_detail
    assert "401" in result.error_detail


@pytest.mark.asyncio
async def test_successful_web_console_login_with_data_records_success(db_session):
    transport = _web_transport(httpx.Response(200, text=_DASHBOARD_HTML))
    result = await check_web_console_login(db_session, transport=transport)
    assert result.target == MonitoringTarget.web_console
    assert result.success is True
    assert result.error_detail is None


@pytest.mark.asyncio
async def test_web_console_login_with_rendered_error_records_failure(db_session):
    transport = _web_transport(httpx.Response(200, text=_ERROR_STATE_HTML))
    result = await check_web_console_login(db_session, transport=transport)
    assert result.success is False
    assert "error alert" in result.error_detail


@pytest.mark.asyncio
async def test_web_console_login_with_empty_state_records_failure(db_session):
    transport = _web_transport(httpx.Response(200, text=_EMPTY_STATE_HTML))
    result = await check_web_console_login(db_session, transport=transport)
    assert result.success is False
    assert "empty state" in result.error_detail


@pytest.mark.asyncio
async def test_escalation_at_threshold_and_reset_on_success(db_session):
    settings = get_settings()
    n = settings.monitoring_escalation_threshold
    fail_transport = _api_transport(401, {"detail": "bad creds"})
    ok_transport = _api_transport(200, {"access_token": "t", "refresh_token": "r", "expires_in": 900})

    for _ in range(n):
        await check_api_login(db_session, transport=fail_transport)
    assert await get_consecutive_failures(db_session, MonitoringTarget.api) == n

    await check_api_login(db_session, transport=ok_transport)
    assert await get_consecutive_failures(db_session, MonitoringTarget.api) == 0
