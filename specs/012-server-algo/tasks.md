# Tasks: Backend Weight Vector Server

**Input**: Design documents from `specs/012-server-algo/`

**Tech stack**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x async, Alembic, PostgreSQL/SQLite, JWT, behave (BDD), pytest

**Note**: BDD testy sú súčasťou US2 (explicitne požadované v spec). Všetky ostatné testy (unit + API) sú zahrnuté podľa požiadaviek spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelizovateľné (rôzne súbory, bez závislostí)
- **[Story]**: Používateľský príbeh (US1–US7)

---

## Phase 1: Setup

**Purpose**: Inicializácia projektu `server/` v koreňovom repozitári.

- [X] T001 Vytvoriť adresárovú štruktúru `server/` podľa plan.md (`app/`, `app/models/`, `app/schemas/`, `app/routers/`, `app/services/`, `app/db/`, `tests/unit/`, `tests/api/`, `tests/bdd/features/`, `tests/bdd/steps/`, `tests/bdd/fixtures/`)
- [X] T002 Vytvoriť `server/pyproject.toml` s metadátami projektu a all dependencies (fastapi, uvicorn[standard], sqlalchemy[asyncio], alembic, asyncpg, aiosqlite, passlib[bcrypt], python-jose[cryptography], pydantic-settings, httpx, pytest, pytest-asyncio, behave, pyyaml)
- [X] T003 [P] Vytvoriť `server/requirements.txt` ako frozen export z pyproject.toml (pre jednoduché `pip install -r requirements.txt`)
- [X] T004 [P] Vytvoriť `server/.env.example` s kompletnou konfiguráciou: `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `ENVIRONMENT`
- [X] T005 [P] Vytvoriť `server/Makefile` s targetmi: `dev` (install + migrate + uvicorn --reload), `test` (pytest), `test-bdd` (behave), `test-all`, `migrate`, `clean`
- [X] T006 Vytvoriť `server/app/config.py` — pydantic-settings `Settings` trieda načítavajúca env vars; singleton `get_settings()`; automatický fallback na SQLite ak `DATABASE_URL` nie je nastavený

---

## Phase 2: Foundational

**Purpose**: Databáza, SQLAlchemy, Alembic, základný FastAPI app — blokujúce prerekvizity pre všetky user stories.

**⚠️ CRITICAL**: Žiadna user story sa nesmie začať kým táto fáza nie je kompletná.

- [X] T007 Vytvoriť `server/app/db/database.py` — async SQLAlchemy engine factory (dialect-aware: asyncpg pre PostgreSQL, aiosqlite pre SQLite); `AsyncSession` factory; `get_db()` dependency
- [X] T008 Vytvoriť `server/app/models/user.py` — SQLAlchemy `User` model: `id` (UUID PK), `email` (unique indexed), `password_hash`, `created_at`, `last_sync_at`, `is_active`
- [X] T009 [P] Vytvoriť `server/app/models/tracking.py` — `TrackingDay` (id UUID, user_id FK, date, is_complete, created_at, updated_at, device_id) + `ElementValue` (id UUID, tracking_day_id FK, element_key indexed, value_binary, value_scale, value_effective, updated_at); UNIQUE constraint `(tracking_day_id, element_key)`
- [X] T010 [P] Vytvoriť `server/app/models/weights.py` — `WeightConfig` (id UUID, user_id FK, element_key, weight_default, weight_personal nullable, updated_at); UNIQUE `(user_id, element_key)`
- [X] T011 [P] Vytvoriť `server/app/models/sync.py` — `SyncRecord` (id UUID, user_id FK, device_id nullable, sync_type Enum, records_sent/accepted/conflicted/rejected, conflict_log JSON nullable, synced_at) + `DailyIndex` (id UUID, tracking_day_id FK unique, index_value, detail_json nullable, computed_at, config_version)
- [X] T012 Inicializovať Alembic v `server/app/db/` (`alembic init`); nastaviť `alembic.ini` a `env.py` pre async SQLAlchemy a `DATABASE_URL` z env; vygenerovať a commitnúť initial migration `001_initial_schema.py` pokrývajúcu všetky modely z T008–T011
- [X] T013 Vytvoriť `server/app/main.py` — FastAPI app inštancia; zaregistrovať health router; CORS middleware (allow origins z config); global exception handler vracajúci `{"detail": str}` bez stack trace; lifespan handler pre DB connection warmup
- [X] T014 Vytvoriť `server/app/routers/health.py` — `GET /api/v1/health` vracajúci `{status, version, db, timestamp}`; overuje DB spojenie volaním `SELECT 1`
- [X] T015 Vytvoriť `server/tests/conftest.py` — pytest fixtures: `async_client` (httpx AsyncClient s in-memory SQLite), `db_session` (čistá DB pre každý test), `override_get_db` (FastAPI dependency override)

**Checkpoint**: `make dev` spustí server, `GET /api/v1/health` vráti `{"status": "ok"}`.

---

## Phase 3: User Story 1 — Regresné testovanie algoritmu (Priority: P1) 🎯 MVP

**Goal**: Vývojár môže poslať tracking dáta a dostať vypočítaný ADHD index identický s Android appkou.

**Independent Test**: `POST /api/v1/compute/daily` s fixture `1_day.yaml` vráti `index_value: 86.61` ±0.01.

### Implementácia US1

- [X] T016 [US1] Vytvoriť `server/app/services/index_calculator.py` — port `IndexCalculator.computeDailyIndexGrouped()` z Android Kotlin do Pythonu; vstup: list `ElementValue`-like dict + `EntityConfig` dict + `active_keys` set; algoritmus C1 (priemer aktívnych detí × váha rodiča); vráti `index_value` (float 0–100) + `detail` per-element
- [X] T017 [P] [US1] Vytvoriť `server/app/schemas/compute.py` — Pydantic v2 modely: `EntityNodeInput`, `ElementValueInput`, `DayInput`, `ComputeDailyRequest`, `ComputeDetailItem`, `ComputeDailyResponse`, `ComputeRangeRequest`, `ComputeRangeResult`, `ComputeRangeResponse`; všetky response modely s `schema_version: str = "1.0"`
- [X] T018 [P] [US1] Vytvoriť `server/tests/bdd/fixtures/1_day.yaml` — 1 deň, `sleep (scale=4) + overall_feeling (scale=5)`, `expected.index_value: 86.61`
- [X] T019 [P] [US1] Vytvoriť `server/tests/bdd/fixtures/3_days.yaml` — 3 dni, rôzne elementy, jeden deň prázdny (`status: no_data`), očakávané hodnoty vypočítané ručne
- [X] T020 [P] [US1] Vytvoriť `server/tests/bdd/fixtures/5_days.yaml` — 5 dní vrátane dňa so subpoložkami (element s parent); overenie C1 algoritmu
- [X] T021 [P] [US1] Vytvoriť `server/tests/bdd/fixtures/15_days.yaml` — 15 dní (min pre adaptáciu váh), mix vyplnených a prázdnych
- [X] T022 [P] [US1] Vytvoriť `server/tests/bdd/fixtures/30_days.yaml` — 30 dní, všetky elementy, boundary values (všetky 0, všetky max)
- [X] T023 [US1] Vytvoriť `server/app/routers/compute.py` — FastAPI router; `POST /api/v1/compute/daily` volá `index_calculator.compute_daily()`; `POST /api/v1/compute/range` iteruje cez `days`, volá `compute_daily()` pre každý; spracuje prázdne dni (`status: no_data`); zaregistrovať router v `main.py`
- [X] T024 [US1] Vytvoriť `server/tests/unit/test_index_calculator.py` — pytest unit testy pre `index_calculator.py`: (1) scalar element e_effective konverzia, (2) binary element, (3) negatívny impact (stress), (4) element so subpoložkami (C1), (5) prázdny vstup → None, (6) všetky elementy inactive → None; každý test porovnáva s ručne vypočítanou hodnotou
- [X] T025 [US1] Vytvoriť `server/tests/api/test_compute.py` — pytest + httpx testy pre compute endpointy: (1) `POST /daily` s valídnym telom → 200 + správny index, (2) `POST /daily` s neznámym element_key → 422, (3) `POST /range` s 3 dňami (1 prázdny) → 3 výsledky so správnymi statusmi, (4) schema_version prítomná v response

**Checkpoint**: `make test` + `python -c "import json; r=...; assert abs(r['index_value'] - 86.61) < 0.01"` — výpočet overený.

---

## Phase 4: User Story 2 — BDD testovacia suita (Priority: P2)

**Goal**: Behave BDD testy pokrývajú všetky výpočtové scenáre a sú spustiteľné offline.

**Independent Test**: `make test-bdd` — ≥10 scenárov, 0 failov, žiadne sieťové volania.

### Implementácia US2

- [X] T026 [US2] Vytvoriť `server/tests/bdd/environment.py` — behave hooks: `before_all` (spusti FastAPI test server v thread, čakaj na health), `after_all` (zastavenie), `before_scenario` (reset DB), `after_scenario` (cleanup); YAML fixture loader helper `load_fixture(name)`
- [X] T027 [P] [US2] Vytvoriť `server/tests/bdd/features/index_calculation.feature` — Feature: "ADHD Index Calculation"; scenáre: (1) Single day - sleep and overall feeling, (2) Day with subnode elements (C1 algorithm), (3) All elements maximum → index 100, (4) All elements zero → index 0, (5) Negative impact elements (stress) inverted, (6) Mixed positive and negative elements
- [X] T028 [P] [US2] Vytvoriť `server/tests/bdd/features/new_user_empty_state.feature` — Feature: "Empty state handling"; scenáre: (1) Empty days list → empty results no error, (2) Day with no values → status no_data, (3) Partial day (< 3 elements) → status partial, (4) All active_keys inactive → index null
- [X] T029 [P] [US2] Vytvoriť `server/tests/bdd/features/weight_adaptation.feature` — Feature: "Weight validation"; scenáre: (1) 1 element vs 3 elements rovnaká suma → rovnaký index, (2) Subnode parent weight nie je väčší ako root weight, (3) 15 dní fixture - adaptačná podmienka splnená
- [X] T030 [US2] Vytvoriť `server/tests/bdd/steps/compute_steps.py` — step implementations pre všetky feature súbory; používa `httpx` sync client; načíta YAML fixture cez `load_fixture()`; step "the index value is approximately {expected}" s toleranciou 0.01; step "the response status is {status}"
- [X] T031 [US2] Pridať `make test-bdd` target do `server/Makefile` — `cd server && python -m behave tests/bdd/features/ --no-capture`; overiť že beží offline (žiadne externé volania v behave steps)

**Checkpoint**: `make test-bdd` — výstup `N features passed, 0 failed` kde N ≥ 3.

---

## Phase 5: User Story 3 — API komunikácia a integračná analýza (Priority: P3)

**Goal**: API je zdokumentované a Swagger UI je dostupné; analýza Android integrácie je zakomponovaná v kóde.

**Independent Test**: `http://localhost:8000/docs` zobrazuje všetky endpointy; `GET /api/v1/compute/daily` má príklad request/response.

