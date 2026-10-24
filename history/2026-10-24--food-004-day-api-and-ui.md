# food-004 — Day API and day screen (2026-10-24)

## Decisions
- `services/food_days.py` holds all day logic (create/restore, values, soft delete with children,
  `day_detail` incl. `prev_date`/`next_date`). Errors are `FoodDayError(code)`; the router maps codes to HTTP status.
- `schemas/food.py` has `DayDetail`, `Entry`, `Weight`, `BloodPressure` for food-005+. Quantities/kg are floats in JSON.
- Clock is the `get_now` dependency in `app/dependencies.py`; tests override it (`fake_now` fixture in `test_food_days.py`).
- `food/api_client.request` now returns the API `detail` string as `error` for 4xx (e.g. `day_exists`), `invalid_input`
  for validation errors; `status_code` is always included.
- Day screen: values partial `_day_values.html` + `_value_button.html` (toggle encoded in `hx-vals`), styles in
  `static/css/food.css`, delete dialogs in `static/js/food_day.js`.
- English msgids in templates; real sk/cs/en texts come with food-010.

## Problems / lessons
- The server test DB is shared for the whole session and services commit, so every test registers a unique email.
- htmx PATCH bodies are form-encoded: read them with `QueryDict(request.body)` in Django.
- e2e: wait for `aria-pressed` after each value tap before the next one (the partial is swapped).
