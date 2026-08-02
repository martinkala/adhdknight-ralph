---

description: "Task list for the SQLite → PostgreSQL data migration script (017-migration-to-postgres)"
---

# Tasks: Migrácia servera na PostgreSQL

**Input**: Design documents from `/specs/017-migration-to-postgres/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md

**Scope note**: FR-001–FR-003 and SC-001–SC-002 are already implemented and verified in production (018-migration-to-server). This task list covers only the remaining gap: FR-004/FR-005 — the `server/scripts/migrate_sqlite_to_postgres.py` script itself.

**Tests**: Included — Constitution VI requires tests for domain-adjacent server logic, and the data-loss risk here is high-stakes. Tests use two temporary SQLite databases (source + destination) instead of a live PostgreSQL, per plan.md/research.md Decision 8, so `make test` stays offline-runnable.

**Organization**: Single user story (US1, P1) — spec.md has exactly one. Tasks are still labeled `[US1]` for traceability.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- File paths are relative to repo root (`/home/martin/projects/adhdmad`)

---

## Phase 1: Setup

- [X] T001 Create `server/scripts/` directory (does not exist yet)

**Checkpoint**: Scaffolding exists.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared skeleton the transfer logic and its tests both depend on

- [X] T002 Create `server/scripts/migrate_sqlite_to_postgres.py` skeleton: CLI arg parsing (positional source path, default `./dev.db`; `--force` flag), imports existing models from `app.models`, `app.config.get_settings()` for destination URL (data-model.md, contracts/cli-contract.md)
- [X] T003 Implement destination-URL validation in `server/scripts/migrate_sqlite_to_postgres.py`: exit 1 with a clear message if `get_settings().is_sqlite` is `True` (research.md Decision 7)
- [X] T004 Implement source-file validation in `server/scripts/migrate_sqlite_to_postgres.py`: exit 1 with a clear message including the resolved path if the source SQLite file doesn't exist
- [X] T005 Implement the non-empty-destination guard in `server/scripts/migrate_sqlite_to_postgres.py`: `SELECT COUNT(*) FROM users` on destination; exit 1 with contracts/cli-contract.md's exact message unless `--force` is passed (research.md Decision 5) (depends on T002)

**Checkpoint**: Script can be invoked, validates its inputs, and refuses unsafe runs — no data transfer yet.

---

## Phase 3: User Story 1 - Migrácia servera na PostgreSQL (Priority: P1) 🎯 MVP

**Goal**: Transfer all rows from the source SQLite `dev.db` into the destination PostgreSQL `adhd_server` database, in FK-safe order, inside one transaction, with zero data loss and zero recomputation of historical index values.

**Independent Test**: Run the script against a seeded temp SQLite source and an empty temp SQLite "destination" (per research.md Decision 8) — row counts match per table, FK references resolve, `daily_indices.index_value` is byte-identical to the source.

### Tests for User Story 1

> Write these first, confirm they fail before implementing T011–T014.

- [X] T006 [P] [US1] Add a seed-fixture helper in `server/tests/unit/test_migrate_sqlite_to_postgres.py` that creates a temp SQLite "source" DB with sample rows across all 6 tables (`users`, `tracking_days`, `element_values`, `daily_indices`, `weight_configs`, `sync_records`), respecting FK relationships (data-model.md)
- [X] T007 [US1] Test: full successful transfer — every table's destination row count equals its source row count, and FK values (`tracking_days.user_id`, `element_values.tracking_day_id`, etc.) still resolve correctly in the destination (depends on T006)
- [X] T008 [US1] Test: guard rejects a run against a non-empty destination — exit code `1`, destination row counts unchanged after the attempt (depends on T005)
- [X] T009 [US1] Test: `--force` allows a re-run against a non-empty destination (depends on T005)
- [X] T010 [US1] Test: a simulated failure mid-transfer (e.g. inject an exception after `tracking_days` but before `element_values`) leaves the destination completely empty afterward — full rollback, not partial (research.md Decision 6)
- [X] T011 [US1] Test: `daily_indices.index_value`/`detail_json`/`config_version` in the destination are byte-identical to the source — never recomputed via `index_calculator` (research.md Decision 4, Constitution Principle II)

### Implementation for User Story 1

- [X] T012 [US1] Implement the FK-ordered transfer functions in `server/scripts/migrate_sqlite_to_postgres.py`: `users` → `tracking_days` → (`element_values`, `daily_indices`) → `weight_configs` → `sync_records` (data-model.md), copying every column verbatim including primary keys (research.md Decision 3)
- [X] T013 [US1] Wrap the full transfer in a single destination transaction in `server/scripts/migrate_sqlite_to_postgres.py`: commit only after all 6 tables succeed, `rollback()` and exit `2` on any exception (research.md Decision 6, contracts/cli-contract.md) (depends on T012)
- [X] T014 [US1] Implement the completion summary output in `server/scripts/migrate_sqlite_to_postgres.py`: print per-table `source_count → dest_count`, exit `0` on success (contracts/cli-contract.md) (depends on T013)

**Checkpoint**: US1 fully functional — `T006`–`T011` all pass against the implementation from `T012`–`T014`.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T015 [P] Run quickstart.md Scenario 1 (local dry run against a local/dockerized PostgreSQL) and record the result
- [X] T016 [P] Run quickstart.md Scenario 2 (guard against duplicate run) manually against the same local PostgreSQL
- [X] T017 Run `cd server && make test` — confirm the new test file passes and no existing test changed behavior
- [X] T018 Add a short "Dátová migrácia zo SQLite" note to `server/README.md` (near the existing "PostgreSQL Setup" section) pointing at the script and `specs/017-migration-to-postgres/quickstart.md`
- [ ] T019 Run quickstart.md Scenarios 3–5 on the actual production server (`app01`) once a real `dev.db` is available to copy over — requires server access, same manual/deferred pattern as 018's T017/T022/T023/T024

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS Phase 3 (transfer logic needs the validated, guarded skeleton to build on)
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion; tests (T006–T011) should be written before implementation (T012–T014) and confirmed failing first
- **Polish (Phase 4)**: Depends on Phase 3 completion

### Parallel Opportunities

- T015, T016 (Phase 4) — independent manual verification steps
- T006 can be written in parallel with T002–T005 (different file), though it depends on the fixture helper being usable before T007 onward runs

---

## Parallel Example: Phase 3 tests

```bash
# T006 (fixture helper) can be written alongside the Phase 2 skeleton work:
Task: "Add seed-fixture helper creating temp SQLite source DB with sample rows"
```

---

## Implementation Strategy

### MVP First (and only) — single user story

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (skeleton, validations, guard)
3. Complete Phase 3: User Story 1 (tests first, then the transfer implementation)
4. **STOP and VALIDATE**: `make test` green, then quickstart.md Scenarios 1–2 locally
5. Phase 4 closes out documentation and the production-server validation (Scenarios 3–5), which — like 018's equivalent tasks — requires real server access and is expected to be run manually when a real `dev.db` is ready to migrate.
