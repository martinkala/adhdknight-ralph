# Quickstart: Validating This Feature

## Prerequisites

- Local dev environment for both `server/` (FastAPI) and `web_app/` (Django) running per their existing READMEs.
- A test user with existing history data (for User Story 1) and a second, fresh user with none (for the "no data yet" state).

## User Story 1 — Dashboard shows data

1. Log in to the web console as the user with existing history.
2. Open the dashboard.
3. **Expected**: last 30 days of history render (not blank).
4. Log in as the fresh user with no history.
5. **Expected**: an explicit "no data yet" message, not a blank page.
6. Manually expire/corrupt the session token, then load the dashboard.
7. **Expected**: redirect to login, not a broken page.

## User Story 2 — Synthetic monitoring

1. Configure the monitoring account and check interval (see `contracts/monitoring-status.md` and `data-model.md#MonitoringCheckResult`).
2. Trigger a check manually (or wait one interval).
3. Call `GET /internal/monitoring/status` — confirm `last_web_console_check` and `last_api_check` are populated with `success: true`.
4. Temporarily break the monitoring account's credentials or point the check at a down endpoint; trigger a check.
5. **Expected**: `success: false` with `error_detail` populated, and a warning surfaced per FR-008.

## User Story 3 — Integrity monitoring

1. Capture an initial `IntegritySnapshot` (baseline).
2. Seed enough new users (or new data rows for one user) to exceed the configured threshold.
3. Trigger the next integrity check.
4. Call `GET /internal/monitoring/status` — confirm `recent_warnings` contains the expected `user_count_growth` or `user_data_growth` entry with correct `previous_value`/`current_value`/`threshold`.
5. Repeat with growth under threshold — confirm no warning is added.

## User Story 4 — Deployment

1. Run the deployment process (Ansible playbook, per `research.md#4`) against a clean target (or a VM/container standing in for one).
2. **Expected**: only `adhd-api` and `adhd-web` systemd services are installed/running; production `.env` values are present on the server but never appear in the git history.
3. Re-run the same playbook.
4. **Expected**: no changes reported the second time (idempotent).

## User Story 5 — Separate log files

1. Trigger a request against the web console; trigger a request against the API.
2. Inspect the web console's log file — confirm it contains only that request's entry (and other console entries), no API entries.
3. Inspect the API's log file — confirm the reverse.
