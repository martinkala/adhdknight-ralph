# API Contracts: Android App ↔ FastAPI Server (Account, Auth, Sync)

**Server base URL**: configured in Settings (e.g. `http://192.168.1.10:8095`)
**Auth**: JWT Bearer token in `Authorization` header (`OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`)
**Client timeouts**: 5s for auth/me/reachability calls; 30s for `/sync/batch` (`ApiClient.kt`)

This supersedes `specs/016-application-server-connect/contracts/api-contracts.md`, which was written before the refresh-token flow existed — see spec.md "Odchýlky od pôvodných specs" for the full list of what changed.

---

## POST /api/v1/auth/register

**Request**:
```json
POST {serverUrl}/api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}
```
Server validates `password` length ≥ 8 (Pydantic validator, 422 if shorter).

**Response — success (201)**:
```json
{
  "schema_version": "1.0",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Response — conflict (409)**:
```json
{ "detail": "Email already registered" }
```

**Client behavior** (`UserRepository.register`):
- On success, immediately calls `login(email, password)` (server returns tokens directly on register too, but the client re-logs-in rather than using the register response tokens directly).
- On 409 → "Účet s týmto emailom už existuje".
- On connection error → "Server nie je dostupný".

---

## POST /api/v1/auth/login

**Request**:
```json
POST {serverUrl}/api/v1/auth/login
Content-Type: application/json