### Implementácia US3

- [X] T032 [P] [US3] Doplniť `server/app/main.py` — nastaviť FastAPI `title`, `description`, `version`, `contact`; pridať OpenAPI tags s popisom pre každú skupinu endpointov (Compute, Auth, Sync, Migrate, Health); pridať example response do každého endpointu v `compute.py` pomocou `responses=` parametra
- [X] T033 [P] [US3] Vytvoriť `server/app/schemas/compute.py` — pridať `model_config = ConfigDict(json_schema_extra={"example": {...}})` pre `ComputeDailyRequest` a `ComputeRangeRequest` s kompletným príkladom z contracts/compute.md
- [X] T034 [US3] Vytvoriť `server/app/routers/compute.py` — pridať `GET /api/v1/compute/android-integration` endpoint vracajúci JSON dokument s analýzou miest v Android appke (z research.md R-007): zoznam miest, odporúčanie update-only, komunikačný pattern; endpoint je verejný (bez auth)
- [X] T035 [US3] Vytvoriť `server/tests/api/test_openapi.py` — overenie že `GET /openapi.json` obsahuje všetky povinné endpointy (`/api/v1/compute/daily`, `/api/v1/compute/range`, `/api/v1/health`); schema_version prítomná v aspoň 1 example response

**Checkpoint**: `http://localhost:8000/docs` — všetky endpointy viditeľné s príkladmi.

