# Food diary — vývojárska príručka

## Architektúra

- **FastAPI (`server/`)** obsahuje všetku doménovú logiku Food diary (validácia, parsovanie,
  autocomplete, export). API prefix `/api/v1/food`, súbory `routers/food*.py`, `services/food_*.py`,
  `models/food.py`, `schemas/food.py`.
- **Django (`web_app/`)** je tenký klient: app `food` (URL `/food/`) iba zobrazuje dáta a volá API
  cez `web_app/food/api_client.py`. Interaktivita cez HTMX (`web_app/static/js/htmx.min.js`,
  bez CDN); CSRF token posiela `hx-headers` na `<body>` v `core/templates/base.html`.
- Spoločný login a layout; prepínač `ADHD | Food` v navigácii. Food stránky dedia
  `food/base_food.html` a vlastné odkazy dávajú do bloku `{% block app_nav %}`.
- Nové UI texty vo `food` cez `{% translate %}` / `gettext` s anglickým msgid.

## Predpoklady

- Python 3.11+ (`python3 -m venv` musí fungovať).
- Pre e2e: systémové knižnice Chromium. Ak `playwright install chromium` alebo spustenie prehliadača
  zlyhá kvôli chýbajúcim knižniciam:
  ```bash
  sudo e2e/.venv/bin/playwright install-deps chromium
  ```
  (Ralph Docker image ich už obsahuje.)

## Lokálne spustenie

```bash
# API (terminál 1)
cd server
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8095 --reload

# Web konzola (terminál 2)
cd web_app
.venv/bin/python manage.py migrate
FASTAPI_URL=http://127.0.0.1:8095 .venv/bin/python manage.py runserver
```

Konzola potom beží na <http://127.0.0.1:8000/>, Food diary na <http://127.0.0.1:8000/food/>.
Venvy vytvorí `./scripts/test-food.sh` (pozri nižšie).

## Testy

```bash
./scripts/test-food.sh            # server + web + e2e
./scripts/test-food.sh --no-e2e   # bez Playwright
VENV_NAME=.venv-docker ./scripts/test-food.sh   # iný názov venv (Ralph kontajner)
```

Skript:
1. vytvorí `server/<venv>`, `web_app/<venv>`, `e2e/<venv>` (default `.venv`), ak chýbajú alebo sú
   nefunkčné, a reinštaluje závislosti iba pri zmene `requirements.txt` (hash vo venv),
2. stiahne Playwright Chromium, ak chýba,
3. spustí `server` pytest (`tests/unit tests/api`), Django testy (`manage.py test`) a e2e,
4. vypíše súhrn `server: OK|FAIL, web: OK|FAIL, e2e: OK|FAIL|SKIPPED`; exit ≠ 0 pri akomkoľvek FAIL.

## E2E (`e2e/`)

Samostatne: `e2e/.venv/bin/pytest e2e -q` (z koreňa repa; `VENV_NAME` určuje, ktoré venvy harness použije).

Fixtures v `e2e/conftest.py`:
- `api_server` — dočasná SQLite DB, `alembic upgrade head`, `uvicorn` na voľnom porte, čaká na `/api/v1/health`.
- `web_server` — `manage.py migrate` + `runserver --noreload` proti `api_server`, sessions v dočasnej
  SQLite (`DJANGO_SQLITE_PATH`). Tiež prepisuje `base_url`, takže `page.goto("/food/")` funguje.
- `user_factory` — vytvorí používateľa cez API, vráti `(email, password)`.
- `logged_in_page` — Playwright `page` prihlásený cez login formulár; `login(page, email, password)` helper.
- `mobile_page` — viewport 360 × 740, `is_mobile=True` (neprihlásený).
- `console_errors` — zoznam JS chýb / `console.error` na `page`.

Procesy sa po session vždy ukončia. Pri zlyhaní testov sa logy API a webu vypíšu v súhrne pytest.
**Selektory iba cez `data-testid`** (UI je viacjazyčné).
