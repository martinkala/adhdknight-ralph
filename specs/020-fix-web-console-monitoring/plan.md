# Implementation Plan: Web Console Fix, Application Monitoring, Deployment & Logging

**Branch**: `020-fix-web-console-monitoring` | **Date**: 2026-08-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/020-fix-web-console-monitoring/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Fix the Django web console dashboard so it renders the logged-in user's history instead of a blank page (root cause to confirm in research: session/token/API-call failure in `web_app/core/views.py:dashboard`). Add scheduled synthetic monitoring (a dedicated test account logging into both the Django console and the FastAPI API) and integrity monitoring (user-count and per-user data-volume growth vs. a configurable threshold, compared against a stored baseline snapshot). Split the FastAPI (`server/app/middleware/logging.py`) and Django console logging into two separate log files. Document/automate a minimal, idempotent deployment of only the API and web console (evaluating Ansible) that pulls production secrets from outside the repository, building on the existing `deploy/nginx`, `deploy/systemd`, and `deploy/scripts` assets.

## Technical Context

**Language/Version**: Python 3.11 (FastAPI server), Python (Django ≥6.0 web console)

**Primary Dependencies**: FastAPI, SQLAlchemy (async) + Alembic + asyncpg/aiosqlite, python-jose (JWT) on the API side; Django, httpx (server-side calls to the API), gunicorn, psycopg on the web console side

**Storage**: PostgreSQL in production (SQLite for local dev) for both the API DB and the Django `adhd_web` DB; log files on local disk (one per component, per goal 4)

**Testing**: pytest / pytest-asyncio / httpx / behave (server); Django's test runner (web_app) — exact web_app test tooling to confirm in research if not already present

**Target Platform**: Linux server, both services co-located (per existing `deploy/systemd`, `deploy/nginx` configs for `api.adhdknight.com` and `console.adhdknight.com`)

**Project Type**: Web application — separate backend API (FastAPI) + backend-rendered web console (Django), no separate frontend SPA

**Performance Goals**: N/A — this feature is a correctness fix plus operational tooling (monitoring, deployment, logging), not a performance-sensitive path

**Constraints**: Monitoring/logging changes must not weaken the existing production guardrail that `FASTAPI_URL` stays `127.0.0.1`-only in production (see recent fix in git history); deployment must not introduce any service beyond the API and web console on the target server

**Scale/Scope**: Single production server, single test/monitoring account, small number of real users (personal/small-scale ADHD tracker deployment per `constitution.md`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`constitution.md` governs the **Android app** (MVVM + Repository, Room schema, ADHD index domain logic, Compose UI, notification rules). This feature touches none of that surface — it is entirely server-side (FastAPI `server/`) and web console (Django `web_app/`) work: a UI bug fix, operational monitoring, deployment tooling, and logging.

**Result: No constitution principle applies to this feature. No gates triggered, no violations, nothing to justify in Complexity Tracking.**

## Project Structure

### Documentation (this feature)

```text
specs/020-fix-web-console-monitoring/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
server/                          # FastAPI API (existing)
├── app/
│   ├── main.py                  # add API-side log file handler config here
│   ├── middleware/logging.py    # existing request logging middleware — split output to dedicated file
│   ├── monitoring/              # NEW: synthetic login check + integrity snapshot/threshold logic
│   └── db/migrations/           # Alembic — NEW tables for monitoring results & integrity snapshots
└── tests/
    └── monitoring/              # NEW: tests for synthetic checks + integrity threshold logic

web_app/                         # Django web console (existing)
├── core/
│   ├── views.py                 # fix dashboard() data-fetch path (goal 1)
│   ├── api_client.py            # likely fix location for the no-data bug
│   └── logging config in adhd_web/settings.py  # NEW: separate log file for console
└── adhd_web/settings.py         # Django logging config

deploy/                          # existing deployment assets
├── nginx/                       # existing, unchanged unless research finds gaps
├── systemd/                     # existing service units for adhd-api / adhd-web
├── scripts/                     # existing install.sh / push-deploy.sh
└── ansible/                     # NEW (if research selects Ansible): playbooks/roles for
                                  # provisioning only the API + web console, pulling secrets
                                  # from an external store
```

**Structure Decision**: Existing two-service layout (FastAPI `server/` + Django `web_app/`) is preserved as-is. Goal 1 is a targeted fix inside `web_app/core`. Goals 2–3 (monitoring, integrity checks) add a new `server/app/monitoring/` module plus corresponding Alembic migration and tests, since the monitoring/integrity checks need durable storage of snapshots and check results — the FastAPI+SQLAlchemy stack already in `server/` is the natural home rather than introducing a new component. Goal 4 (logging) is a configuration-only change in each service's existing logging setup. Goal 5 (deployment) extends `deploy/` with either an Ansible playbook or a documented alternative, decided in research.md.

## Complexity Tracking

*No constitution violations — this section is not applicable (see Constitution Check above).*
