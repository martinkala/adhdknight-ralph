# food-008 — Calendar and list (2026-10-24)

## Decisions
- `services/food_overview.py` holds the calendar and the days list; endpoints live in `routers/food_days.py`
  (`GET /calendar`, `GET /days` next to `GET /days/{date}`). Children of a page of days are loaded with one
  `IN` query per table, no N+1.
- Month selection uses a string range on `food_days.date` (`YYYY-MM-01` … `YYYY-MM-31`), works on SQLite and Postgres.
- `severity` added to the API responses (server owns the bands 1–3 / 4–6 / 7–10).
- Calendar grid: Python `calendar.Calendar(firstweekday=MONDAY).monthdatescalendar`, rendered as a flat CSS grid
  of 7 `minmax(0, 1fr)` columns; card padding 0.25 rem and 1 px gaps keep cells ≥ 44 px at 360 px.
- All missing days share one POST form (one CSRF token); buttons carry `name=date value=...`.
- `FakeApi` in Django tests now also records `params`.

## Problems / lessons
- `base.html` styles every `nav` element (blue bar). Food sub-navigation uses `div role="navigation"`.
- The delete-day e2e assertion changed: deleting returns to `/food/?month=YYYY-MM`.
