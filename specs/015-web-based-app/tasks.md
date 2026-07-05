# Tasks: Web Companion App

**Input**: Design documents from `specs/015-web-based-app/`

**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Nie sú explicitne požadované v spec — nie sú zahrnuté. Validácia cez quickstart.md scenáre.

**Tech Stack**: Python 3.11+, Django 5.x, httpx, Chart.js 4.x (CDN), Bootstrap 5 (CDN)

**Two-server architecture**: FastAPI :8095 (existujúci) + Django :8000 (nový)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelizovateľné (rôzne súbory, žiadne závislosťi)
- **[Story]**: User story podľa spec.md

---

## Phase 1: FastAPI rozšírenie (Blocker pre všetky US)

**Purpose**: Nové endpointy na čítanie uložených dát. Existujúci server nemá "pull" API — bez tejto fázy dashboard nemá dáta.

**⚠️ CRITICAL**: Táto fáza musí byť dokončená pred akoukoľvek Django implementáciou.

- [X] T001 Create `server/app/routers/user.py` — nový FastAPI router s `GET /api/v1/user/history?days=30` (načíta TrackingDay + DailyIndex + ElementValue pre `current_user`, zoradí zostupne podľa date, vráti `{schema_version, days: [{date, index_value, detail: [{element_key, value_effective, weight, contribution, impact}]}], total_days}`)
- [X] T002 Add `GET /api/v1/user/me` do `server/app/routers/user.py` — vráti `{email, created_at, total_days}` pre `current_user`
- [X] T003 Register user router in `server/app/main.py` — `app.include_router(user.router)` s prefix `/api/v1/user` a tag `"user"`

**Checkpoint**: `curl -H "Authorization: Bearer <token>" http://127.0.0.1:8095/api/v1/user/history` vráti JSON s poľom `days`.

---

## Phase 2: Django Setup (Shared Infrastructure)

**Purpose**: Inicializácia Django projektu. Závislosť pre všetky user stories.

- [X] T004 Initialize Django project — `django-admin startproject adhd_web web_app` v root adresári projektu; overiť že `web_app/manage.py` existuje
- [X] T005 Create `web_app/requirements.txt` — obsah: `Django>=5.0`, `httpx>=0.27`
- [X] T006 Create Django app — `python manage.py startapp core` v `web_app/`; overiť štruktúru `web_app/core/`
- [X] T007 Configure `web_app/adhd_web/settings.py` — pridať: `INSTALLED_APPS += ["core"]`, `SERVER_URL = "http://127.0.0.1:8095"`, `SESSION_COOKIE_AGE = 86400`, `TEMPLATES[0]["DIRS"] = [BASE_DIR / "core/templates"]`, `STATICFILES_DIRS = [BASE_DIR / "static"]`
- [X] T008 Create `web_app/core/api_client.py` — httpx wrapper s funkciami: `post_login(email, password) -> dict`, `post_register(email, password) -> dict`, `get_history(token, days=30) -> dict`, `get_me(token) -> dict`; každá funkcia číta `SERVER_URL` z Django settings; pri `httpx.ConnectError` vráti `{"error": "server_unavailable"}`
- [X] T009 Create `web_app/core/templates/base.html` — Bootstrap 5 CDN navbar s odkazmi: Dashboard, Trend, Účet, Info; aktívny link podľa current URL; podmienený logout button ak session obsahuje `jwt`
- [X] T010 Configure `web_app/adhd_web/urls.py` — include `core.urls`; `web_app/core/urls.py` s placeholder URL patterns (vyplní sa v jednotlivých US)
- [X] T011 Run `python manage.py migrate` — Django session + admin tabulky; overiť že `db.sqlite3` vznikol v `web_app/`

**Checkpoint**: `python manage.py runserver 8000` štartuje bez chýb, `http://127.0.0.1:8000/` vráti HTTP odpoveď.

---

## Phase 3: User Story 1 — Autentifikácia (Priority: P1) 🎯 MVP

**Goal**: Registrácia, prihlásenie, odhlásenie. Neautentifikovaní používatelia vidí len login/register.

**Independent Test**: Zaregistruj nový účet → prihlás sa → vidíš `/dashboard/` (aj keď prázdny). Odhlás sa → redirect na `/login/`. Neexistujúci účet → chybová správa vo formulári.

