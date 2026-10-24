# food-001 — Skeleton and test harness (2026-10-24)

## Decisions
- `scripts/test-food.sh` keeps a sha256 of `requirements.txt` inside each venv (`.requirements.sha256`)
  and reinstalls only when it changes; a broken venv (`bin/python -c pass` fails) is recreated.
- Active app for the `ADHD | Food` switch comes from a context processor (`core.context_processors.active_app`),
  not from template blocks, so the switch and CSS `active` class work for every page.
- `TEMPLATES.APP_DIRS = True` so app templates (`web_app/food/templates/food/`) are found.
- htmx 2.0.4 vendored at `web_app/static/js/htmx.min.js` (loaded in `base.html` head); CSRF via `hx-headers` on `<body>`.
- Fixed the pre-existing failing ADHD test per the sync contract (`test_sync_batch_tomorrow_is_rejected`), server code untouched.

## Problems / lessons
- Output written to stderr from session-fixture teardown is swallowed by pytest capture; server logs on
  failure are printed via `pytest_terminal_summary` instead.
- Servers run in their own process group (`start_new_session=True`) and are killed with `killpg` in fixture finalizers.
- The ADHD dashboard still loads Chart.js from a CDN, so the "no console errors on /" e2e check needs network.
- The container has no `ps`/`pgrep`; check leftover processes via `/proc/*/cmdline`.
