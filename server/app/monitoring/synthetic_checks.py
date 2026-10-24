import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.monitoring.models import MonitoringCheckResult, MonitoringTarget

logger = logging.getLogger("adhd.monitoring")

_CSRF_INPUT_RE = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')


async def record_check_result(
    db: AsyncSession, target: MonitoringTarget, success: bool, error_detail: str | None = None
) -> MonitoringCheckResult:
    result = MonitoringCheckResult(target=target, success=success, error_detail=error_detail if not success else None)
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


async def get_consecutive_failures(db: AsyncSession, target: MonitoringTarget, limit: int = 50) -> int:
    """Counts back from the most recent check for `target` until the first success
    (or the run of checks ends), per data-model.md's derived-not-stored escalation note."""
    stmt = (
        select(MonitoringCheckResult.success)
        .where(MonitoringCheckResult.target == target)
        .order_by(MonitoringCheckResult.checked_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    count = 0
    for success in rows:
        if success:
            break
        count += 1
    return count


async def _warn_and_maybe_escalate(db: AsyncSession, target: MonitoringTarget, success: bool, detail: str | None) -> None:
    """FR-008 (plain failure warning) + FR-008a (escalation at N consecutive failures).
    Both are surfaced as log lines here — this is the channel US5's separate `logs/api.log`
    makes independently observable to an operator, per contracts/monitoring-status.md."""
    if not success:
        logger.warning("monitoring check failed: target=%s detail=%s", target.value, detail)

    settings = get_settings()
    n = settings.monitoring_escalation_threshold
    consecutive = await get_consecutive_failures(db, target)
    if consecutive == n:
        logger.error(
            "monitoring ESCALATION: target=%s failed %d consecutive checks (threshold=%d)",
            target.value, consecutive, n,
        )


async def check_api_login(db: AsyncSession, transport: httpx.AsyncBaseTransport | None = None) -> MonitoringCheckResult:
    """FR-006: authenticate against the API using the monitoring account.
    `transport` is a test seam (see tests/monitoring/test_synthetic_checks.py) — production
    callers omit it and httpx dials the real network."""
    settings = get_settings()
    success, detail = False, None
    try:
        async with httpx.AsyncClient(base_url=settings.monitoring_api_base_url, timeout=10.0, transport=transport) as client:
            r = await client.post(
                "/api/v1/auth/login",
                json={"email": settings.monitoring_account_email, "password": settings.monitoring_account_password},
            )
        if r.status_code == 200 and "access_token" in r.json():
            success = True
        else:
            detail = f"login failed: HTTP {r.status_code}"
    except httpx.HTTPError as exc:
        detail = f"request error: {exc}"

    result = await record_check_result(db, MonitoringTarget.api, success, detail)
    await _warn_and_maybe_escalate(db, MonitoringTarget.api, success, detail)
    return result


async def check_web_console_login(
    db: AsyncSession, transport: httpx.AsyncBaseTransport | None = None
) -> MonitoringCheckResult:
    """FR-005: log into the web console using the monitoring account, then confirm the
    dashboard renders the expected (seeded) history data rather than an error or the
    "no data yet" state — catches a repeat of the US1 bug, not just a down login page.
    `transport` is a test seam, see check_api_login."""
    settings = get_settings()
    success, detail = False, None
    try:
        async with httpx.AsyncClient(
            base_url=settings.monitoring_web_console_base_url, timeout=10.0, follow_redirects=True, transport=transport
        ) as client:
            login_page = await client.get("/login/")
            csrf_match = _CSRF_INPUT_RE.search(login_page.text)
            if not csrf_match:
                detail = "could not locate CSRF token on login page"
            else:
                r = await client.post(
                    "/login/",
                    data={
                        "email": settings.monitoring_account_email,
                        "password": settings.monitoring_account_password,
                        "csrfmiddlewaretoken": csrf_match.group(1),
                    },
                )
                if r.status_code != 200 or str(r.url).rstrip("/").endswith("/login"):
                    detail = f"login did not reach the dashboard: HTTP {r.status_code} url={r.url}"
                elif 'class="alert alert-error"' in r.text:
                    # Note: base.html's <style> block always defines the .alert-error CSS
                    # class, so checking for the bare substring "alert-error" would always
                    # match — this checks for the actual rendered error <div>, not the CSS rule.
                    detail = "dashboard rendered with an error alert"
                elif "Zatiaľ nemáte žiadne dáta." in r.text:
                    detail = "expected data missing: dashboard shows the empty state"
                else:
                    success = True
    except httpx.HTTPError as exc:
        detail = f"request error: {exc}"

    result = await record_check_result(db, MonitoringTarget.web_console, success, detail)
    await _warn_and_maybe_escalate(db, MonitoringTarget.web_console, success, detail)
    return result
