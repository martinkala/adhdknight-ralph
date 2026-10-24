# food-005 — Entries and measurements (2026-10-24)

## Decisions
- Entry logic in `services/food_entries.py`, measurement CRUD in `services/food_measurement_records.py`
  (the pure parsers stay in `food_measurements.py`). One router `routers/food_entries.py` for both.
- All domain errors reuse `FoodDayError(code)`; the router maps 404/409 codes and defaults to 422.
- `split_entries` keeps a decimal comma between digits (`0,5 l kofoly`); found by an e2e screenshot.
- `fill_time` flag on POST weights / blood-pressures: the server fills the user's local time on today's day.
- HTMX errors come back as HTTP 200 + `X-Food-Error` header so the list can show the message in place
  and the e2e "no 4xx in network" check holds.
- Quick add clears the field in `htmx:configRequest` (parameters already collected) and restores the text
  on error; `hx-sync="this:queue all"` keeps fast consecutive Enters in order.
- Template filter library `food/templatetags/food_format.py` (`qty`, `number`, `bp_raw`).

## Problems / lessons
- e2e: interacting with freshly swapped HTMX content right away can be too early (hx-* attributes are
  processed during settle). `_settled(page)` in `e2e/test_food_entries.py` waits for no `.htmx-*` state classes.
- Whitespace inside a button breaks exact text regex assertions; keep chip markup on one line.
- Text with `<br>` inside a flex container loses line breaks; notes use `white-space: pre-line` instead.
- Weight add form with a `type=time` input overflowed 360 px; the time input needs an explicit width.
