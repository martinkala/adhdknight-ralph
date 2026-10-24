# Specification: food-001 — Kostra Food diary a testovacia infraštruktúra

## Feature: Food diary skeleton, prepínač appiek, jednotný test runner a Playwright e2e

### Overview
Pripraví základ, na ktorom stoja všetky ďalšie food specs: Django app `food`, prepínač appiek
v navigácii, HTMX, jeden príkaz na spustenie všetkých testov (`scripts/test-food.sh`) a e2e harness,
ktorý spustí skutočný FastAPI + Django proti dočasnej databáze. Bez tohto nemá Ralph spätnú väzbu.

### User Stories
- Ako vývojár (Ralph) chcem jedným príkazom spustiť všetky testy, aby som vedel, či je spec hotová.
- Ako používateľ chcem v konzole prepínať medzi ADHD a Food, aby som mal oba nástroje pod jedným loginom.

---

## Functional Requirements

### FR-1: Test runner `scripts/test-food.sh`
Skript v koreni repa (spustiteľný, bash, `set -euo pipefail`):
1. Názov venv priečinka je `${VENV_NAME:-.venv}` (Ralph v Dockeri používa `.venv-docker`,
   `scripts/ralph-docker/`). Ak venv neexistuje alebo je nefunkčný (`<venv>/bin/python -c pass` zlyhá),
   vytvorí `server/<venv>`, `web_app/<venv>`, `e2e/<venv>` (`python3 -m venv`) a nainštaluje závislosti
   (`server/requirements.txt`, `web_app/requirements.txt`, `e2e/requirements.txt`).
   Reinštalácia iba ak sa zmenil requirements súbor (porovnanie hashu uloženého vo venv).
   Všetky ďalšie kroky (aj e2e harness) používajú tento `<venv>`, nie natvrdo `.venv`.
2. Spustí server testy: `cd server && <venv>/bin/pytest tests/unit tests/api -q`.
3. Spustí Django testy: `cd web_app && <venv>/bin/python manage.py test -v 1` (všetky appky).
4. Spustí e2e: `e2e/<venv>/bin/pytest e2e -q` (preskočí sa s `--no-e2e`).
5. Exit code ≠ 0, ak zlyhá ktorýkoľvek krok. Na konci vypíše súhrn `server: OK|FAIL, web: OK|FAIL, e2e: OK|FAIL|SKIPPED`.

**Acceptance Criteria:**
- [ ] `./scripts/test-food.sh` na čistom checkoute (bez venv) vytvorí venvs a skončí s exit 0
- [ ] Zámerne rozbitý test v ktorejkoľvek časti → exit ≠ 0 a súhrn ukáže FAIL pri danej časti
- [ ] `./scripts/test-food.sh --no-e2e` nespúšťa Playwright
- [ ] `VENV_NAME=.venv-docker ./scripts/test-food.sh` použije a vytvorí `.venv-docker` venvy a hostiteľské `.venv` nechá nedotknuté
- [ ] Existujúce ADHD testy (server aj web) bežia a prechádzajú

### FR-1a: Známy pokazený ADHD test
`server/tests/api/test_future_date.py::test_sync_batch_tomorrow_returns_422` zlyháva už na `master`
(nesúvisí s food). `/api/v1/sync/batch` budúci deň neodmietne s 422. Vráti 200, deň započíta do
`records_rejected` a pridá konflikt `resolution: "rejected_future_date"`. Tak to opisuje aj kontrakt
v `docs/reference/shared-account-sync-platform/contracts/api-contracts.md`.
**Oprav test podľa kontraktu, nie server kód:** premenuj ho na `test_sync_batch_tomorrow_is_rejected`,
over status 200, `summary.records_rejected > 0` a konflikt `rejected_future_date`. Ostatné ADHD testy nemeň.

**Acceptance Criteria:**
- [ ] `cd server && <venv>/bin/pytest tests/unit tests/api -q` → 0 failed
- [ ] `app/services/sync_service.py` a `app/routers/sync.py` sú nezmenené

### FR-2: E2E harness (`e2e/`)
- `e2e/requirements.txt`: `pytest`, `pytest-playwright`, `httpx`. Prehliadač Chromium cez
  `e2e/.venv/bin/playwright install chromium` (urobí to `test-food.sh`, ak chýba).
- `e2e/conftest.py`, session fixtures:
  - `api_server`: dočasný SQLite súbor v `tmp_path_factory`, `DATABASE_URL` naň, `alembic upgrade head`
    (cez `server/.venv/bin/alembic` s `cwd=server`), potom `server/.venv/bin/uvicorn app.main:app`
    na voľnom porte na `127.0.0.1`. Čaká na `GET /api/v1/health` (max. 20 s).
    Env: `SECRET_KEY` testovací, `REGISTRATION_MODE=open` (food-002 to zmení na pozvánky).
  - `web_server`: `web_app/.venv/bin/python manage.py runserver 127.0.0.1:<port> --noreload`
    s `FASTAPI_URL` na `api_server`, `DJANGO_DEBUG=true`, vlastná dočasná SQLite DB pre sessions
    (`DJANGO_DATABASE_URL` nepoužiť; pridaj env `DJANGO_SQLITE_PATH`, ktorý settings rešpektuje, default `db.sqlite3`).
    Pred štartom `manage.py migrate`.
  - `user_factory`: vytvorí používateľa cez API (unikátny email) a vráti `(email, password)`.
  - `logged_in_page`: Playwright `page` prihlásený cez UI login formulár.
