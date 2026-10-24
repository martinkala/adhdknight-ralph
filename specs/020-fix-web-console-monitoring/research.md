# Research: Web Console Fix, Application Monitoring, Deployment & Logging

## 1. Dashboard "no data" root cause

**Decision**: Root cause to be confirmed by reproducing the bug locally, but the prime suspect is the request/response path in `web_app/core/views.py:dashboard()` → `api_client.get_history(token, days=30)`. Candidates: (a) the session token stored at login doesn't match what the API expects (expired/never-refreshed), silently returning an empty payload instead of the `unauthorized` error the view already checks for; (b) `history.get("error")` check only handles `"unauthorized"`, so any other error shape (network error, 500, malformed JSON) falls through and renders the template with effectively empty `history`; (c) the template itself fails to render non-empty `history` correctly.

**Rationale**: The existing code already handles the expired-token case explicitly (redirect to login), which means the "no data" symptom the user reports is a *different* failure mode than expired auth — otherwise they'd already be seeing a login redirect. That points at either a data-shape mismatch between what `api_client.get_history` returns and what `dashboard.html` expects, or a swallowed error.

**Alternatives considered**: Rewriting the whole `api_client` — rejected, no evidence the whole client is broken since `account`/`trend` share the same pattern and weren't reported broken.

## 2. Synthetic monitoring account & scheduling

**Decision**: A single dedicated user account (flagged e.g. `is_monitoring_account=true` or via a reserved email/username convention) is created once and reused by a scheduled job that (a) logs into the Django console via its normal login flow, (b) authenticates against the FastAPI `/auth` endpoint directly. The job runs as a periodic OS-level task (cron or systemd timer, consistent with the existing systemd-based deployment) rather than introducing a new task queue.

**Rationale**: Project has no existing task-queue/scheduler dependency (no Celery, no APScheduler in `requirements.txt`); adding one is disproportionate to "log in every N minutes and record the result." systemd timers integrate with the existing `deploy/systemd` assets and existing `journald`/file-logging conventions.

**Alternatives considered**: Celery beat / APScheduler — rejected as new infra for a lightweight periodic check; external uptime service (e.g. a SaaS pinger) — rejected because it can't authenticate as a real user or evaluate response *content* (data presence), only HTTP status.

### 2a. Consecutive-failure escalation (FR-008a)

**Decision**: Default escalation threshold N=2 consecutive failures per target, configurable via the same config surface as the check interval. Computed by querying the last N `MonitoringCheckResult` rows for that target rather than persisting a running counter (per data-model.md).

**Rationale**: N=2 means one flaky/transient failure doesn't page anyone, but two in a row (i.e., the problem survived at least one full check interval) does — a reasonable default for a single-server personal deployment without needing a separate config value to invent from scratch.

**Alternatives considered**: N=1 (escalate on first failure) — rejected as indistinguishable from FR-008's plain per-failure warning, defeating the purpose of a separate escalation tier; a time-based window (e.g., "failing for >10 minutes") instead of a count — rejected as equivalent in effect but more complex to reason about than "N consecutive checks" given checks already run on a fixed interval.

## 3. Integrity monitoring thresholds

**Decision**: Store a periodic snapshot (timestamp, total user count, per-user data-row count) in a new table, and on each check compare against the most recent prior snapshot. Thresholds (max acceptable growth for user count and per-user data count between checks) are configurable via environment/config values, not hardcoded.

**Rationale**: Matches FR-009–FR-012 and SC-003 in spec.md; keeps comparison stateless beyond "last snapshot," avoiding unbounded history scans on every check.

**Alternatives considered**: Comparing against a rolling window average instead of last-snapshot — rejected as unnecessary complexity beyond what the spec asks for; can be revisited if last-snapshot proves too noisy in practice.

## 4. Deployment tooling

**Decision**: Evaluate Ansible as the primary candidate since the user explicitly asked for it to be assessed; a minimal playbook provisions only the two systemd services (`adhd-api`, `adhd-web`) plus nginx config, matching what already exists under `deploy/`. Idempotency comes from Ansible's built-in module semantics (package/service/template modules are naturally idempotent) rather than custom shell scripting.

