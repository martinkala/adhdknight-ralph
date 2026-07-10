# Feature Specification: Migrácia servera na PostgreSQL

**Feature Branch**: `017-migration-to-postgres`

**Created**: 2026-07-10

**Status**: Draft

**Prerekvizita**: 016-application-server-connect (F1 — server connectivity)

---

## Kontext a účel

FastAPI server aktuálne beží so SQLite databázou. SQLite postačuje pre lokálny vývoj, ale nie je vhodný pre produkčné nasadenie (limity pri súbežných pripojeniach, žiadna replikácia). Táto feature migruje server na PostgreSQL — SQLite zostáva pre lokálny vývoj.

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
- **FR-004**: Dátová migrácia zo SQLite do PostgreSQL MUST prebehnúť cez migračný skript bez straty dát.

### Non-functional Requirements

- SQLite zostáva default pre `make dev` — lokálny vývoj nesmie vyžadovať PostgreSQL.
- Existujúce API testy prechádzajú bez zmeny testovacieho kódu po migrácii.

---

## Success Criteria *(mandatory)*

- **SC-001**: Po migrácii na PostgreSQL prechádzajú všetky existujúce API testy bez zmeny testovacieho kódu.
- **SC-002**: `DATABASE_URL=postgresql://...` v `.env` → server štartuje s PostgreSQL bez ďalšej konfigurácie.
- **SC-003**: Migračný skript prenesie 100% záznamov zo SQLite do PostgreSQL bez straty.

---

## Assumptions

- PostgreSQL je nainštalovaný na produkčnom serveri (nie je súčasťou tejto feature).
- SQLite zostáva default pre lokálny vývoj aj po tejto migrácii.
- Alembic sa používa pre správu schémy (už integrovaný v serveri).
