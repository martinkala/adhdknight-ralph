# Feature Specification: Web Console Fix, Application Monitoring, Deployment & Logging

**Feature Branch**: `020-fix-web-console-monitoring`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "Ciel 1: opravit web based konzolu, pretoze sa nezobrazuju ziadne data pri prihlaseni uzivatela. Ciel 2: navrhnut monitoring aplikacii (web based, api based) so spolocnym testovacim uzivatelskym uctom prihlasujucim sa v pravidelnych intervaloch, a integrity-based monitoring (detekcia prieniku, test poctu uzivatelov, test poctu dat per uzivatel oproti threshold-u). Ciel 3: deployment len pre API a web app (nic ine na serveri), vratane Ansible a bezpecneho ulozenia .env mimo repository. Ciel 4: separatne logovanie web konzoly a API do samostatnych suborov."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dashboard shows data after login (Priority: P1)

A logged-in user opens the web console dashboard and expects to see their tracked history (the last 30 days of activity). Today the dashboard renders with no data, making the console appear broken.

**Why this priority**: This is an active production bug affecting every user of the web console — without it, the console has no value.

**Independent Test**: Log in as a test user with known historical data, load the dashboard, and verify the expected data points render (not an empty state).

**Acceptance Scenarios**:

1. **Given** a user with existing history data and a valid session, **When** they log in and land on the dashboard, **Then** their last 30 days of data are visible.
2. **Given** a user whose session token has expired, **When** they load the dashboard, **Then** they are redirected to login rather than shown a blank/broken dashboard.
3. **Given** a brand-new user with no history yet, **When** they load the dashboard, **Then** they see an explicit "no data yet" state rather than an unexplained blank page.

---

### User Story 2 - Synthetic uptime monitoring for web console and API (Priority: P2)

An operator wants ongoing confidence that both the web console and the API are actually working end-to-end (not just "process is running"), verified by a dedicated monitoring account that logs in on a schedule and checks that expected data appears.

**Why this priority**: Prevents a repeat of User Story 1 (silently broken login/data path) from going unnoticed, and extends the same check to the API.

**Independent Test**: Configure the monitoring account and interval; confirm a failed login or missing-data response produces a visible alert/warning, and a successful check produces no alert.

**Acceptance Scenarios**:

1. **Given** a scheduled monitoring cycle runs, **When** the monitoring account logs into the web console, **Then** the system records success/failure and surfaces a warning on failure or on unexpectedly missing data.
2. **Given** a scheduled monitoring cycle runs, **When** the monitoring account authenticates against the API, **Then** the system records success/failure and surfaces a warning on failure.
3. **Given** the monitoring account fails N consecutive scheduled checks against the same target (configurable, default N=2), **When** the Nth consecutive failure is recorded, **Then** a distinct, higher-severity escalation warning is raised for that target — not merely a repeat of the same single-failure warning already raised on check 1.

---

### User Story 3 - Integrity / intrusion-detection monitoring (Priority: P2)

An operator wants early warning of anomalous growth that could indicate account abuse or a data breach: a sudden spike in new user registrations, or a sudden spike in the amount of data recorded for a given user since the last check.

**Why this priority**: Detects intrusion or abuse patterns that uptime monitoring (User Story 2) would not catch, protecting user data integrity.

**Independent Test**: Seed a test scenario where user growth or per-user data growth exceeds the configured threshold between two checks, and verify a warning is generated; verify normal growth produces no warning.

**Acceptance Scenarios**:

1. **Given** a baseline user count from the previous check, **When** the current check finds growth exceeding the configured threshold, **Then** a warning is generated identifying the anomaly.
2. **Given** a baseline per-user data count from the previous check, **When** a user's data count grows by more than the configured threshold since that check, **Then** a warning is generated identifying that user and the growth amount.
3. **Given** growth stays within configured thresholds, **When** a check runs, **Then** no warning is generated.

---

### User Story 4 - Minimal, reproducible deployment of API and web app only (Priority: P3)

An operator wants to (re)deploy the API and web console to a server with nothing else running there, using a documented, repeatable process, without committing production secrets to the repository.