**Rationale**: The repo already has `deploy/scripts/install.sh` and `push-deploy.sh` (imperative shell) plus systemd/nginx configs (declarative targets) — Ansible is a natural fit to make the existing imperative scripts idempotent and re-runnable, and is a widely-known, dependency-light choice (no server-side agent required, unlike e.g. Salt).

**Alternatives considered**: Keeping/extending the existing shell scripts with manual idempotency checks — viable but more error-prone and harder to keep in sync as the two scripts grow; Docker Compose — rejected because it changes the deployment model (containers vs. the current bare-systemd approach) more than the spec's scope warrants, and the constraint is "only API + web app run on the server," not "must be containerized."

## 5. Storing production `.env` outside the repository

**Decision**: Keep `.env` files out of git (already the case per `.gitignore`), and have the deployment process (Ansible or scripts) fetch/template production values from a location outside the repo on the target server — e.g., an Ansible Vault–encrypted variables file kept in a separate, access-controlled location (not this repository), decrypted at deploy time onto the server's local `.env`.

**Rationale**: Ansible Vault is the natural complement to choosing Ansible for deployment (decision #4) — encrypted-at-rest secrets, decrypted only during the playbook run, no extra secrets-manager infrastructure needed for a single-server deployment.

**Alternatives considered**: A hosted secrets manager (e.g., cloud KMS/secrets service) — rejected as disproportionate infrastructure for a single-server personal project; manually maintaining `.env` by hand on the server outside of any deploy tooling — rejected because it isn't reproducible (fails FR-014's idempotency requirement) and has no audit trail.

## 6. Separate log files per component

**Decision**: FastAPI (`server/app/middleware/logging.py` + `app/main.py` logging setup) gets a dedicated file handler (e.g. `logs/api.log`); Django (`web_app/adhd_web/settings.py` `LOGGING` dict) gets its own dedicated file handler (e.g. `logs/web.log`). Both use each framework's standard logging configuration (Python `logging` module `FileHandler`/`RotatingFileHandler`) rather than a custom logging library.

**Rationale**: Both frameworks already use the standard `logging` module idiomatically; adding a `RotatingFileHandler` per service is the smallest change that satisfies FR-017–FR-019 without introducing a new dependency (e.g., no need for `structlog` or a log-shipping agent, which is explicitly out of scope per spec.md Assumptions).

**Alternatives considered**: Centralized log aggregation (e.g., shipping both to a single indexed store) — explicitly out of scope per spec.md; single shared log file with a component tag on each line — rejected because it doesn't satisfy FR-019 ("contains only that component's own log entries") as directly as physically separate files.

## 7. Automated secret-scan safeguard (FR-016a)

**Decision**: Add `detect-secrets` (or `gitleaks` — either is acceptable, pick whichever integrates more simply) as a pre-commit hook in the repository, scanning staged changes for likely secret patterns before a commit is allowed.

**Rationale**: `.env` files are already gitignored (research.md §5 and existing `.gitignore`), but that only prevents *accidental* `git add .env` — it does nothing if a secret is pasted directly into a tracked file (code, config, a commit message). A pre-commit scanner catches that class of mistake locally, before it ever reaches the remote, with no server-side infrastructure required.

**Alternatives considered**: CI-only scanning (e.g., a GitHub Actions secret-scan step) — viable as a second layer but doesn't stop the secret from being pushed in the first place, and this is a single-maintainer repo without a required-CI-check gate today; a hosted secret-scanning service — rejected as disproportionate for a single-server personal project, same reasoning as research.md §5's rejection of a hosted secrets manager.

## Outstanding items for implementation (not spec ambiguity, just sequencing)

- Exact bug in the dashboard data path must be confirmed by reproduction before writing the fix (User Story 1, `/speckit-tasks` should include a repro/diagnosis task before the fix task).
- Exact monitoring/integrity check interval and threshold *default values* are operational tuning, not architecture — pick sane defaults during implementation (e.g., 15-minute check interval) and make them configurable per FR-005/FR-006/FR-010/FR-012.
