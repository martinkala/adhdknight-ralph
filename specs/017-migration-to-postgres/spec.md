# Feature Specification: Migrácia servera na PostgreSQL

**Feature Branch**: `017-migration-to-postgres`

**Created**: 2026-07-10

**Status**: Draft

**Prerekvizita**: 016-application-server-connect (F1 — server connectivity)

---

## Kontext a účel

FastAPI server aktuálne beží so SQLite databázou. SQLite postačuje pre lokálny vývoj, ale nie je vhodný pre produkčné nasadenie (limity pri súbežných pripojeniach, žiadna replikácia). Táto feature migruje server na PostgreSQL — SQLite zostáva pre lokálny vývoj.

**Stav implementácie (aktualizované 2026-08-02, po produkčnom nasadení 018-migration-to-server)**:
FR-001, FR-002 a FR-003 sú **už implementované a overené v produkcii** — `server/app/config.py` prepína SQLite↔PostgreSQL cez `DATABASE_URL` bez zmeny kódu, a na produkčnom serveri (`api.adhdknight.com`) bežia Alembic migrácie (`alembic upgrade head`) čisto proti PostgreSQL 16 (databáza `adhd_server`, rola rovnakého mena, viazaná len na `localhost` — pozri `specs/018-migration-to-server/data-model.md` PostgresDatabase). Jediný zostávajúci gap je **FR-004** — samotný skript na prenos existujúcich riadkov zo SQLite `dev.db` do tejto PostgreSQL databázy. 018 tento skript volá (`server/scripts/migrate_sqlite_to_postgres.py`), ale zámerne ho neimplementuje — je to scope tejto feature.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Migrácia servera na PostgreSQL (Priority: P1)

Server prejde z SQLite na PostgreSQL databázu. SQLite zostáva pre lokálny vývoj a testovanie. PostgreSQL sa použije pre produkčné nasadenie.

**Why this priority**: SQLite má limity pri viacerých súbežných pripojeniach a nie je vhodný pre produkčné nasadenie na vzdialenom serveri.

**Independent Test**: Spusti server s PostgreSQL konfiguráciou → existujúce API testy prechádzajú bez zmeny. Dáta importované do SQLite sú prenesené do PostgreSQL bez straty.

**Acceptance Scenarios**:

1. **Given** PostgreSQL je nainštalovaný a nakonfigurovaný v `.env`, **When** server štartuje, **Then** všetky API endpointy fungujú identicky ako so SQLite.
2. **Given** existujú dáta v SQLite dev databáze, **When** prebehne migračný skript, **Then** všetky záznamy sú prenesené do PostgreSQL bez straty dát.
3. **Given** server beží s PostgreSQL, **When** sa spustia existujúce testy, **Then** všetky prechádzajú bez zmeny testovacieho kódu.

### Edge Cases

- Čo ak PostgreSQL migrácia zlyhá na polovici? → Alembic transakcie zabezpečia rollback — databáza ostane v konzistentnom stave.
- Čo ak `.env` neobsahuje DATABASE_URL? → Server štartuje so SQLite fallbackom (lokálny vývoj).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Server MUST byť nasaditeľný s PostgreSQL databázou v produkcii; SQLite zostáva pre lokálny vývoj.
- **FR-002**: Prepínanie medzi SQLite a PostgreSQL MUST byť cez `.env` premennú `DATABASE_URL` bez zmeny kódu.
- **FR-003**: Existujúce Alembic migrácie MUST fungovať s PostgreSQL bez zmeny.
- **FR-004**: Dátová migrácia zo SQLite do PostgreSQL MUST prebehnúť cez migračný skript bez straty dát. Skript MUST byť na ceste `server/scripts/migrate_sqlite_to_postgres.py` — na tento presný path sa už odkazuje `deploy/scripts/install.sh` (018) ako na externú závislosť; zmena cesty by vyžadovala zodpovedajúcu zmenu aj v 018.
- **FR-005**: Skript MUST prenášať dáta pre všetky tabuľky vlastnené `adhd_server` databázou — `users`, `tracking_days`, `element_values`, `daily_indices`, `weight_configs`, `sync_records` (pozri `server/app/models/`) — s zachovaním cudzích kľúčov a `app_id` scopingu (016).

### Non-functional Requirements

- SQLite zostáva default pre `make dev` — lokálny vývoj nesmie vyžadovať PostgreSQL.
- Existujúce API testy prechádzajú bez zmeny testovacieho kódu po migrácii.

---

## Success Criteria *(mandatory)*

- **SC-001**: Po migrácii na PostgreSQL prechádzajú všetky existujúce API testy bez zmeny testovacieho kódu. ✅ **Overené** — `make test` prechádza rovnako so SQLite aj PostgreSQL (018 produkčné nasadenie).
- **SC-002**: `DATABASE_URL=postgresql://...` v `.env` → server štartuje s PostgreSQL bez ďalšej konfigurácie. ✅ **Overené v produkcii** (`api.adhdknight.com`, `alembic upgrade head` prešiel čisto proti PostgreSQL 16).
- **SC-003**: Migračný skript prenesie 100% záznamov zo SQLite do PostgreSQL bez straty. ⬜ **Zostáva** — toto je jediné neoverené/neimplementované SC tejto feature.

---

## Assumptions

- PostgreSQL je nainštalovaný na produkčnom serveri (nie je súčasťou tejto feature) — na produkcii (`app01`) beží `postgresql-16` z oficiálneho PGDG repozitára (distro default 13 bol nedostatočný pre Django 6 v rámci 018, preto sa inštaluje takto).
- Databáza `adhd_server` a rovnomenná rola už na produkcii existujú (vytvorené inštalačným skriptom 018, `deploy/scripts/install.sh --step databases`), viazané len na `localhost`.
- SQLite zostáva default pre lokálny vývoj aj po tejto migrácii.
- Alembic sa používa pre správu schémy (už integrovaný v serveri) — schéma je už na produkcii plne migrovaná (`51a4112e7c48` → `a1b2c3d4e5f6` → `c3d4e5f6a7b8`), táto feature rieši len presun **dát**, nie schémy.
- Zdrojové dáta pre migráciu sú v `server/dev.db` (lokálny SQLite súbor vývojára) — táto feature nešpecifikuje mechanizmus prenosu súboru `dev.db` na produkčný server (napr. `scp`); to je manuálny krok operátora pred spustením skriptu.
