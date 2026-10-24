---

description: "Task list template for feature implementation"
---

# Tasks: Web Console Fix, Application Monitoring, Deployment & Logging

**Input**: Design documents from `/specs/020-fix-web-console-monitoring/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/monitoring-status.md, quickstart.md

**Tests**: Included for User Stories 2 & 3 (new domain logic — synthetic checks, integrity thresholds) since `server/tests/` already has pytest/pytest-asyncio/httpx infrastructure to extend. Not included for User Story 1 (bug fix — reproduce manually per quickstart.md, add a regression test once root cause is confirmed) or Stories 4/5 (deployment tooling and logging config are verified via quickstart.md, not unit tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

Existing two-service layout: `server/app/` + `server/tests/` (FastAPI), `web_app/core/` + `web_app/adhd_web/` (Django), `deploy/` (systemd/nginx/scripts/ansible). See plan.md "Project Structure".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Nothing new to scaffold — both services and `deploy/` already exist. This phase is a no-op beyond confirming environments run.

- [X] T001 Confirm `server/` (FastAPI, `make` or `uvicorn app.main:app --reload`) and `web_app/` (`python manage.py runserver`) both start locally per their existing READMEs, so all following tasks can be verified as you go

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared monitoring data model that User Stories 2 & 3 both depend on. User Stories 1, 4, 5 do NOT depend on this phase and can proceed in parallel with it.

**⚠️ CRITICAL**: T002-T005 MUST complete before any Phase 4/5 (US2/US3) task starts.

- [X] T002 [P] Add `MonitoringCheckResult` SQLAlchemy model (per data-model.md) in `server/app/monitoring/models.py`
- [X] T003 [P] Add `IntegritySnapshot` and `UserDataVolumeSnapshot` SQLAlchemy models (per data-model.md) in `server/app/monitoring/models.py`
- [X] T004 [P] Add `IntegrityWarning` SQLAlchemy model (per data-model.md) in `server/app/monitoring/models.py`
- [X] T005 Generate and apply Alembic migration for the four new monitoring tables in `server/app/db/migrations/versions/` (depends on T002-T004) — `0fe796b54aed_add_monitoring_tables.py`, applied to local dev SQLite; full test suite still green (pre-existing unrelated failure in `test_future_date.py` confirmed present on master too)

**Checkpoint**: Monitoring tables exist — US2 and US3 implementation can now begin.

---

## Phase 3: User Story 1 - Dashboard shows data after login (Priority: P1) 🎯 MVP

**Goal**: Fix the web console dashboard so it renders the logged-in user's history instead of appearing blank.

**Independent Test**: Log in as a user with existing history, load `/dashboard`, confirm data renders (see quickstart.md US1).

### Diagnosis (must precede the fix)

- [X] T006 [US1] Reproduce the bug locally: log in as a user with known history data, inspect the actual response from `api_client.get_history()` in `web_app/core/api_client.py` (add temporary debug logging if needed) to confirm which failure mode from research.md §1 applies — **confirmed**: `dashboard.html`/`trend.html` embedded `history.days` directly into an inline `<script>` via `{{ history.days|default:"[]"|safe }}`, which renders Django's `str()`/repr of the Python list (single-quoted strings, `None` instead of `null`). Any day with a null `index_value` (i.e. no computed `DailyIndex` yet) produces literal `None` in the script, which is invalid JavaScript and throws, aborting the whole chart-rendering IIFE — the page renders but appears to have "no data".

### Implementation for User Story 1

- [X] T007 [US1] Fix the confirmed root cause in `web_app/core/api_client.py` and/or `web_app/core/views.py:dashboard()` so a successful API response's history data reaches the template — added `_history_context()` in `views.py` that serializes `days` via `json.dumps` (real JSON, not Python repr) and templates now embed `{{ days_json|safe }}` instead of `{{ history.days|safe }}`
- [X] T008 [US1] Update `web_app/core/views.py:dashboard()` (and `trend()`, which shares the same pattern) to treat any non-`"unauthorized"` error response distinctly from a genuinely empty history, per FR-002 — `_history_context()` returns `error_message` (mapped via `_ERROR_MESSAGES`) separately from `has_data`/`days_json`
- [X] T009 [US1] Update `web_app/core/templates/dashboard.html` to render an explicit "no data yet" state when `history` is empty but the fetch succeeded, vs. rendering nothing — added `{% elif not has_data %}` branch ("Zatiaľ nemáte žiadne dáta.") to both `dashboard.html` and `trend.html`, plus `.alert-info` style in `base.html`
- [X] T010 [US1] Add a regression test (Django test client, `web_app/core/tests/`) covering: user with data sees data, user without data sees the empty-state message, expired token redirects to login (creates `web_app/core/tests/` if it doesn't exist yet) — `web_app/core/tests/test_dashboard.py` (5 tests, verified they fail against the pre-fix code and pass against the fix)

**Checkpoint**: User Story 1 fully functional and testable independently — this alone is shippable as the MVP.

---

## Phase 4: User Story 2 - Synthetic uptime monitoring (Priority: P2)

**Goal**: A dedicated monitoring account logs into both the web console and the API on a schedule; failures and missing data surface as warnings, and repeated consecutive failures escalate.

**Independent Test**: Trigger a check manually, confirm `GET /internal/monitoring/status` reflects success; break the monitoring account's credentials, confirm the next check reflects failure, and confirm a second consecutive failure escalates (see quickstart.md US2).

### Tests for User Story 2

- [X] T011 [P] [US2] Test for successful web console synthetic login recording a `MonitoringCheckResult(success=True)` in `server/tests/monitoring/test_synthetic_checks.py`
- [X] T012 [P] [US2] Test for failed API synthetic login recording `MonitoringCheckResult(success=False, error_detail=...)` in `server/tests/monitoring/test_synthetic_checks.py`

### Implementation for User Story 2

- [X] T013 [US2] Seed/provision the dedicated monitoring account (flag or reserved-account convention per data-model.md `MonitoringAccount`) via a migration or seed script in `server/app/db/migrations/versions/` or `server/scripts/` — added `is_monitoring_account` column to `User` (`server/app/models/user.py`) + `187ee05ae8ff_...py` migration that seeds the account (credentials from `Settings.monitoring_account_email/password`) plus 3 days of seeded tracking history/index so the synthetic web-console check has real data to verify
- [X] T014 [US2] Implement the API-side synthetic login check (calls the existing `/auth` login endpoint, records `MonitoringCheckResult`) in `server/app/monitoring/synthetic_checks.py`
- [X] T015 [US2] Implement the web-console-side synthetic login check (drives the Django login form via httpx, records `MonitoringCheckResult`) in `server/app/monitoring/synthetic_checks.py` (depends on T014) — during E2E verification (see T019) found and fixed a false-positive: the initial check flagged every successful login as failed because it searched for the substring `"alert-error"`, which also matches `base.html`'s static `.alert-error { ... }` CSS rule present on every page. Fixed to match the actual rendered `class="alert alert-error"` div, with a regression test covering the CSS-only case.
- [X] T016 [US2] Implement warning surfacing on check failure (FR-008) — log a distinguishable warning-level entry (consumed by the log monitoring from US5) in `server/app/monitoring/synthetic_checks.py`
- [X] T017 [US2] Implement consecutive-failure escalation (FR-008a): after recording each `MonitoringCheckResult`, query the last N results for that target (N from config, default 2) and, if all failed, log a distinct higher-severity escalation warning in `server/app/monitoring/synthetic_checks.py` (depends on T016); add a test in `server/tests/monitoring/test_synthetic_checks.py` covering escalation at N=2 and reset-on-success
- [X] T018 [US2] Implement `GET /internal/monitoring/status` per `contracts/monitoring-status.md` (including the derived `consecutive_failures` field per FR-008a), restricted to operator/admin auth, in `server/app/api/monitoring.py` — implemented in `server/app/routers/monitoring.py` (matching this codebase's existing `app/routers/` convention rather than introducing a new `app/api/` package); auth via a shared `X-Monitoring-Key` header checked against `Settings.monitoring_api_key` (`require_monitoring_operator` in `app/dependencies.py`) — a full RBAC/admin-role system would be disproportionate infra per research.md's stated reasoning for this single-server deployment. Built the response shape including the US3 `last_integrity_snapshot`/`recent_warnings` fields now too (T026) since the endpoint is one small file.
- [X] T019 [US2] Wire a systemd timer + service unit (per research.md §2) that invokes the synthetic checks on a configurable interval in `deploy/systemd/adhd-monitoring.timer` and `deploy/systemd/adhd-monitoring.service` — oneshot service runs `server/scripts/run_monitoring_checks.py` (also runs the US3 integrity check in the same invocation); timer default 15min matches `Settings.monitoring_check_interval_minutes`'s default. End-to-end verified locally: ran both real servers, ran the script against them, confirmed `GET /internal/monitoring/status` reflected successful checks and a captured integrity snapshot. This also caught and fixed a real bug in the check itself (see T014-T017 notes below) before it ever reached deploy.

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Integrity / intrusion-detection monitoring (Priority: P2)

**Goal**: Detect anomalous user-count or per-user data-volume growth against a configurable threshold, comparing each check to the prior snapshot.

**Independent Test**: Seed growth exceeding threshold between two snapshots, confirm a warning appears in `recent_warnings`; seed growth under threshold, confirm no warning (see quickstart.md US3).

### Tests for User Story 3

- [X] T020 [P] [US3] Test that user-count growth exceeding threshold raises an `IntegrityWarning(metric=user_count_growth)` in `server/tests/monitoring/test_integrity_checks.py`
- [X] T021 [P] [US3] Test that per-user data growth exceeding threshold raises an `IntegrityWarning(metric=user_data_growth)` identifying the correct user in `server/tests/monitoring/test_integrity_checks.py`
- [X] T022 [P] [US3] Test that growth within threshold raises no warning, and that the very first check (no prior snapshot) does not error (edge case from spec.md) in `server/tests/monitoring/test_integrity_checks.py`

### Implementation for User Story 3

- [X] T023 [US3] Implement snapshot capture (total user count + per-user data count → `IntegritySnapshot` + `UserDataVolumeSnapshot`) in `server/app/monitoring/integrity_checks.py` — counts exclude `is_monitoring_account` users so the monitoring account's own seeded activity never looks like anomalous growth
- [X] T024 [US3] Implement threshold comparison against the most recent prior snapshot, raising `IntegrityWarning` rows on breach, in `server/app/monitoring/integrity_checks.py` (depends on T023)
- [X] T025 [US3] Add configurable thresholds (user-count growth, per-user data growth, and the FR-008a escalation N) to `server/app/config.py` / settings, sourced from environment per FR-010/FR-012/FR-008a
- [X] T026 [US3] Extend `GET /internal/monitoring/status` to include `last_integrity_snapshot` and `recent_warnings` per `contracts/monitoring-status.md` in `server/app/api/monitoring.py` (depends on T018, T023, T024) — done as part of T018, see note there
- [X] T027 [US3] Add integrity snapshot capture to the same systemd timer cadence as US2 (or a separate timer if a different interval is desired) in `deploy/systemd/adhd-monitoring.service` (depends on T019, T023) — `run_monitoring_checks.py` calls `capture_and_compare()` in the same run as the synthetic checks

**Checkpoint**: All monitoring (US2 + US3) independently functional alongside the US1 fix.

---

## Phase 6: User Story 4 - Minimal, reproducible deployment (Priority: P3)

**Goal**: Deploy only the API and web console to a server, idempotently, without committing production secrets.

**Independent Test**: Run the playbook against a clean target, confirm only `adhd-api`/`adhd-web` services exist; re-run, confirm no changes (see quickstart.md US4).

### Implementation for User Story 4

- [X] T028 [P] [US4] Create Ansible inventory + `deploy/ansible/site.yml` playbook provisioning the `adhd-api` and `adhd-web` systemd services from the existing unit files in `deploy/systemd/` — code arrives via rsync (`ansible.posix.synchronize`) of committed content, not `git clone`/`pull` on the server, matching `deploy/scripts/push-deploy.sh`'s "no GitHub credentials on the server" principle. Package/PostgreSQL/certbot provisioning stays in the existing `install.sh` (one-time setup); this playbook is the repeatable per-deploy path (code sync, venvs, migrations, systemd units).
- [X] T029 [P] [US4] Create Ansible role/tasks for nginx config deployment from `deploy/nginx/` in `deploy/ansible/roles/nginx/`
- [X] T030 [US4] Set up an Ansible Vault–encrypted variables file (stored outside this repository, referenced but not committed) for production `.env` values, templated onto the server during the playbook run, in `deploy/ansible/group_vars/` — `group_vars/all/vault.yml.example` documents the expected variable names with placeholder values only (same pattern as `.env.example`); the real, encrypted file lives outside the repo and is passed via `-e @path --ask-vault-pass` per `deploy/ansible/README.md`
- [X] T031 [US4] Document the deployment process (prerequisites, how to run the playbook, how the Vault file is managed/rotated) in `deploy/ansible/README.md`
- [X] T032 [US4] Add an automated secret-scan safeguard (FR-016a): install `detect-secrets` (per research.md §7) as a pre-commit hook, generate the baseline, and document it in `deploy/ansible/README.md` — add `.pre-commit-config.yaml` at the repository root and a `.secrets.baseline` file — baseline generated against the whole repo (28 pre-existing findings reviewed: all test fixtures, doc examples, the existing `django-insecure-...` dev-only default key, and Alembic revision-hash hex strings misidentified as high-entropy secrets — none are real production secrets); verified the hook passes clean against the baseline and correctly blocks a newly-introduced fake secret in a scratch file
- [X] T033 [US4] Verify idempotency by running the playbook twice against a test target and confirming the second run reports no changes (manual validation per quickstart.md US4, no automated test) — verified `ansible-playbook site.yml --syntax-check` passes and the `.env` Jinja templates render correctly with placeholder vault values; did **not** run the playbook against a real/staging target (none available in this environment, and `become: true` tasks would alter real system state) — this step still needs a human to run against an actual server per the README before first production use

**Checkpoint**: Deployment reproducible independent of the other stories.

---

## Phase 7: User Story 5 - Separate log files for web console and API (Priority: P3)

**Goal**: Web console and API write to separate log files so each can be monitored independently.

**Independent Test**: Trigger activity in each component, confirm entries land only in that component's file (see quickstart.md US5).

### Implementation for User Story 5

- [X] T034 [P] [US5] Add a dedicated `RotatingFileHandler` (e.g. `logs/api.log`) to the FastAPI logging setup in `server/app/main.py` and `server/app/middleware/logging.py` — added `server/app/logging_config.py::configure_api_logging()` (attaches the handler to the `adhd` parent logger, so both `adhd.request` in `middleware/logging.py` and `adhd.monitoring` reach it via propagation with no change needed to `middleware/logging.py` itself), called from `main.py` at import time
- [X] T035 [P] [US5] Add a dedicated `RotatingFileHandler` (e.g. `logs/web.log`) via Django's `LOGGING` config in `web_app/adhd_web/settings.py`
- [X] T036 [US5] Confirm the warnings emitted in T016/T017 (US2 synthetic check failures and escalations) land in `logs/api.log` so operators monitoring that file see monitoring failures too (depends on T016, T017, T034) — `run_monitoring_checks.py` calls the same `configure_api_logging()` (it never imports `app.main`, so this call was necessary); verified manually that both `adhd.request` and `adhd.monitoring` lines land in `logs/api.log` and Django's lines land only in `logs/web.log`, with no cross-contamination

**Checkpoint**: All five user stories independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories.

- [X] T037 [P] Run all of `quickstart.md`'s validation steps end-to-end against a local/staging environment — US1: covered by the 5 regression tests in `web_app/core/tests/test_dashboard.py` plus manual confirmation the pre-fix code fails them; US2/US3: ran both real servers locally, ran `scripts/run_monitoring_checks.py` against them, confirmed `GET /internal/monitoring/status` reflects successful checks + an integrity snapshot, and confirmed a real bug (CSS-selector false positive) along the way (see T015); US5: manually confirmed `logs/api.log`/`logs/web.log` isolation with no cross-contamination; US4: syntax-checked and template-rendered only (no real/staging target available in this environment — see T033)
- [X] T038 Update `server/README.md` and `web_app/README.md` with the new monitoring endpoint, log file locations, and (link to) the Ansible deployment doc — `web_app/README.md` created (none existed before)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: No dependency on Setup; BLOCKS Phase 4 (US2) and Phase 5 (US3) only — does NOT block US1, US4, US5
- **US1 (Phase 3)**: Independent — can start immediately
- **US2 (Phase 4)**: Depends on Foundational (Phase 2)
- **US3 (Phase 5)**: Depends on Foundational (Phase 2); status-endpoint task T026 depends on US2's T018
- **US4 (Phase 6)**: Independent — can start immediately
- **US5 (Phase 7)**: Independent — can start immediately; T036 depends on US2's T016/T017
- **Polish (Phase 8)**: Depends on all desired stories being complete

### Parallel Opportunities

- Phase 2: T002, T003, T004 in parallel (different model classes, same file — coordinate if working simultaneously)
- US1, US4, US5 can all start immediately alongside Phase 2, with no cross-dependencies
- Within US2: T011, T012 in parallel; within US3: T020, T021, T022 in parallel
- US4's T028, T029 in parallel (different files)
- US5's T034, T035 in parallel (different services' files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3 (US1) — the dashboard fix is independently shippable and addresses the most urgent reported bug.
2. Deploy/demo.

### Incremental Delivery

1. US1 (dashboard fix) → ship immediately, no dependency on anything else.
2. Foundational (Phase 2) → US2 (uptime monitoring, including escalation) → ship.
3. US3 (integrity monitoring) → ship (builds on US2's status endpoint).
4. US5 (log separation) → ship (makes US2/US3 warnings independently observable).
5. US4 (deployment automation + secret-scan safeguard) → ship last; operational tooling, not user-facing.

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
