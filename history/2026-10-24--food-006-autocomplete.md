# food-006 — Autocomplete (2026-10-24)

## Decisions
- `services/food_suggestions.py`: grouping and counting in SQL, two bounded queries (top groups, then their
  spellings). "Last use" = latest day date, then latest `created_at` (imported history sorts by its real day).
- Join with `food_days` to exclude deleted days explicitly instead of relying on the cascade in `delete_day`.
- Django view `/food/suggestions/` returns JSON; the dropdown is rendered by `static/js/food_suggest.js`
  (no HTMX partial: keyboard navigation and replacing only the last part of the input need client state anyway).
- The keydown handler runs in the capture phase so Enter on a chosen suggestion does not submit the form and
  Esc on an open list does not cancel the inline edit (food_entries.js handlers run on body bubble).
- Tapping a suggestion: `mousedown` is prevented so the field keeps focus (focusout closes the list).

## Problems / lessons
- Shared in-memory SQLite across server tests: never look rows up by text/date only; get them via the id
  returned by the API (otherwise another test's user row is picked).
- Stale responses are dropped by a per-field sequence number (fast typing).
