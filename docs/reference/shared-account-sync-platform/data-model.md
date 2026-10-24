# Data Model: Shared Account, Login & Sync Platform

**Extracted from**: `android_app` (client) + `server` (FastAPI), current code as of 2026-07-25.

---

## Android client — local storage

### ServerConfig (plain `SharedPreferences`, file `adhd_prefs`)

| Key | Type | Default | Notes |
|---|---|---|---|
| `server_url` | String | `""` | Empty = server disabled. Normalized on write: trailing `/` stripped. |

Source: `PreferencesRepository.kt`.

### UserSession (`EncryptedSharedPreferences`, file `adhd_secure_prefs`, AES256_SIV keys / AES256_GCM values via `MasterKey.AES256_GCM`)

| Key | Type | Default | Notes |
|---|---|---|---|
| `access_token` | String | `""` | JWT, short-lived (15 min server default). |
| `refresh_token` | String | `""` | JWT, long-lived (30 days server default). |
| `user_email` | String | `""` | Display only. |

Source: `EncryptedPreferencesRepository.kt`. `clearSession()` removes all three keys on logout.

### UI state (in-memory, not persisted)

```
AccountUiState
├── LoggedOut
├── Loading
├── LoggedIn(email: String, totalDays: Int, createdAt: String)
└── Error(message: String)

SyncUiState
├── Idle
├── Syncing
├── Done(accepted: Int, conflicted: Int)
└── Error(message: String)
```

Source: `AccountViewModel.kt`.

### Sync payload shape (client → server), from `ApiClient.kt`

```
SyncValueItem(element_key: String, value_binary: Int, value_scale: Int?, updated_at: String, note: String? = null)
SyncDayItem(date: String, is_complete: Boolean = false, updated_at: String, values: List<SyncValueItem>)
BatchSyncRequest(schema_version: String = "1.0", app_id: String = "adhd_tracker", device_id: String? = null, days: List<SyncDayItem>)
```

`app_id` scopes a day's data to the app that wrote it — see "App scoping" section below. A new app just sets its own constant (e.g. `"food_diary"`); no server-side registration of app ids is required.

