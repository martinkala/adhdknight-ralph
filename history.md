# History

One line per completed spec (newest last). Details in `history/YYYY-MM-DD--food-NNN-*.md`.

- 2026-10-24 — Setup: constitution 2.0.0, Ralph loop scripts, food specs 001–011, import mapping (interactive, not a spec)
- 2026-10-24 — food-001: test runner `scripts/test-food.sh`, Playwright e2e harness, Django app `food`, ADHD | Food switch, responsive nav, vendored htmx + CSRF
- 2026-10-24 — food-002: invite-only registration (invitations + CLI), token refresh in web session (30 days), change password, account deletion (all apps), user settings (language, timezone)
- 2026-10-24 — food-003: food tables + migration (days, entries, weights, blood pressures, meds dictionary), food_constants, text normalization/splitting, quantity parser + duplicate merge, blood pressure/weight parsing, today in user timezone, food data in account deletion
- 2026-10-24 — food-004: day API (today, create/restore, read, values, soft delete, prev/next), /food/ with Today + add day, day screen with sections and HTMX autosave of sleep/stool/gas, delete day with 2 confirmations
- 2026-10-24 — food-005: entries API (split, quantity parsing, merge, edit, soft delete, most used quantities), weights + blood pressures API (raw quick entry, fill_time), day screen quick add with focus, inline edit, quantity popover, sport intensity, notes, BP/weight UI
- 2026-10-24 — food-006: suggestions API (word-start match without diacritics, grouped by text_norm, by count then last use, groups, LIKE escaping), web autocomplete listbox on quick add and inline edit (last part without quantity, choose adds single item, keyboard, max 8 on mobile)
- 2026-10-24 — food-007: med dictionary API (list, upsert with moving entries on kind change, soft delete), entries in med categories fill the dictionary, common `/meds` input with `+` splitting and `needs_classification`, web: one meds field, classification dialog, move action, `/food/settings/meds/` dictionary page
- 2026-10-24 — food-008: calendar API (month, severity, entry counts) and paginated days list API with summaries, /food/ month calendar (Monday weeks, severity dots + legend, tap creates a missing day, future disabled, ?month), /food/list/ with pagination, back to the day's month
- 2026-10-24 — food-009: JSON export (`FoodExport`) and long-format CSV export with BOM, `/changes` with tombstones and group-safe paging, day delete stamps one `updated_at`, `/food/export/` download page + nav link
- 2026-10-24 — food-010: Django i18n sk/cs/en (English msgids, committed .po/.mo, babel compile script), LanguageMiddleware (session → cookie → sk), translated layout/login/registration/account/food, localized dates and decimals, language select on account page + cookie switch on login/registration, E2E_LANGUAGE harness option
