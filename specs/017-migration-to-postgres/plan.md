# Implementation Plan: Migrácia servera na PostgreSQL

**Branch**: `017-migration-to-postgres` | **Date**: 2026-08-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-migration-to-postgres/spec.md`

---

## Summary

FR-001–FR-003 (server nasaditeľný s PostgreSQL, `.env`-driven switch, Alembic proti Postgres) sú už implementované a overené v produkcii vďaka `018-migration-to-server` nasadeniu. Zostávajúci scope tejto feature je úzky: **jeden CLI skript**, `server/scripts/migrate_sqlite_to_postgres.py`, ktorý prenesie existujúce riadky zo zdrojového SQLite (`dev.db`) do produkčnej PostgreSQL databázy `adhd_server` — bez straty dát, transakčne, s guardom proti duplicitnému behu. 018's `deploy/scripts/install.sh` už na tento presný súbor odkazuje ako na externú závislosť.

---

## Technical Context

**Language/Version**: Python 3.11+ (rovnaké ako zvyšok `server/`; produkcia beží 3.12 cez pyenv-postavený interpreter mimo `/root`, viď 018)

**Primary Dependencies**: SQLAlchemy 2.0 (async) — rovnaké modely z `server/app/models/`, `aiosqlite` (zdroj), `asyncpg` (cieľ) — všetky už v `server/requirements.txt`, žiadna nová závislosť

**Storage**: Číta `server/dev.db` (SQLite), zapisuje do produkčnej `adhd_server` PostgreSQL databázy (`DATABASE_URL` z `server/.env`)

**Testing**: `pytest`, nová testovacia trieda v `server/tests/unit/test_migrate_sqlite_to_postgres.py` — používa dve dočasné SQLite databázy (zdroj + cieľ) namiesto živého PostgreSQL, aby zostalo `make test` offline-spustiteľné (Constitution VI). Reálna PostgreSQL kompatibilita sa overuje cez `quickstart.md` na produkčnom serveri.

**Target Platform**: CLI skript spúšťaný na produkčnom serveri (súčasť `deploy/scripts/install.sh --step migrate-data`, 018) alebo lokálne pre suchý beh

**Project Type**: Jeden Python skript v rámci existujúceho `server/` projektu (nie samostatný projekt/balík)

**Performance Goals**: Nešpecifikované nad rámec — dev-scale objem dát (jeden vývojár, rádovo stovky až nízke tisícky riadkov), jednorazový beh per nasadenie

**Constraints**:
- MUST byť transakčný — pri akejkoľvek chybe kompletný rollback, cieľová DB ostane nezmenená (research.md Decision 6)
- MUST odmietnuť beh, ak cieľová DB nie je prázdna, bez `--force` (research.md Decision 5)
- MUST zachovať existujúce UUID hodnoty (žiadny ID remapping, research.md Decision 3)
- MUST prenášať `daily_indices` bez prepočtu (research.md Decision 4 — Constitution Principle II)
- MUST rešpektovať presný CLI kontrakt, na ktorý sa 018 už odkazuje (`contracts/cli-contract.md`)

**Scale/Scope**: 6 tabuliek (`users`, `tracking_days`, `element_values`, `daily_indices`, `weight_configs`, `sync_records`), 1 skript, 1 testovací súbor

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Rovnako ako 018, aj táto feature je serverová/dátová infraštruktúra mimo scope Android-špecifickej constitution (MVVM/Compose/Room/index-algoritmus na strane appky sa nemenia).

| Princíp | Status | Poznámka |
|---|---|---|
| I. Architektúra (MVVM/Repository) | ✅ N/A | Netýka sa `android_app/` |
| II. Doménová logika indexu | ✅ PASS | Skript **neprepočítava** index — `daily_indices` sa kopírujú presne tak, ako boli vypočítané (research.md Decision 4), takže sa vyhýba akémukoľvek riziku zmeny hodnôt/parametrov, ktoré by vyžadovalo zdôvodnenie v PR |
| III. Dátový model (Room) | ✅ N/A | Žiadne Room entity; PostgreSQL schéma je nezmenená (rovnaká ako pred touto feature) |
| IV. UX | ✅ N/A | Bez UI dopadu — CLI nástroj pre operátora |
| V. Notifikácie | ✅ N/A | Nedotknuté |
| VI. Testovanie | ✅ PASS | Nová testovacia trieda (dve SQLite DB, offline, deterministické) pokrýva transfer logiku, guard, aj rollback |
| VII. Tech stack | ✅ PASS | Žiadna nová závislosť — SQLAlchemy/aiosqlite/asyncpg už v `requirements.txt` |

**Výsledok: PASS — žiadne bloky, žiadny Complexity Tracking záznam potrebný.**

## Project Structure

### Documentation (this feature)

```text
specs/017-migration-to-postgres/
├── plan.md                    ← tento súbor
├── research.md                ← 8 rozhodnutí: ORM prístup, poradie prenosu, UUID bez remappingu, kópia bez prepočtu, idempotency guard, transakčnosť, zdroj/cieľ config, testovanie bez živého Postgres
├── data-model.md              ← poradie tabuliek podľa FK, kľúčové polia, MigrationRun (konceptuálny súhrn behu)
├── contracts/
│   └── cli-contract.md        ← invokácia, vstupy, exit kódy — kontrakt s 018's install.sh
├── quickstart.md              ← 5 validačných scenárov (lokálny dry-run, guard, produkčný beh, počty riadkov, funkčné overenie cez API)
└── checklists/
    └── requirements.md        ← spec quality checklist, všetko PASS
```

### Source Code (repository root)

```text
server/
├── scripts/
│   └── migrate_sqlite_to_postgres.py   # NOVÝ — samotný migračný skript (kontrakt s 018)
└── tests/
    └── unit/
        └── test_migrate_sqlite_to_postgres.py   # NOVÝ — dve dočasné SQLite DB (zdroj+cieľ), offline testy
```

**Structure Decision**: Jeden nový skript v `server/scripts/` (adresár zatiaľ neexistuje, vytvorí sa) + jeden testovací súbor v existujúcej `server/tests/unit/` štruktúre. Žiadne zmeny v `server/app/` (aplikačný kód, modely, Alembic) — tie sú už hotové a nemenia sa.

## Complexity Tracking

*Žiadne porušenia Constitution Check — táto sekcia sa nevyžaduje.*