- Procesy sa po session ukončia (aj pri páde testu). Logy servera a webu sa pri zlyhaní vypíšu.
- Mobilný viewport: fixture `mobile_page` (360 × 740, `is_mobile=True`).
- **Selektory v e2e testoch výhradne cez `data-testid`**, nie cez texty (UI bude viacjazyčné).

**Acceptance Criteria:**
- [ ] `e2e/test_smoke.py::test_login_and_switch_to_food` prejde: login → ADHD dashboard → klik na „Food“ → `/food/`
- [ ] `e2e/test_smoke.py::test_mobile_nav_no_horizontal_scroll` prejde: na 360 px `document.documentElement.scrollWidth <= 360`
- [ ] Po skončení testov nebeží žiadny uvicorn ani runserver proces spustený harnessom

### FR-3: Django app `food`
- `web_app/food/` (apps, urls, views, templates `web_app/food/templates/food/`), zaregistrovaná
  v `INSTALLED_APPS`, URL prefix `/food/` v `adhd_web/urls.py`.
- `web_app/food/api_client.py` pre volania `/api/v1/food/*`, rovnaký štýl ako `core/api_client.py`
  (httpx, timeout 5 s, chyby `server_unavailable` / `unauthorized` / `server_error`).
- `/food/` vyžaduje login (inak redirect na `login`) a zobrazí placeholder stránku
  s `data-testid="food-home"`.
- Všetky nové UI texty vo `food` sa píšu cez `gettext` / `{% translate %}` s **anglickým msgid**
  (preklady sk/cs pridá food-010). `LANGUAGE_CODE` ostáva zatiaľ bez zmeny.

**Acceptance Criteria:**
- [ ] Django test: neprihlásený GET `/food/` → 302 na login
- [ ] Django test: prihlásený GET `/food/` → 200 a obsahuje `data-testid="food-home"`

### FR-4: Prepínač appiek a responzívna navigácia
- V `core/templates/base.html` prepínač `ADHD | Food` (`data-testid="app-switch-adhd"`, `"app-switch-food"`),
  aktívna appka je zvýraznená. ADHD odkazy (Dashboard, Trend, Info, Diagnostika) sa zobrazujú
  iba v ADHD časti, food odkazy iba vo Food časti (blok `{% block app_nav %}`). Účet a Odhlásiť sú vždy.
- Na šírke < 600 px sa navigácia zalomí alebo zbalí do menu (`data-testid="nav-toggle"`), bez horizontálneho scrollu.
- Existujúce ADHD stránky fungujú ako doteraz.

**Acceptance Criteria:**
- [ ] Django testy ADHD (`core`) prechádzajú bez zmeny ich asercií
- [ ] Na `/food/` je aktívny prepínač Food, na `/` aktívny ADHD (Django test na CSS triedu `active`)

### FR-5: HTMX a CSRF
- `web_app/static/js/htmx.min.js` (htmx 2.x, verzia v komentári na 1. riadku, stiahnuté raz a commitnuté, bez CDN).
- `base.html` načíta htmx a nastaví `hx-headers` s CSRF tokenom na `<body>`.

**Acceptance Criteria:**
- [ ] e2e: na `/food/` je `window.htmx` definované a v konzole prehliadača nie sú chyby

### FR-6: Dokumentácia
- `docs/food/README.md`: architektúra (FastAPI = logika, Django = UI), lokálne spustenie,
  `./scripts/test-food.sh`, e2e, predpoklady (Python 3.11+, Chromium závislosti).

**Acceptance Criteria:**
- [ ] `docs/food/README.md` existuje a príkazy v ňom fungujú

---

## Success Criteria
- Celý test suite beží jedným príkazom za < 3 min na vývojárskom stroji.
- Ralph v ďalších specs nepotrebuje nič ručne nastavovať.

## Dependencies
- Existujúci `server/` a `web_app/`.

## Assumptions
- Lokálne je Python 3.11+ (aktuálne 3.14). Ak by `playwright install chromium` zlyhal pre chýbajúce
  systémové knižnice, zapíš to do `## Implementation notes` a do `docs/food/README.md`
  (`sudo e2e/.venv/bin/playwright install-deps chromium`). Vtedy spec NIE JE hotová.

---

## Completion Signal

### Implementation Checklist
- [ ] `scripts/test-food.sh`
- [ ] `e2e/` (requirements, conftest, test_smoke.py)
- [ ] Django app `food` + prepínač appiek + responzívna navigácia
- [ ] htmx + CSRF
- [ ] `docs/food/README.md`

### Testing Requirements
- [ ] `./scripts/test-food.sh` → exit 0 (server + web + e2e)
- [ ] Žiadne JS chyby v konzole na `/food/` a `/`

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 0 -->