{ "email": "user@example.com", "password": "secret123" }
```

**Response — success (200)**: same `TokenResponse` shape as register.

**Response — error (401)**:
```json
{ "detail": "Invalid credentials" }
```

**Client behavior** (`UserRepository.login`):
- Stores `access_token` (+ `refresh_token` if non-blank) in `EncryptedSharedPreferences`.
- Calls `GET /api/v1/user/me` to fill in display info; if that call fails, still reports login success with `totalDays=0, createdAt=""`.
- 401 → "Nesprávne prihlasovacie údaje".
- 409 → "Účet s týmto emailom už existuje" (only relevant from the register→login chain).
- Connection error → "Server nie je dostupný".
- Timeout → "Server neodpovedá, skúste neskôr".

---

## POST /api/v1/auth/refresh

**Request**:
```json
POST {serverUrl}/api/v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "eyJ..." }
```

**Response — success (200)**: `TokenResponse` (new access + refresh token pair — refresh token is rotated, not reused).

**Response — error (401)**: invalid/expired/wrong-type token → `{"detail": "Not a refresh token"}` or `{"detail": "Invalid or expired token"}` or `{"detail": "User not found"}`.

**Client behavior** (`UserRepository.refreshAccessToken`, private):
- Only invoked from inside `syncAll()` on a 401 from `/sync/batch` — **not** wired up for other 401s (e.g. a stale token hitting `/user/me` directly is not currently retried).
- On success, both tokens are re-saved.
- On failure, returns `null` and the caller surfaces "Prihlásenie vypršalo, prihláste sa znova" — session is **not** cleared automatically.

---

## GET /api/v1/user/me

**Request**:
```
GET {serverUrl}/api/v1/user/me?app_id=adhd_tracker
Authorization: Bearer {access_token}
```
`app_id` query param, default `"adhd_tracker"` — scopes `total_days` to that app's `tracking_days` rows only. `email`/`created_at` are account-level and identical regardless of `app_id`.

**Response — success (200)**:
```json
{ "email": "user@example.com", "created_at": "2026-06-01T08:00:00", "total_days": 42 }
```

**Response — invalid token (401)**:
```json
{ "detail": "Could not validate credentials" }
```

**Client behavior**: called right after login/register and on app start if a session already exists (`AccountViewModel.init`), always passing its own `app_id` (e.g. `APP_ID` constant in `ApiClient.kt`). No explicit 401-refresh handling on this call in the current client — a 401 here surfaces as a generic error rather than triggering refresh (asymmetry with `/sync/batch`, worth normalizing in the new app).

---

## GET /api/v1/user/history

**Request**:
```
GET {serverUrl}/api/v1/user/history?days=30&app_id=adhd_tracker
Authorization: Bearer {access_token}
```
`days` query param: 1–90, default 30. `app_id` query param, default `"adhd_tracker"`.

**Response — success (200)**:
```json
{
  "schema_version": "1.0",
  "days": [
    {
      "date": "2026-07-24",
      "index_value": 72.5,
      "detail": [
        { "element_key": "sleep", "value_effective": 0.75, "weight": 15.0, "contribution": 11.25, "impact": 1 }
      ]
    }
  ],
  "total_days": 1
}
```

**Not currently called from the Android client** in the code reviewed (no reference in `ApiClient.kt`/`UserRepository.kt`) — server-only / web-app-facing endpoint today. `detail` is shaped around the ADHD index calculation (`weight`/`contribution`/`impact` come straight from `IndexCalculator`), so it is **not domain-neutral** — a new app needs its own equivalent if it wants a server-side history view of its own computed metric.

---

## POST /api/v1/sync/batch

**Request**:
```json
POST {serverUrl}/api/v1/sync/batch
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "schema_version": "1.0",
  "app_id": "adhd_tracker",
  "device_id": null,
  "days": [
    {
      "date": "2026-07-24",
      "is_complete": false,
      "updated_at": "2026-07-24T20:15:00Z",
      "values": [
        { "element_key": "sleep", "value_binary": 1, "value_scale": 4, "note": null, "updated_at": "2026-07-24T20:15:00Z" }
      ]
    }
  ]
}
```
`app_id` (default `"adhd_tracker"`) scopes which app's `TrackingDay` this batch writes to — see data-model.md "App scoping". `device_id` is accepted but the current client always sends `null` (see data-model.md). `element_key` is free-form — this endpoint has no knowledge of the ADHD tracker's specific element set, so a new app can sync arbitrary keys through it unmodified, and even reuse the same key name as another app (e.g. both apps having a `"sleep"` element) without collision, since `app_id` disambiguates them.

**Response — success (200)**:
```json
{
  "sync_id": "uuid",
  "summary": {
    "days_received": 1,
    "records_sent": 1,
    "records_accepted": 1,
    "records_conflicted": 0,
    "records_rejected": 0
  },
  "conflicts": [],
  "computed_indices": []
}
```
`computed_indices` is always `[]` in the current implementation — declared in the schema but never populated by `sync_service.py`.

**Server-side algorithm** (`sync_service.process_batch_sync`):
1. Days with a future `date` are entirely rejected (`resolution: "rejected_future_date"`), all their values counted in `records_rejected`.
2. `TrackingDay` is get-or-created per `(user_id, app_id, date)`.
3. For each `ElementValueSyncItem`: get-or-create `ElementValue` by `(tracking_day_id, element_key)`.
   - New element → inserted as-is, counted `records_accepted`.
   - Existing element → **LWW by `updated_at`**: incoming newer → overwrite, `records_accepted`; incoming not newer → server keeps its value, `records_conflicted` + a `ConflictRecord{date, element_key, resolution: "server_wins"}` is appended.
4. Naive (timezone-less) timestamps from SQLite are coerced to UTC before comparison.
5. Single `db.commit()` at the end of the whole batch (not per-day).

**Client behavior** (`UserRepository.syncAll`):
- Reads **all** local days/values (no incremental/delta sync — full resync every time).
- On 401, refreshes token once and retries the whole batch; does not retry a second time.
- 401 after failed refresh → "Prihlásenie vypršalo, prihláste sa znova".
- Connection error → "Server nie je dostupný". Timeout → "Server neodpovedá, skúste neskôr". Anything else → "Synchronizácia zlyhala".

---

## GET /api/v1/sync/status

**Request**:
```
GET {serverUrl}/api/v1/sync/status?app_id=adhd_tracker
Authorization: Bearer {access_token}
```
`app_id` query param, default `"adhd_tracker"`.

**Response — success (200)**:
```json
{ "user_id": "uuid", "app_id": "adhd_tracker", "total_days_synced": 42 }
```
`total_days_synced` counts only `TrackingDay` rows for the given `app_id`.

Not currently called from the Android client in the code reviewed.

---

## Complete error-state map

| Situation | HTTP / Exception | UI message |
|---|---|---|
| Wrong password / unknown account (login) | 401 | "Nesprávne prihlasovacie údaje" |
| Password < 8 chars (register) | 422 | Client now prevents this case (Register button disabled + inline hint below 8 chars); if it ever reaches the server anyway, still falls into generic "Registrácia zlyhala" |
| Email already exists (register) | 409 | "Účet s týmto emailom už existuje" |
| Server unreachable | `ConnectException` / `IOException` | "Server nie je dostupný" |
| Refresh token invalid/expired | 401 on `/auth/refresh` | Sync surfaces "Prihlásenie vypršalo, prihláste sa znova"; session is left intact (not cleared) |
| Timeout (> configured timeout) | `SocketTimeoutException` | "Server neodpovedá, skúste neskôr" |
| Empty server URL | (local validation, no request sent) | "Zadajte URL servera v nastaveniach" |
| Not logged in, sync attempted | (local check, no request sent) | "Prihláste sa pred synchronizáciou" |

---

## Notes for the new app

- HTTP (not HTTPS) is accepted for `localhost` / `10.0.2.2` per `network_security_config.xml`; all other hosts require HTTPS (`cleartextTrafficPermitted="false"` base config). Reuse this file as-is.
- `minSdk 26`, `targetSdk 34`, `compileSdk 34`, Kotlin `jvmTarget 17` — match these unless there's a specific reason to diverge (keeps shared code/modules buildable together if ever merged).
- Ktor client config to reuse verbatim: `HttpClient(Android) { ContentNegotiation(json) ; HttpTimeout(5_000ms request+connect) }`, with a per-call `timeout { requestTimeoutMillis = 30_000 }` override for the sync endpoint only.
- Define one `const val APP_ID = "food_diary"` (mirroring `ApiClient.APP_ID` in the existing app) and pass it on every call that accepts `app_id` — `/sync/batch` (body), `/migrate` (body), `/user/me`, `/user/history`, `/sync/status` (query param). This is what makes the shared account/server model work without data collisions — see data-model.md "App scoping".
