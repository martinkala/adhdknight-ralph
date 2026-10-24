# food-009 — Export and changes (2026-10-24)

## Decisions
- `services/food_export.py` builds `FoodExport` (reuses `_children_by_day` / `_measurement_order` from
  `food_overview.py`) and the long-format CSV; `services/food_changes.py` serves `/changes`. Both endpoints live
  in `routers/food_export.py`.
- JSON entries always carry `intensity` (null outside sport), so every entry has the same keys (pandas friendly).
  The `FoodExport` item models have defaults, so food-011 can parse LLM output that omits empty fields.
- File name `food-diary-<from>-<to>.<ext>`: a missing end is the first / last exported day, or today without days.
  `from > to` → 422 `invalid_range`.
- CSV: BOM + `csv.DictWriter` (RFC 4180, CRLF); numbers via `Decimal(repr(x)).normalize()` → `2`, `0.5`, `80.6`.
  Row order per day: day values, entries in D2 category order, weights, blood pressures.
- `/changes` paging: the oldest `limit + 1` rows of each table give the oldest `limit + 1` overall, sorted by
  `(updated_at, id)`. A page never splits a group with the same `updated_at` (deleting a day stamps the day and
  all children with one time); if one group is larger than the limit the whole group is returned. With
  `has_more` the `server_time` is the last `updated_at` of the page, otherwise the time before the queries.
- `server_time` uses the real clock, not `get_now` (tests fake `get_now`, `updated_at` is always real).
- Web: `/food/export/` is a GET form (no CSRF needed for a download); `api_client.download` returns raw bytes
  and headers, `call_download` goes through `call_with_refresh`.

## Problems / lessons
- `delete_day` set `updated_at` on children explicitly but the day got its own `onupdate` time a moment later;
  now the day uses the same `now`, so a day tombstone and its children are one group.
- SQLite returns naive datetimes; `/changes` makes every timestamp UTC-aware before comparing and serializing.