- [X] T012 [US1] Create `web_app/core/decorators.py` — `@login_required_jwt` decorator: ak `request.session.get("jwt")` chýba → redirect na `/login/?next=<current_url>` (implementované priamo v views.py cez `_require_login` helper)
- [X] T013 [US1] Create `web_app/core/views.py` — `LoginView(View)`: GET renderuje `login.html`; POST zavolá `api_client.post_login(email, password)` → pri úspechu uloží `request.session["jwt"]` a `request.session["email"]` → redirect `/dashboard/`; pri chybe renderuje `login.html` s `error` kontextom
- [X] T014 [US1] Add `RegisterView(View)` do `web_app/core/views.py` — rovnaký vzor ako LoginView ale volá `api_client.post_register`; po úspešnej registrácii auto-login a redirect `/dashboard/`
- [X] T015 [US1] Add `LogoutView(View)` do `web_app/core/views.py` — POST: `request.session.flush()` → redirect `/login/`
- [X] T016 [US1] Create `web_app/core/templates/login.html` — extends `base.html`; Bootstrap card s email + password poľami; zobrazí `{{ error }}` ak existuje; odkaz na `/register/`
- [X] T017 [US1] Create `web_app/core/templates/register.html` — extends `base.html`; Bootstrap card s email + password poľami; zobrazí `{{ error }}`; odkaz na `/login/`
- [X] T018 [US1] Register URL patterns in `web_app/core/urls.py` — `/login/`, `/register/`, `/logout/` → príslušné views

**Checkpoint**: Registrácia nového účtu → prihlásenie → redirect na `/dashboard/` (HTTP 200 alebo 302). Neexistujúci účet pri login → formulár s chybou.

---

## Phase 4: User Story 2 — Dashboard (Priority: P2)

**Goal**: Hlavná stránka s double-sided bar chartom — pozitívne príspevky hore (zelené), negatívne dole (červené).

**Independent Test**: Prihlásený, server má dáta → dashboard zobrazí bar chart. Server offline → správa "Server nie je dostupný". Žiadne dáta → prázdny stav s vysvetlením.

- [X] T019 [US2] Add `DashboardView(View)` do `web_app/core/views.py` — `@login_required_jwt`; zavolá `api_client.get_history(token, days=30)`; transformuje dáta pre Chart.js: `labels=[dates]`, `positive_data=[sum contribution where impact>0 per day]`, `negative_data=[sum contribution where impact<0 per day]`; vloží ako JSON do template context; pri `error=server_unavailable` vloží `server_error=True`
- [X] T020 [US2] Create `web_app/core/templates/dashboard.html` — extends `base.html`; ak `server_error` → Bootstrap alert "Server nie je dostupný"; ak `empty` → info text "Zatiaľ žiadne záznamy — zadaj dáta cez mobilnú aplikáciu"; inak `<canvas id="mainChart">`; `<script>` blok s Chart.js stacked bar konfiguráciou (datasets: positive=zelená, negative=červená)
- [X] T021 [US2] Register `/dashboard/` URL in `web_app/core/urls.py`; root `/` redirect na `/dashboard/`

**Checkpoint**: Dashboard zobrazí double-sided bar chart pri dostupných dátach. Žiadny input element pre zadávanie záznamov nie je viditeľný.

---

## Phase 5: User Story 3 — Denný trend (Priority: P3)

**Goal**: Line chart ADHD indexu za posledných 30 dní.

**Independent Test**: Naviguj na `/trend/` → zobrazí sa line chart s hodnotami 0–100 na Y osi, dátumy na X osi.

- [X] T022 [US3] Add `TrendView(View)` do `web_app/core/views.py` — `@login_required_jwt`; zavolá `api_client.get_history(token, days=30)`; extrahuje `labels=[dates]`, `data=[index_value]` (None hodnoty ako null pre Chart.js); pri error → `server_error=True`
- [X] T023 [US3] Create `web_app/core/templates/trend.html` — extends `base.html`; `<canvas id="trendChart">`; Chart.js line chart konfigurácia: Y os 0–100, X os dátumy, `spanGaps=true` pre null hodnoty; pri error/empty — rovnaký vzor ako dashboard
- [X] T024 [US3] Register `/trend/` URL in `web_app/core/urls.py`

---