**Why this priority**: Reduces server attack surface and operational risk, and removes reliance on tribal knowledge for deployment; lower priority than the monitoring/bug-fix work since the app already runs in production today.

**Independent Test**: Provision or reset a target server using the documented process/tooling and confirm only the API and web app services end up running, with production `.env` values present but absent from version control.

**Acceptance Scenarios**:

1. **Given** a clean target server, **When** the documented deployment process is run, **Then** only the API and web console services are installed and running (no unrelated services).
2. **Given** a deployment run, **When** it needs production configuration values, **Then** it retrieves them from outside the repository (not from a committed `.env` file) and they are not written into version control at any point.
3. **Given** the deployment process is re-run against a server already at the target state, **When** it completes, **Then** the result is the same as the first run (repeatable, no drift).

---

### User Story 5 - Separate log files for web console and API (Priority: P3)

An operator wants to monitor the web console and the API independently, so each must write its own log output to a separate file rather than a single interleaved stream.

**Why this priority**: Enables the monitoring in User Stories 2 and 3 to inspect each component's health independently; mostly an operational/observability convenience once the higher-priority fixes and monitoring are in place.

**Independent Test**: Trigger activity in the web console and separately in the API, and confirm each component's log entries land only in that component's dedicated log file.

**Acceptance Scenarios**:

1. **Given** the web console handles a request, **When** it logs that activity, **Then** the entry is written to the web console's dedicated log file only.
2. **Given** the API handles a request, **When** it logs that activity, **Then** the entry is written to the API's dedicated log file only.
3. **Given** both components are running, **When** an operator inspects either log file, **Then** it contains only entries from that component, in chronological order.

---

### Edge Cases

