# History

One line per completed spec (newest last). Details in `history/YYYY-MM-DD--food-NNN-*.md`.

- 2026-10-24 — Setup: constitution 2.0.0, Ralph loop scripts, food specs 001–011, import mapping (interactive, not a spec)
- 2026-10-24 — food-001: test runner `scripts/test-food.sh`, Playwright e2e harness, Django app `food`, ADHD | Food switch, responsive nav, vendored htmx + CSRF
- 2026-10-24 — food-002: invite-only registration (invitations + CLI), token refresh in web session (30 days), change password, account deletion (all apps), user settings (language, timezone)
- 2026-10-24 — food-003: food tables + migration (days, entries, weights, blood pressures, meds dictionary), food_constants, text normalization/splitting, quantity parser + duplicate merge, blood pressure/weight parsing, today in user timezone, food data in account deletion
- 2026-10-24 — food-004: day API (today, create/restore, read, values, soft delete, prev/next), /food/ with Today + add day, day screen with sections and HTMX autosave of sleep/stool/gas, delete day with 2 confirmations