---

## Phase 6: User Story 4 — Lokálne spustenie (Priority: P4)

**Goal**: Vývojár spustí server na čistom Linux stroji za < 5 minút.

**Independent Test**: Na čistom Ubuntu 22.04 + Python 3.11: `git clone && cd server && make dev` → server beží.

### Implementácia US4

- [X] T036 [US4] Dokončiť `server/Makefile` — `make dev`: (1) overenie Python ≥ 3.11 (`python3 --version`), (2) `pip install -e .` alebo `pip install -r requirements.txt`, (3) `cp .env.example .env` ak `.env` neexistuje, (4) `alembic upgrade head`, (5) `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`; `make clean`: odstráni SQLite dev.db + `__pycache__`
- [X] T037 [P] [US4] Vytvoriť `server/.env.example` — kompletný s komentármi: `DATABASE_URL=sqlite+aiosqlite:///./dev.db  # Change to PostgreSQL for production`, `SECRET_KEY=change-me-in-production`, `ENVIRONMENT=development`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=30`
- [X] T038 [P] [US4] Vytvoriť `server/README.md` — sekcie: Prerequisites, Quick Start (3 príkazy), Configuration (.env popis), Running tests, API docs URL, PostgreSQL setup (voliteľné)
- [X] T039 [US4] Pridať `server/tests/api/test_health.py` — overenie `/api/v1/health` response: `status == "ok"`, `db == "connected"`, `version` prítomná; test na SQLite fallback (bez PostgreSQL)

**Checkpoint**: `make dev` na čistom prostredí → `curl http://localhost:8000/api/v1/health` → `{"status": "ok"}`.

