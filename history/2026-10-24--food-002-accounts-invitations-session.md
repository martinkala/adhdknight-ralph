# food-002 — Accounts: invitations, long session, password change, account deletion, settings (2026-10-24)

## Decisions
- Invitation logic lives in `services/invitation_service.py`; the token is claimed with a conditional
  `UPDATE ... WHERE used_at IS NULL` in the same transaction as the user insert (rowcount check), so it
  cannot be used twice even under concurrent requests.
- SQLite returns naive datetimes for `DateTime(timezone=True)`; expiry comparison treats them as UTC.
- Account deletion (`services/account_service.py`) runs explicit bulk deletes, children first. Food tables
  from food-003+ must be added to `delete_account`.
- Web token refresh: `core.api_client.call_with_refresh` + `SessionExpired` exception handled by
  `core.middleware.SessionExpiredMiddleware`. All ADHD views use it; food uses `food.api_client.call`.
- Server tests: autouse fixture `open_registration` in `tests/conftest.py` monkeypatches the cached settings.
- e2e runs with `REGISTRATION_MODE=invite`; `user_factory` inserts invitations straight into the API SQLite DB.

## Problems / lessons
- Sync batch does not write `sync_records`/`weight_configs` and a one-element day gets no `daily_index`,
  so the deletion test seeds those rows directly.
- Local dev: with no `REGISTRATION_MODE` in `server/.env` the default is now `invite`; use
  `scripts/create_invitation.py` or set `REGISTRATION_MODE=open`.
