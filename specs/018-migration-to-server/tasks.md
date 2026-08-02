---

description: "Task list for HTTPS/TLS + Basic Auth + PostgreSQL hardening (018-migration-to-server)"
---

# Tasks: HTTPS / TLS Setup pre produkčné nasadenie

**Input**: Design documents from `/specs/018-migration-to-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-behavior.md, quickstart.md

**Status**: All repo-side artifacts (configs, scripts, settings changes, docs) are implemented — T001–T016, T018–T021, T025–T027 are done. T017, T022, T023, T024 require a real production/staging server to execute against and are intentionally left open; see `server/README.md` "Produkčné nasadenie" for the exact commands to run there.

**Tests**: Not requested in spec.md. This is infrastructure/config, not application code — validation happens via the `quickstart.md` scenarios (tasks in each phase run the relevant scenario against a real/staging server instead of automated tests).

**Organization**: Tasks are grouped by user story (US1 = HTTPS/TLS, US2 = Basic Auth on console). Both are P1 in spec.md; US1 is sequenced first because US2's Nginx config builds on top of US1's console server block.

**Cross-feature blocker**: `017-migration-to-postgres` has not delivered a SQLite→PostgreSQL data-migration script yet (only `spec.md` exists). Task T010 below wires up the *call site* for that tool per `research.md` Decision 8 — it does **not** implement the migration logic itself. T010 will fail loudly until 017 delivers its script; that failure is expected and correct, not a bug in 018.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- File paths are relative to repo root (`/home/martin/projects/adhdmad`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffolding needed before any config content is written

- [X] T001 Create `deploy/nginx/`, `deploy/systemd/`, `deploy/scripts/` directories (empty scaffolding, matches plan.md Project Structure)
- [X] T002 [P] Add `gunicorn>=22.0.0` and `psycopg[binary]>=3.1.0` to `web_app/requirements.txt` (Gunicorn = production WSGI server for Django; psycopg = Postgres driver for `adhd_web` database)
- [X] T003 [P] Create `web_app/.env.example` with `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRET_KEY`, `DJANGO_DATABASE_URL` (documented defaults matching local dev, per data-model.md EnvironmentConfig)
- [X] T004 [P] Create `web_app/.gitignore` covering `.env`, `staticfiles/`, `__pycache__/`, `*.pyc` (web_app currently has no `.gitignore`; prevents the new `.env` and `collectstatic` output from being committed)

**Checkpoint**: Scaffolding exists; no behavior changes yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: PostgreSQL, Django production settings, and process-supervision units that both user stories run on top of

**⚠️ CRITICAL**: No user story work can be verified end-to-end until this phase is complete

- [X] T005 Add `setup_postgres()` step to `deploy/scripts/install.sh`: verify/set `listen_addresses = 'localhost'` in `postgresql.conf`, restrict `pg_hba.conf` to `local` (peer) + `host ... 127.0.0.1/32 scram-sha-256` (FR-006; data-model.md PostgresDatabase)
- [X] T006 Add `create_databases()` step to `deploy/scripts/install.sh`: create `adhd_server` DB + role (owned by API, consumed by 017's migration) and `adhd_web` DB + role (owned by Django), both password-auth restricted to localhost
- [X] T007 [P] Update `web_app/adhd_web/settings.py`: env-driven `DEBUG` (← `DJANGO_DEBUG`, default `True`), `ALLOWED_HOSTS` (← `DJANGO_ALLOWED_HOSTS`), `SECRET_KEY` (← `DJANGO_SECRET_KEY`, falls back to existing insecure dev key), `DATABASES` (← `DJANGO_DATABASE_URL` if set, else existing SQLite fallback), `STATIC_ROOT = BASE_DIR / 'staticfiles'`, `CSRF_TRUSTED_ORIGINS = ['https://console.adhdknight.com']`, `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` (research.md Decision 7 — must preserve current dev behavior when no env vars are set)
- [X] T008 [P] Write `deploy/systemd/adhd-api.service`: `ExecStart=uvicorn app.main:app --host 127.0.0.1 --port 8095`, `WorkingDirectory=server/`, `EnvironmentFile=server/.env`, `Restart=on-failure` (data-model.md SystemdUnit)
- [X] T009 [P] Write `deploy/systemd/adhd-web.service`: `ExecStart=gunicorn adhd_web.wsgi:application --bind 127.0.0.1:8000`, `WorkingDirectory=web_app/`, `EnvironmentFile=web_app/.env`, `Restart=on-failure`
- [X] T010 Add `migrate_data()` step to `deploy/scripts/install.sh`: invoke 017's SQLite→PostgreSQL migration tool (expected path `server/scripts/migrate_sqlite_to_postgres.py`, per research.md Decision 8); if the script is missing, **fail with an explicit error** (`"017 migration tool not found — see specs/017-migration-to-postgres"`), never silently skip or reimplement the migration inline
- [X] T011 Add `install_deps_and_migrate()` step to `deploy/scripts/install.sh`: venv setup + `pip install -r requirements.txt` for both `server/` and `web_app/`, `alembic upgrade head` (server), `python manage.py migrate` + `python manage.py collectstatic --noinput` (web_app), then enable+start `adhd-api.service` and `adhd-web.service` (depends on T005–T010)

**Checkpoint**: PostgreSQL is up and localhost-only, both app processes run under systemd on `127.0.0.1`, Django settings are production-ready — but nothing is reachable from outside yet (no Nginx/TLS in front). Foundation ready for US1.

---

## Phase 3: User Story 1 - Bezpečná komunikácia cez HTTPS (Priority: P1) 🎯 MVP

**Goal**: Both domains are reachable over valid, auto-renewing HTTPS; HTTP requests redirect to HTTPS; local dev HTTP stays untouched.

**Independent Test**: Deploy server with HTTPS cert → mobile app and web app connect without certificate warnings; certificate auto-renews without any client-side change.

### Implementation for User Story 1

- [X] T012 [P] [US1] Write `deploy/nginx/api.adhdknight.com.conf`: `server_name api.adhdknight.com`, `proxy_pass http://127.0.0.1:8095`, standard proxy headers (`X-Forwarded-Proto`, `X-Forwarded-For`, `Host`) — no `auth_basic` directive (contracts/http-behavior.md)
- [X] T013 [P] [US1] Write `deploy/nginx/console.adhdknight.com.conf`: `server_name console.adhdknight.com`, `proxy_pass http://127.0.0.1:8000`, `location /static/ { alias <path-to>/web_app/staticfiles/; }`, proxy headers including `X-Forwarded-Proto`
- [X] T014 [US1] Add `setup_nginx_and_certs()` step to `deploy/scripts/install.sh`: symlink both configs from `deploy/nginx/` into `/etc/nginx/sites-available/` + `sites-enabled/`, run `nginx -t`, then `certbot --nginx -d api.adhdknight.com` and `certbot --nginx -d console.adhdknight.com` (depends on T012, T013; research.md Decision 2 — certbot's `--nginx` plugin auto-adds the port-443 block, cert paths, and the port-80→443 redirect, satisfying FR-003)
- [X] T015 [US1] Add `systemctl enable --now certbot.timer` to `deploy/scripts/install.sh` and a comment documenting the DNS-01 fallback (Edge Case in spec.md) for servers without a public IP for the HTTP-01 challenge (FR-002)
- [X] T016 [US1] Add "Produkčné nasadenie" section to `server/README.md`: domains, systemd units, pointer to `deploy/`, and an explicit note that `network_security_config.xml` (016) already covers dev-mode cleartext HTTP — no Android change needed (FR-004)
- [ ] T017 [US1] Run quickstart.md Scenarios 1, 2, 4, 5 against the staging/production server; record pass/fail for each (SC-001, SC-002, SC-003)

**Checkpoint**: US1 fully functional — `https://api.adhdknight.com` and `https://console.adhdknight.com` serve valid Let's Encrypt certs, HTTP redirects to HTTPS on both, `certbot.timer` handles renewal, and `make dev` locally is unaffected.

---

## Phase 4: User Story 2 - Basic auth na web konzole (Priority: P1)

**Goal**: `console.adhdknight.com` requires HTTP Basic Auth at the Nginx layer before any request reaches Django; `api.adhdknight.com` has no basic auth.

**Independent Test**: Open `console.adhdknight.com` without credentials → browser is prompted for Basic Auth before anything from Django loads; correct credentials → page loads normally.

### Implementation for User Story 2

- [X] T018 [US2] Add `auth_basic "Restricted"; auth_basic_user_file /etc/nginx/.htpasswd_console;` to the `location /` block in `deploy/nginx/console.adhdknight.com.conf` (depends on T013)
- [X] T019 [US2] Add `setup_basic_auth()` step to `deploy/scripts/install.sh`: install `apache2-utils` if missing, run `htpasswd -cb /etc/nginx/.htpasswd_console admin admin` to create the placeholder credential, and print an explicit operator warning to change it via `htpasswd /etc/nginx/.htpasswd_console admin` before going live (FR-005; data-model.md BasicAuthCredential — placeholder never becomes the real production password)
- [X] T020 [US2] Add a comment/assertion in `deploy/scripts/install.sh` (or a short check script) confirming `deploy/nginx/api.adhdknight.com.conf` contains no `auth_basic` directive, so a future edit can't accidentally add auth to the API domain (SC-004)
- [X] T021 [US2] Document the manual password-change requirement in `server/README.md` "Produkčné nasadenie" section: placeholder `admin`/`admin` MUST be replaced by a human interactively on the server, never committed to the repo
- [ ] T022 [US2] Run quickstart.md Scenario 3 against the staging/production server: confirm `401` + `WWW-Authenticate` on console without credentials, `200`/`302` with credentials, and no `WWW-Authenticate` at all on the API domain

**Checkpoint**: Both user stories complete — console is protected by Nginx-level Basic Auth in front of TLS+Django; API is reachable over HTTPS with no basic auth, using its own JWT auth.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Remaining FR-006 verification, safety checks, and regression confirmation across both stories

- [ ] T023 [P] Run quickstart.md Scenario 6 against the production server: confirm `psql` from `127.0.0.1` succeeds and from an external host fails/times out (SC-005)
- [ ] T024 [P] Run quickstart.md Scenario 7: execute `deploy/scripts/install.sh --step migrate-data` and confirm it either succeeds (if 017 has since delivered its tool) or fails with the explicit "017 migration tool not found" error — never a silent no-op
- [X] T025 Run `cd server && make test` and `cd web_app && python manage.py test` to confirm the settings/dependency changes in T002, T007 did not break existing test suites (no test code changes expected — same behavior with env vars unset)
- [X] T026 [P] Add an `nginx -t` syntax-check (fail-fast, before `systemctl reload nginx`) to every config-changing step in `deploy/scripts/install.sh`, per the rollback note in quickstart.md
- [X] T027 Verify `.htpasswd_console`, `web_app/.env`, and `server/.env` are all gitignored and `git status` shows no real secrets staged before considering the feature done

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS both user stories (Nginx has nothing to proxy to until app processes run under systemd)
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 2 **and** on T013 (console Nginx config from US1) — not independently deployable before US1's console server block exists, but independently *testable* once both are in place (auth_basic is an isolated directive addition)
- **Polish (Phase 5)**: Depends on Phase 3 and Phase 4 both being complete

### Within Each Phase

- Tasks marked `[P]` touch different files and can run in parallel
- Unmarked tasks within a phase either share a file (`deploy/scripts/install.sh` — most Phase 2/3/4 script-step tasks append to the same file sequentially) or depend on a `[P]` task's output

### Parallel Opportunities

- T002, T003, T004 (Phase 1) — different files
- T007, T008, T009 (Phase 2) — different files (T005/T006/T010/T011 all edit `install.sh` sequentially)
- T012, T013 (Phase 3) — different Nginx config files
- T023, T024, T026 (Phase 5) — independent verification/safety tasks

---

## Parallel Example: Phase 2 (Foundational)

```bash
# These touch different files and can run together once T001 (Setup) is done:
Task: "Update web_app/adhd_web/settings.py for env-driven production config"
Task: "Write deploy/systemd/adhd-api.service"
Task: "Write deploy/systemd/adhd-web.service"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (PostgreSQL localhost binding, systemd units, Django prod settings, 017 call-site)
3. Complete Phase 3: User Story 1 (HTTPS/TLS on both domains)
4. **STOP and VALIDATE**: run quickstart.md Scenarios 1, 2, 4, 5
5. At this point both domains are securely reachable — US2 (basic auth on console) can follow as the next increment without touching US1's work

### Incremental Delivery

1. Setup + Foundational → app processes running locally under systemd, Postgres locked down
2. Add US1 → both domains on valid HTTPS, redirect works → validate → this is the MVP (spec.md marks US1 as the priority story)
3. Add US2 → console gated by Basic Auth → validate → feature complete
4. Phase 5 closes out the FR-006 (Postgres) and 017-blocker verification that doesn't belong to either story specifically

### Blocked work — flag, don't reimplement

T010 (data migration call-site) and, by extension, the full end-to-end production cutover cannot be *completed* until `017-migration-to-postgres` delivers its migration script. Per spec.md's explicit instruction, do not write that migration logic as part of these tasks — T010's job is only to wire up the call and fail clearly if the dependency is missing.