- What happens when the monitoring test-user account's own credentials expire or are locked out — does the monitoring system distinguish "app is broken" from "monitoring account itself needs attention"?
- How does the integrity monitor handle the very first check (no prior baseline to compare against)?
- What happens when the growth-threshold check coincides with an expected legitimate spike (e.g., a marketing push)? Is there a way to acknowledge/suppress a warning?
- What happens if the log destination for either component becomes unwritable (disk full, permissions) — does the app fail loudly or silently drop logs?
- What happens during deployment if a required production secret is missing from the external secret store?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The web console dashboard MUST display the logged-in user's history data when that data exists, instead of the current no-data/blank result.
- **FR-002**: The web console MUST distinguish between "user has no data yet" and "data failed to load," presenting a distinct, explicit message for each case.
- **FR-003**: The web console MUST redirect the user to login (rather than showing a broken/blank dashboard) whenever the session/token backing the dashboard request is invalid or expired.
- **FR-004**: The system MUST provide a dedicated monitoring account that is distinct from regular user accounts and usable by both the web console and API checks.
- **FR-005**: The system MUST perform a scheduled login check against the web console using the monitoring account, at a configurable interval.
- **FR-006**: The system MUST perform a scheduled authentication check against the API using the monitoring account, at a configurable interval.
- **FR-007**: The system MUST record the result (success/failure, timestamp) of every monitoring check.
- **FR-008**: The system MUST surface a warning when a monitoring check fails or returns unexpectedly missing data.
- **FR-008a**: The system MUST raise a distinct, higher-severity escalation warning — separate from the per-failure warning in FR-008 — when the same monitoring target (web console or API) fails N consecutive scheduled checks, where N is configurable with a default of 2.
- **FR-009**: The system MUST track the total user count at each integrity check and compare it against the count recorded at the previous check.
- **FR-010**: The system MUST raise a warning when user-count growth since the previous check exceeds a configurable threshold.
- **FR-011**: The system MUST track each user's data volume at each integrity check and compare it against that user's volume recorded at the previous check.
- **FR-012**: The system MUST raise a warning, identifying the affected user, when a user's data-volume growth since the previous check exceeds a configurable threshold.
- **FR-013**: The deployment process MUST result in only the API and web console services running on the target server, with no unrelated services installed.
- **FR-014**: The deployment process MUST be repeatable/idempotent: re-running it against a server already at the target state MUST NOT change the outcome.
- **FR-015**: The deployment process MUST source production configuration/secrets from a location outside the source-controlled repository.
- **FR-016**: The repository MUST NOT contain production secret values at any point in its history going forward (only non-secret examples/templates, as today's `.env.example` pattern already does).
- **FR-016a**: The deployment/repository tooling MUST include an automated safeguard (e.g., a pre-commit or CI secret-scan check) that flags likely secret values before they are committed, so FR-016 is machine-checked rather than relying on manual discipline alone.
- **FR-017**: The web console MUST write its log output to a log file that is separate from the API's log output.
- **FR-018**: The API MUST write its log output to a log file that is separate from the web console's log output.
- **FR-019**: Each component's log file MUST contain only that component's own log entries.

### Key Entities

- **Monitoring Check Result**: A record of one synthetic login/health check (web console or API), including timestamp, target component, outcome (success/failure), and any error detail.
- **Integrity Snapshot**: A periodic recording of aggregate counters (total user count, per-user data volume) used as the baseline for the next comparison.
- **Integrity Warning**: An alert generated when a snapshot-to-snapshot comparison exceeds a configured growth threshold, including which metric, which entity (e.g., user), and the magnitude of growth.
- **Monitoring Account**: The single shared test user credential used to exercise both the web console and API login paths on a schedule.
- **Deployment Configuration**: The set of production environment values (secrets, connection strings) required to run the API and web console, stored outside the repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of users with existing history data see that data on the dashboard immediately after login (currently 0%).
- **SC-002**: A synthetic login failure on either the web console or the API produces a visible warning within one monitoring interval of the failure occurring.
- **SC-003**: An anomalous spike in user registrations or in a single user's data volume (beyond the configured threshold) produces a warning within one monitoring interval, with zero warnings raised for growth that stays within threshold during normal operation.
- **SC-004**: A server can be brought from clean to fully deployed (API + web console only, no unrelated services) using the documented process alone, without manual undocumented steps.
- **SC-005**: No production secret values exist in the repository at any point after this feature ships.
- **SC-006**: An operator can determine the health of the web console or the API independently by reading only that component's log file, without filtering out entries from the other component.

## Assumptions

- The web console (Django) and API (FastAPI) referenced in the existing codebase are the "web based console" and "api based" components in scope for all four goals.
- "No data pri prihlaseni" (User Story 1) is caused by the dashboard's data-fetch path (session token / API call to fetch history) failing silently rather than by the data not existing; the fix targets that path, but the exact root cause is to be confirmed during planning/implementation, not fixed sight-unseen in this spec.
- The monitoring account (User Stories 2 & 3) is a single, dedicated non-production-data account, not a rotating set of real user accounts.
- "Pravidelne intervaly" (regular intervals) for monitoring checks is a configurable schedule (e.g., every N minutes), with the exact default interval to be decided during planning.
- Growth thresholds for integrity monitoring (user count, per-user data volume) are configurable values, not fixed constants, since "moc rychlo" (too fast) is context-dependent.
- "Vsetko ostatne na serveri nebude" (nothing else on the server) means no additional application services beyond the API and web console; standard OS-level infrastructure (reverse proxy, process supervisor) required to run those two remains in scope, matching the existing `deploy/nginx` and `deploy/systemd` setup.
- Ansible is evaluated as one deployment-tooling option among others during planning, not mandated as the final choice by this spec.
- Secret storage outside the repository (goal 3) will use a mechanism decided during planning (e.g., a secrets manager, encrypted vault, or server-local file provisioned out-of-band); this spec only requires that secrets are never committed to the repository.
- Separate log files (goal 4) are local files on the server per component; centralized log aggregation/shipping is out of scope unless specified later.
- The consecutive-failure escalation threshold in FR-008a (default N=2) is computed by querying recent `Monitoring Check Result` rows for the same target, not by adding new persisted state — "consecutive" resets as soon as one check for that target succeeds.
- The automated secret-scan safeguard in FR-016a is a repository/CI-level tool (e.g., `detect-secrets` or `gitleaks`), chosen during implementation; it augments, not replaces, keeping secrets out of `.env` files committed to the repo.