---

## Phase 7: User Story 5 — Autentifikácia (Priority: P5)

**Goal**: Registrácia a prihlásenie email + heslo; všetky sync/migrate endpointy chránené JWT.

**Independent Test**: Register → Login → access protected endpoint → 200; bez tokenu → 401.

### Implementácia US5

- [X] T040 [US5] Vytvoriť `server/app/services/auth_service.py` — `hash_password(plain)`, `verify_password(plain, hashed)` (passlib bcrypt); `create_access_token(data, expires_delta)`, `create_refresh_token(data)` (python-jose JWT); `decode_token(token)` → payload alebo `HTTPException 401`
- [X] T041 [P] [US5] Vytvoriť `server/app/schemas/auth.py` — Pydantic modely: `RegisterRequest` (email, password min 8 znakov), `LoginRequest`, `TokenResponse` (access_token, refresh_token, token_type, expires_in, schema_version), `RefreshRequest`
- [X] T042 [P] [US5] Vytvoriť `server/app/routers/auth.py` — `POST /api/v1/auth/register`: skontroluj unikátnosť emailu (409 ak existuje), hashuj heslo, ulož User, vráť TokenResponse; `POST /api/v1/auth/login`: overenie email+heslo (401 ak neplatné), vráť TokenResponse; `POST /api/v1/auth/refresh`: validuj refresh token, vráť nový access token
- [X] T043 [US5] Vytvoriť `server/app/dependencies.py` — FastAPI dependency `get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User`; dekóduje JWT, načíta User z DB; vráti 401 ak token neplatný alebo user neexistuje
- [X] T044 [US5] Zaregistrovať `auth` router v `server/app/main.py`; aplikovať `Depends(get_current_user)` na budúce chránené routery (sync, migrate) — zatiaľ ako placeholder
- [X] T045 [US5] Vytvoriť `server/tests/api/test_auth.py` — testy: (1) register nový email → 201 + tokeny, (2) register duplicitný email → 409, (3) login správne credentials → 200 + tokeny, (4) login nesprávne heslo → 401, (5) refresh platný token → 200 + nový access token, (6) chránený endpoint bez tokenu → 401, (7) chránený endpoint s platným tokenom → 200

**Checkpoint**: Register + login flow funguje; `/api/v1/health` je verejný; `/api/v1/sync/*` vráti 401 bez tokenu.

---

## Phase 8: User Story 6 — Offline Sync (Priority: P6)

**Goal**: Batch sync ≥30 dní offline dát s automatickým LWW conflict resolution.

**Independent Test**: BDD scenár `sync_offline.feature` — 7 offline dní syncnutých v jednom requeste, 1 konflikt vyriešený automaticky.

### Implementácia US6