## Phase 6: User Story 4 — Používateľský účet (Priority: P4)

**Goal**: Stránka s emailom, počtom dní a tlačidlom odhlásenia.

**Independent Test**: Naviguj na `/account/` → vidíš email a základné info. Klikni odhlásenie → redirect `/login/`.

- [X] T025 [US4] Add `AccountView(View)` do `web_app/core/views.py` — `@login_required_jwt`; zavolá `api_client.get_me(token)`; vloží `email`, `created_at`, `total_days` do context
- [X] T026 [US4] Create `web_app/core/templates/account.html` — extends `base.html`; Bootstrap card s emailom a štatistikami; form `POST /logout/` s Bootstrap button
- [X] T027 [US4] Register `/account/` URL in `web_app/core/urls.py`

---

## Phase 7: User Story 5 — Info stránka (Priority: P5)

**Goal**: Statická stránka s popisom projektu.

**Independent Test**: Naviguj na `/info/` (aj bez prihlásenia) → zobrazí sa popis projektu.

- [X] T028 [P] [US5] Add `InfoView(TemplateView)` do `web_app/core/views.py` — `template_name="info.html"`; verejne dostupná (bez `@login_required_jwt`)
- [X] T029 [P] [US5] Create `web_app/core/templates/info.html` — extends `base.html`; popis projektu ADHD Tracker, verzia, účel
- [X] T030 [P] [US5] Register `/info/` URL in `web_app/core/urls.py`

---

## Phase 8: Polish & Cross-Cutting

- [X] T031 Create `web_app/static/js/charts.js` — zdieľané Chart.js helper funkcie (defaults, color constants); importovaný v `base.html`
- [X] T032 Add CSRF protection — `{% csrf_token %}` vo všetkých POST formulároch (login, register, logout); overiť že Django `CsrfViewMiddleware` je aktívny v settings
- [X] T033 Add session expiry handling in `web_app/core/views.py` — ak FastAPI vráti 401 → `request.session.flush()` + redirect `/login/?expired=1`; `login.html` zobrazí "Prihlásenie vypršalo" ak `?expired=1`
- [ ] T034 Manual validation — spusti všetkých 8 quickstart scenárov z `specs/015-web-based-app/quickstart.md` a zaznač výsledky

---

## Dependencies & Execution Order

```
T001→T002→T003 (FastAPI) → T004–T011 (Django setup) → T012–T018 (US1 auth)
                                                      → T019–T021 (US2 dashboard)
                                                      → T022–T024 (US3 trend)
                                                      → T025–T027 (US4 account)
T028–T030 (US5 info) — independent of US1-4
T031–T034 (Polish) — after all US complete
```

### Parallel Opportunities

```
# FastAPI fáza (musí byť prvá):
T001, T002 — rôzne funkcie v rovnakom súbore → sekvenčne

# Django setup (T004-T011) — väčšina sekvenčná (závislosť settings→app→urls)

# Po dokončení auth (US1):
US3 (T022-T024) a US4 (T025-T027) sú paralelné — rôzne views/templates
US5 (T028-T030) — plne paralelné s US2-4
```

---

## Implementation Strategy

### MVP First

1. **T001-T003** — FastAPI endpointy (bez toho dashboard nefunguje)
2. **T004-T011** — Django projekt setup
3. **T012-T018** — US1 autentifikácia (prihlásenie + register)
4. **STOP & VALIDATE**: Registrácia a login fungujú → redirect na dashboard
5. **T019-T021** — US2 dashboard s grafom
6. **STOP & VALIDATE**: Graf zobrazuje dáta

### Incremental Delivery

- Po T018: Autentifikácia hotová → mergovateľný checkpoint
- Po T021: Dashboard funguje → demo-ready MVP
- T022-T030: Dopĺňanie ostatných stránok
- T031-T034: Polish

---

## Notes

- FastAPI server musí bežať na 8095 počas vývoja Django views
- `httpx.ConnectError` musí byť zachytený v každej view — nie 500 error
- Chart.js dáta sa vkladajú ako `json.dumps(data)` cez Django template `{{ data|safe }}`
- CSRF: všetky POST formy musia mať `{% csrf_token %}`
- `overall_feeling` vždy scaleMin=1, scaleMax=5 (Constitution Princíp IV) — web app len zobrazuje, nepočíta
