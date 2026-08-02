# Data Model: Migrácia servera na PostgreSQL — dátový migračný skript

**Feature**: 017 — SQLite → PostgreSQL dátová migrácia
**Date**: 2026-08-02

**Poznámka**: Táto feature nepridáva žiadne nové entity ani stĺpce — zdrojová (SQLite) aj cieľová (PostgreSQL) schéma sú **identické** (obe spravované rovnakými Alembic migráciami, viď `server/app/db/migrations/versions/`). Nižšie je len poradie prenosu a FK vzťahy existujúcich entít, relevantné pre správne fungovanie migračného skriptu.

---

## Poradie prenosu (podľa FK závislostí)

| # | Tabuľka | Model | FK závislosť | Poznámka |
|---|---|---|---|---|
| 1 | `users` | `User` | žiadna | koreň, musí ísť prvý |
| 2 | `tracking_days` | `TrackingDay` | `user_id → users.id` | |
| 3 | `element_values` | `ElementValue` | `tracking_day_id → tracking_days.id` | |
| 3 | `daily_indices` | `DailyIndex` | `tracking_day_id → tracking_days.id` (unique) | prenáša sa **presne tak, ako je** — pozri research.md Decision 4 |
| 4 | `weight_configs` | `WeightConfig` | `user_id → users.id` | |
| 5 | `sync_records` | `SyncRecord` | `user_id → users.id` | |

`element_values` a `daily_indices` sú na rovnakej úrovni (obe závisia len na `tracking_days`, nie jedna na druhej) — poradie medzi nimi je ľubovoľné.

---

## Kľúčové polia relevantné pre migráciu

| Tabuľka | PK | Unique constraints (MUST sa zachovať) | Typy vyžadujúce pozornosť pri type coercion |
|---|---|---|---|
| `users` | `id` (UUID string) | `email` | `is_active` (Bool), `created_at`/`last_sync_at` (`DateTime(timezone=True)`) |
| `tracking_days` | `id` | `(user_id, app_id, date)` | `is_complete` (Bool) |
| `element_values` | `id` | `(tracking_day_id, element_key)` | `value_binary` (Int), `value_scale` (nullable Int), `value_effective` (Float) |
| `daily_indices` | `id` | `tracking_day_id` (unique 1:1) | `index_value` (Float), `detail_json` (Text — JSON-serialized string, prenáša sa ako string, neparsuje sa) |
| `weight_configs` | `id` | `(user_id, app_id, element_key)` | `weight_default`/`weight_personal` (Float, nullable) |
| `sync_records` | `id` | žiadny | `sync_type` (Enum: `batch`/`single`/`migration` — SQLAlchemy `Enum` musí existovať v Postgres ako `sync_type` typ; už vytvorené Alembic migráciou) |

**Validačné pravidlo (FR-005)**: počet riadkov v cieľovej PostgreSQL MUST byť presne rovnaký ako v zdrojovej SQLite, pre každú tabuľku samostatne — toto je hlavná runtime-overiteľná podmienka SC-003.

---

## MigrationRun (konceptuálna entita skriptu, nie DB tabuľka)

Skript pri behu drží v pamäti súhrn (vypisuje na stdout pri dokončení, pozri `contracts/cli-contract.md`):

| Pole | Popis |
|---|---|
| `source_path` | cesta k zdrojovému SQLite súboru |
| `destination_url` | cieľová PostgreSQL (bez hesla v logu) |
| `rows_per_table` | `{tabuľka: (zdroj_count, cieľ_count)}` |
| `status` | `success` \| `aborted_non_empty_destination` \| `failed_rollback` |