- [X] T046 [US6] Vytvoriť `server/app/services/sync_service.py` — `process_batch_sync(user_id, days, device_id, db)`: pre každý deň (1) get-or-create `TrackingDay`, (2) LWW: ak `incoming.updated_at > stored.updated_at` → update + increment `records_accepted`, inak `records_conflicted`; uloží `SyncRecord` so summary; zavolá `index_calculator` pre každý prijatý deň; vráti `SyncResult` dataclass
- [X] T047 [P] [US6] Vytvoriť `server/app/schemas/sync.py` — Pydantic modely: `ElementValueSyncItem` (s `updated_at`), `DaySyncItem` (date, is_complete, updated_at, values list), `BatchSyncRequest` (schema_version, device_id, days), `ConflictRecord`, `SyncSummary`, `BatchSyncResponse` (schema_version, sync_id, summary, conflicts, computed_indices)
- [X] T048 [US6] Vytvoriť `server/app/routers/sync.py` — `POST /api/v1/sync/batch` (auth required): volá `sync_service.process_batch_sync()`; `GET /api/v1/sync/status` (auth required): vráti poslednú sync info pre user; `GET /api/v1/sync/indices` (auth required, query params `from_date`/`to_date`): vráti `DailyIndex` záznamy pre dané obdobie
- [X] T049 [US6] Zaregistrovať `sync` router v `server/app/main.py` s `Depends(get_current_user)`
- [X] T050 [P] [US6] Vytvoriť `server/tests/bdd/features/sync_offline.feature` — Feature: "Offline Batch Sync"; scenáre: (1) 7 dni offline → batch sync → 7 accepted, 0 conflicts; (2) 1 konflikt (mobile newer) → mobile_wins; (3) 1 konflikt (server newer) → server_wins; (4) Prázdny batch → 0 records, no error; (5) 30 dní sync < 10 sekúnd (performance scenár)
- [X] T051 [US6] Rozšíriť `server/tests/bdd/steps/` — pridať `sync_steps.py` so step implementáciami pre `sync_offline.feature`; performance test step meria elapsed time a assertion `< 10.0`
- [X] T052 [US6] Vytvoriť `server/tests/api/test_sync.py` — pytest API testy: (1) batch sync 3 dní (authenticated) → 200 + summary, (2) batch sync bez auth → 401, (3) sync s konfliktom → conflict log v response, (4) `GET /indices` vracia správne computed_indices pre date range

**Checkpoint**: `make test-bdd FEATURE=sync_offline` — všetky scenáre prechádzajú vrátane performance < 10s.

---

## Phase 9: User Story 7 — Migrácia existujúcich dát (Priority: P7)

**Goal**: Existujúci Android používateľ importuje historické dáta na server jedným API volaním.

**Independent Test**: POST `/api/v1/migrate` s 180 dňami → 200 + `days_imported: 178`, report o 2 skipped.

### Implementácia US7

- [X] T053 [US7] Vytvoriť `server/app/services/migration_service.py` — `process_migration(user_id, days, weight_config, strategy, db)`: strategy `mobile_source_of_truth` vždy prepíše; strategy `skip_existing` preskočí existujúce; importuje `WeightConfig`; vráti `MigrationResult` s counts a skipped list; idempotentné pre `skip_existing`
- [X] T054 [P] [US7] Vytvoriť `server/app/schemas/migrate.py` — Pydantic modely: `MigrationWeightItem`, `MigrationDayItem`, `MigrateRequest` (schema_version, source, migration_strategy Enum, days, weight_config), `MigrationSkipRecord`, `MigrationSummary`, `MigrateResponse`, `MigrateStatusResponse`
- [X] T055 [US7] Vytvoriť `server/app/routers/migrate.py` — `POST /api/v1/migrate` (auth required): validácia `migration_strategy` (422 ak neplatná), volá `migration_service.process_migration()`; `GET /api/v1/migrate/{migration_id}` (auth required): vráti stav migrácie z `SyncRecord` (type=migration)
- [X] T056 [US7] Zaregistrovať `migrate` router v `server/app/main.py` s `Depends(get_current_user)`
- [X] T057 [US7] Vytvoriť `server/tests/api/test_migrate.py` — pytest testy: (1) import 5 dní `mobile_source_of_truth` → 200 + 5 accepted, (2) import 5 dní `skip_existing` kde 2 existujú → 3 accepted + 2 skipped, (3) import bez auth → 401, (4) neplatná stratégia → 422, (5) `GET /migrate/{id}` → status completed, (6) weight_config import → WeightConfig záznamy v DB