`element_key` is an opaque string — the sync layer does not know or care what it means, so a new app can use its own set of keys freely as long as they don't need to be distinguished from another app's keys within the same `(user_id, date)` row (see spec.md "Otvorené otázky" #1).

`updated_at` on `SyncDayItem` is currently reused as the `updated_at` for **every** value in that day (`UserRepository.syncAll()` sets `values.map { ... updated_at = day.updatedAt ... }`) — i.e. the client does not currently track per-element timestamps locally, only per-day. This limits how precise the server's per-element LWW resolution can be for same-day edits; worth revisiting if the new app needs finer-grained conflict resolution.

---

## Server — persisted entities (SQLAlchemy models)

### `users` (`app/models/user.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | UUID |
| `email` | String(255), unique, indexed | |
| `password_hash` | String(255) | bcrypt via `passlib` |
| `created_at` | DateTime(tz) | default now |
| `last_sync_at` | DateTime(tz), nullable | present in schema, **not currently written anywhere** — dead column |
| `is_active` | Boolean | default true |

Relationships: `tracking_days`, `weight_configs`, `sync_records` (all cascade delete).

### `tracking_days` (`app/models/tracking.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | UUID |
| `user_id` | FK → `users.id`, CASCADE | |
| `app_id` | String(50), default `"adhd_tracker"` | which app owns this day's data — see "App scoping" |
| `date` | String(10) | `YYYY-MM-DD`, indexed |
| `is_complete` | Boolean | client-supplied flag |
| `created_at` / `updated_at` | DateTime(tz) | `updated_at` has `onupdate` |
| `device_id` | String(255), nullable | accepted but never populated by the current client |

`UniqueConstraint(user_id, app_id, date)` — **one row per user, per app, per calendar day.** Two apps can independently own a `TrackingDay` for the same date under the same account.

### `element_values` (`app/models/tracking.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | UUID |
| `tracking_day_id` | FK → `tracking_days.id`, CASCADE | |
| `element_key` | String(100), indexed | free-form, app-defined |
| `value_binary` | Integer | default 0 |
| `value_scale` | Integer, nullable | |
| `value_effective` | Float | default 0.0 — **note: column exists but `sync_service.py` never sets it on write**, only `value_binary`/`value_scale`/`note`/`updated_at` are written during sync |
| `note` | String(250), nullable | |
| `updated_at` | DateTime(tz) | used for LWW comparison |

`UniqueConstraint(tracking_day_id, element_key)`.

### `daily_indices` (`app/models/tracking.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | |
| `tracking_day_id` | FK → `tracking_days.id`, unique | one index per day |
| `index_value` | Float | |
| `detail_json` | Text, nullable | JSON-encoded `[{element_key, value_effective, weight, contribution, impact}]` |
| `computed_at` | DateTime(tz) | |
| `config_version` | String(20) | default `"1.0"` |

This table is **domain-specific to the ADHD index** — a new app's own computed metric (if any) would need an analogous but separately-named table, not a reuse of this one, since `/user/history` reads directly from it.

### `sync_records` (`app/models/sync.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | |
| `user_id` | FK → `users.id`, CASCADE | |
| `app_id` | String(50), default `"adhd_tracker"` | |
| `device_id` | String(255), nullable | |
| `sync_type` | Enum(`batch`, `single`, `migration`) | |
| `records_sent` / `records_accepted` / `records_conflicted` / `records_rejected` | Integer | |
| `conflict_log` | Text, nullable | |
| `synced_at` | DateTime(tz) | |

**Note:** this table is defined and related to `User`, but `sync_service.process_batch_sync()` never actually inserts a row into it — the per-sync summary is only returned in the API response, not persisted server-side. Worth fixing if audit history across devices/apps is wanted.

### `weight_configs` (`app/models/weights.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | String(36), PK | |
| `user_id` | FK → `users.id`, CASCADE | |
| `app_id` | String(50), default `"adhd_tracker"` | |
| `element_key` | String(100) | |
| `weight_default` / `weight_personal` | Float | |
| `updated_at` | DateTime(tz) | |

`UniqueConstraint(user_id, app_id, element_key)`. Populated by `POST /api/v1/migrate` (`weight_config` payload); not written by `/sync/batch`.

---

## App scoping

One `users` row (one email+password, one JWT) can own data across any number of apps. Isolation between apps happens entirely through the `app_id` string column added to `tracking_days`, `weight_configs`, and `sync_records` — there is no fixed enum or registration table for app ids; a new app just starts sending its own string (e.g. `"food_diary"`) and gets its own isolated rows automatically.

| Concern | How it's scoped |
|---|---|
| `POST /api/v1/sync/batch` | `app_id` in request body, default `"adhd_tracker"` |
| `POST /api/v1/migrate` | `app_id` in request body, default `"adhd_tracker"` |
| `GET /api/v1/user/me` | `app_id` query param, default `"adhd_tracker"` — scopes `total_days`; `email`/`created_at` are account-level, not app-scoped |
| `GET /api/v1/user/history` | `app_id` query param, default `"adhd_tracker"` |
| `GET /api/v1/sync/status` | `app_id` query param, default `"adhd_tracker"` |

Migration: `server/app/db/migrations/versions/c3d4e5f6a7b8_add_app_id_scoping.py` (Alembic `batch_alter_table`, verified upgrade/downgrade on SQLite; compatible with PostgreSQL). Existing rows are backfilled to `app_id = "adhd_tracker"`, so pre-existing single-app deployments and clients that don't send `app_id` at all keep working unchanged.

Verified in `server/tests/api/test_multi_app.py`: two apps writing the same `element_key` for the same date under the same account do not conflict or overwrite each other; `/sync/status` and `/user/me` report counts scoped to the requesting app only.

---

## JWT token payload

```
{
  "sub": "<user_id>",
  "type": "access" | "refresh",
  "exp": <unix timestamp>
}
```

Signed HS256 with `settings.secret_key`. Access token: 15 min default (`access_token_expire_minutes`). Refresh token: 30 days default (`refresh_token_expire_days`). Both configurable via `.env`.

---

## Validation rules

| Field | Rule |
|---|---|
| `server_url` | Must start with `http://` or `https://`, or be empty. Trailing slash stripped on save. |
| `email` | Standard email validation (Pydantic `EmailStr` server-side). |
| `password` | Server enforces ≥ 8 characters (`RegisterRequest.password_min_length` validator); client UI now matches (`MIN_PASSWORD_LENGTH = 8` in `AccountScreen.kt`). |
| `access_token` / `refresh_token` | Stored as-is; expiry handled server-side (401 response), not client-side pre-validation. |
