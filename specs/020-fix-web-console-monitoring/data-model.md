# Data Model: Web Console Fix, Application Monitoring, Deployment & Logging

Only User Stories 2 & 3 (monitoring, integrity checks) introduce new persisted data. Goals 1, 4, and 5 (dashboard fix, logging, deployment) are behavioral/configuration changes with no new entities.

## MonitoringCheckResult

Records one synthetic login/health check against the web console or the API (FR-005–FR-008).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID / PK | |
| `target` | enum(`web_console`, `api`) | which component was checked |
| `checked_at` | timestamp | when the check ran |
| `success` | boolean | login/auth succeeded and expected data was returned |
| `error_detail` | text, nullable | populated on failure |

**Validation rules**: `error_detail` MUST be null when `success = true`; MUST be non-empty when `success = false`.

**Escalation (FR-008a)**: Consecutive-failure count per `target` is derived, not stored — computed by querying the most recent `MonitoringCheckResult` rows for that `target` ordered by `checked_at` and counting back from the latest until a `success = true` row is hit (or none exists). No new column/table is needed; the configurable threshold `N` (default 2) lives in application config alongside the integrity-growth thresholds.

## IntegritySnapshot

A periodic recording of aggregate counters used as the baseline for the next comparison (FR-009, FR-011).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID / PK | |
| `captured_at` | timestamp | |
| `total_user_count` | integer | |

**Relationships**: has many `UserDataVolumeSnapshot` rows (one per user, captured at the same `captured_at`).

## UserDataVolumeSnapshot

Per-user data volume at a given `IntegritySnapshot` (FR-011).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID / PK | |
| `snapshot_id` | FK → IntegritySnapshot | |
| `user_id` | FK → existing user entity | |
| `data_count` | integer | count of that user's tracked data rows at capture time |

**Validation rules**: unique on (`snapshot_id`, `user_id`).

## IntegrityWarning

An alert generated when a snapshot-to-snapshot comparison exceeds a configured growth threshold (FR-010, FR-012).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID / PK | |
| `raised_at` | timestamp | |
| `metric` | enum(`user_count_growth`, `user_data_growth`) | |
| `user_id` | FK, nullable | set only for `user_data_growth` |
| `previous_value` | integer | value at prior snapshot |
| `current_value` | integer | value at current snapshot |
| `threshold` | integer | configured threshold at time of check |

**State transitions**: created once per detected anomaly; no update/edit — a fresh check either raises a new warning or doesn't (no "resolve" state in this spec's scope; operators dismiss out-of-band).

## MonitoringAccount

Not a new table — represented by a flag/convention on the existing user entity (FR-004), e.g. a boolean `is_monitoring_account` or a reserved account created via seed/migration. Exact mechanism is an implementation choice for `/speckit-tasks`, not a new conceptual entity requiring its own table.

## DeploymentConfiguration

Not application data — represents the external (Ansible Vault–encrypted, per research.md §5) secret values consumed at deploy time. No runtime table; out of scope for the application's own data model.