**Checkpoint**: `make test` všetky API testy prechádzajú; migrácia je idempotentná.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Integrácia, kvalita, finalizácia.

- [X] T058 [P] Pridať `server/.gitignore` — `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dev.db`, `.env`, `*.egg-info/`, `.pytest_cache/`, `htmlcov/`
- [X] T059 [P] Pridať `pytest.ini` alebo `[tool.pytest.ini_options]` do `pyproject.toml` — `asyncio_mode = "auto"`, `testpaths = ["tests"]`, markers pre `unit`, `api`, `bdd`
- [X] T060 [P] Pridať `server/app/middleware/logging.py` — request logging middleware: method, path, status_code, elapsed_ms; bez loggingu request body (PII ochrana)
- [X] T061 Spustiť `make test-all` a opraviť všetky failing testy; overiť že coverage domény (`index_calculator.py`, `sync_service.py`) ≥ 80%
- [X] T062 Overiť backward compatibility: pridať dummy nové pole do `ComputeDailyResponse`, overiť že existujúce testy nevyhadzujú chybu (`extra='ignore'` v Pydantic config)
- [X] T063 Validovať quickstart.md scenáre SC-001 až SC-007 podľa `specs/012-server-algo/quickstart.md` — ručne alebo skriptom; dokumentovať výsledky
- [X] T064 Doplniť `server/README.md` — sekcie: PostgreSQL setup, Troubleshooting (common errors), Link na Swagger UI, Príklady curl príkazov pre každý endpoint

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Žiadna závislosť — môže začať okamžite
- **Phase 2 (Foundational)**: Závisí na Phase 1 — **blokuje všetky user stories**
- **Phase 3–9 (User Stories)**: Všetky závisia na Phase 2; môžu bežať v prioritnom poradí P1→P7
- **Phase 10 (Polish)**: Závisí na dokončených user stories

### User Story Dependencies

| Story | Závisí na | Nezávisí na |
|-------|-----------|------------|
| US1 (P1) | Phase 2 | — |
| US2 (P2) | US1 (YAML fixtures + compute endpoint) | US3–US7 |
| US3 (P3) | US1 (endpointy existujú) | US2, US4–US7 |
| US4 (P4) | Phase 2 (server beží) | US1–US3, US5–US7 |
| US5 (P5) | Phase 2 (User model) | US1–US4, US6–US7 |
| US6 (P6) | US5 (auth dependency) + US1 (index_calculator) | US2–US4, US7 |
| US7 (P7) | US5 (auth dependency) | US1–US4, US6 |

### Paralelné príležitosti

- **Phase 1**: T003, T004, T005 môžu bežať paralelne s T001
- **Phase 2**: T008, T009, T010, T011 môžu bežať paralelne po T007
- **Phase 3**: T017, T018–T022 môžu bežať paralelne po T016

---

## Parallel Example: User Story 1

```bash
# Po dokončení T016 (index_calculator), paralelne:
Task T017: "Vytvoriť schemas/compute.py"
Task T018: "Vytvoriť fixtures/1_day.yaml"
Task T019: "Vytvoriť fixtures/3_days.yaml"
Task T020: "Vytvoriť fixtures/5_days.yaml"
Task T021: "Vytvoriť fixtures/15_days.yaml"
Task T022: "Vytvoriť fixtures/30_days.yaml"

# Po T017 (schemas hotové):
Task T023: "Implement compute router"
Task T024: "Unit testy pre index_calculator"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Phase 1: Setup → Phase 2: Foundational
2. Phase 3: US1 — compute engine + fixtures
3. Phase 4: US2 — BDD testy
4. **STOP & VALIDATE**: `make test-all` → výpočet identický s Android
5. MVP je použiteľný ako regresný testovací nástroj

### Incremental Delivery

1. US1+US2 → Testovací server ✅
2. US4 → Easy-to-start ✅
3. US5 → Auth foundation ✅
4. US3 → API docs ✅
5. US6 → Sync ✅
6. US7 → Migrácia ✅

### Poradie pre jedného developera (odporúčané)

Phase 1 → Phase 2 → US1 → US2 → US4 → US5 → US6 → US7 → Polish
