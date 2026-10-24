# food-011 — Import and merge (2026-10-24)

## Decisions
- Two services: `food_import_parser.py` (pure: text → `ParsedImport` with days, issues, skipped empty days,
  unknown columns) and `food_import_merge.py` (`plan_import` reads the user's data, `commit_import` stores the plan).
  The router `routers/food_import.py` builds the preview from the plan; commit re-parses and re-plans.
- Header columns are matched by `normalize()` (trim, lower case, no diacritics), so `Spánok`, `sport ` work.
  Unknown names are reported, blank and `pohyb` are ignored. Legacy columns (`wlk`, `end`, ...) raise
  `unsupported_format_legacy`. A paste starting with a date row uses the 2026.csv column order (`default_header` issue).
- Duplicates are a multiset per day (`Counter` of category + text_norm + quantity + unit; weight kg + time;
  BP values + time), so re-importing the same sheet skips everything.
- Meds of TSV/CSV are sorted by the dictionary, then by `classify`; the dictionary is filled for every imported
  med entry (`med_dictionary.stage`). JSON meds already carry their category.
- One transaction: `_apply` only flushes; `commit_import` commits once or rolls back and re-raises.
  Explicit increasing `created_at` keeps the measurement order, so export → import → export is identical.
- Web: plain POST form (`action=preview|commit`), conflicts / classification as hidden paired lists
  (`conflict`+`choice`, `classify_norm`+`classify_kind`), small `food_import.js` for the choice buttons,
  "Use for all" and enabling Import. API calls of the import use a 60 s timeout (`api_client.call(timeout=...)`).

## Problems / lessons
- `FakeApi` in Django tests had a fixed signature; it now accepts `timeout`.
- A newline inside an unquoted TSV cell starts a new row — test inputs with multi-line cells must be quoted
  (Google Sheets quotes them on copy).
