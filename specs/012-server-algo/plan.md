# Implementation Plan: Backend Weight Vector Server

**Branch**: `012-server-algo` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

## Summary

Python FastAPI server, ktorý implementuje identický výpočet ADHD denného indexu ako Android appka. Primárny účel je regresné testovanie algoritmu a príprava infraštruktúry pre budúci produkčný sync. Server je standalone Python projekt v adresári `server/` v koreňovom repozitári. Databáza: PostgreSQL pre produkciu, SQLite pre lokálny dev. Testy: BDD (behave) + pytest s YAML fixturami.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- FastAPI 0.111+ (async web framework, auto-generated OpenAPI docs)
- Pydantic v2 (request/response validácia a serializácia)
- SQLAlchemy 2.x async (ORM)
- Alembic (DB migrácie)
- uvicorn (ASGI server)
- psycopg2-binary / asyncpg (PostgreSQL driver)
- aiosqlite (SQLite pre dev)
- passlib[bcrypt] (password hashing)
- python-jose (JWT tokeny)
- behave (BDD test runner)
- pytest + httpx (unit + API testy)
- PyYAML (YAML fixture loader)

**Storage**:
- PostgreSQL 14+ — primárna (produkcia, CI)
- SQLite — dev/localhost alternatíva (env var prepínač)

**Testing**: pytest + behave (BDD feature files) + httpx async test client

**Target Platform**: Linux server (Ubuntu 20.04+), localhost development bez root

**Project Type**: Web API service (REST, JSON)

**Performance Goals**:
- Batch sync 30 dní < 10 sekúnd na bežnom hardvéri
- Single compute request < 500ms p99
- BDD testy bežia offline a deterministicky

**Constraints**:
- Offline-first na Android strane — server je opt-in doplnok
- Spustenie bez root/sudo
- Bez externých sieťových závislostí v testoch
- API backward compatible — additive-only zmeny

**Scale/Scope**: Vývojový + testovací nástroj. Prvá fáza: <50 používateľov, testovacia prevádzka.

## Constitution Check

| Princíp | Stav | Poznámka |
|---------|------|----------|
| I. MVVM architektura | ✅ N/A pre server | Android strana zostáva bez zmeny |
| II. Domenova logika indexu | ✅ MUSÍ | Server reimplementuje identický vzorec; pokrytý unit + BDD testami |
| III. Datový model | ✅ Čiastočne | Server má vlastnú DB schému; Android Room schéma sa nemení |
| IV. UX pravidlá | ✅ N/A | Server nemá UI |
| V. Notifikácie | ✅ N/A | |
| VI. Testovanie | ✅ MUSÍ | Každá zmena výpočtu musí mať test; BDD + unit pokrytie |
| VII. Tech stack | ⚠️ Nová závislosť | Server je nový projekt — nepridáva závislosť do Android app |
| Post-MVP scope | ⚠️ Podmienečne | Server = testovací nástroj ✅; centralizovaný výpočet pre produkciu ostáva post-MVP |

**Gate**: PASS — server nie je náhradou Android výpočtu, je aditívny doplnok.

## Project Structure

### Documentation (this feature)

```text
specs/012-server-algo/
├── plan.md              ← tento súbor
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── compute.md
│   ├── auth.md
│   ├── sync.md
│   └── migrate.md
└── tasks.md             ← generuje /speckit-tasks
```

### Source Code

```text
server/
├── app/
│   ├── main.py                  # FastAPI app, router registration
│   ├── config.py                # Settings cez env vars (pydantic-settings)
│   ├── models/                  # SQLAlchemy ORM modely
│   │   ├── user.py              # User
│   │   ├── tracking.py          # TrackingDay, ElementValue, DailyIndex
│   │   ├── weights.py           # WeightConfig
│   │   └── sync.py              # SyncRecord
│   ├── schemas/                 # Pydantic request/response schémy
│   │   ├── tracking.py
│   │   ├── auth.py
│   │   ├── sync.py
│   │   └── compute.py
│   ├── routers/                 # FastAPI routers (jeden súbor = jeden domain)
│   │   ├── auth.py              # /api/v1/auth/*
│   │   ├── compute.py           # /api/v1/compute/*
│   │   ├── sync.py              # /api/v1/sync/*
│   │   └── migrate.py           # /api/v1/migrate
│   ├── services/                # Business logika (bez HTTP závislostí)
│   │   ├── index_calculator.py  # Port IndexCalculator z Androidu
│   │   ├── weight_service.py    # Adaptácia váh
│   │   └── sync_service.py      # Conflict resolution, batch processing
│   └── db/
│       ├── database.py          # SQLAlchemy engine + async session factory
│       └── migrations/          # Alembic migrations (versions/)
├── tests/
│   ├── unit/                    # pytest — čistá logika bez HTTP
│   │   ├── test_index_calculator.py
│   │   └── test_weight_service.py
│   ├── api/                     # pytest + httpx — endpoint testy
│   │   ├── test_compute.py
│   │   ├── test_auth.py
│   │   └── test_sync.py
│   └── bdd/                     # behave BDD
│       ├── features/
│       │   ├── index_calculation.feature
│       │   ├── weight_adaptation.feature
│       │   ├── sync_offline.feature
│       │   └── new_user_empty_state.feature
│       ├── steps/
│       │   └── *.py
│       └── fixtures/            # Human-editable YAML
│           ├── 1_day.yaml
│           ├── 3_days.yaml
│           ├── 5_days.yaml
│           ├── 15_days.yaml
│           └── 30_days.yaml
├── Makefile                     # make dev, make test, make migrate
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

**Structure Decision**: Single Python project v `server/` adresári. Android kód zostáva v `android_app/`. Nie je monorepo Python balík — jednoduchý flat `server/app/` layout.

## Complexity Tracking

| Item | Why Needed | Alternative Rejected |
|------|------------|---------------------|
| SQLAlchemy async | Batch sync + concurrent requests bez blocking | Sync SQLAlchemy: blokuje event loop pri batch operáciách |
| Alembic | Schéma sa bude meniť (additive migrations) | Ručné ALTER TABLE: netrackuje históriu |
| behave (BDD) | Human-readable scenáre pre doménového experta | Len pytest: nie je čitateľný pre non-technika |
| JWT auth | Stateless, funguje pre mobile + budúci web | Session cookies: nevhodné pre mobile klienta |
