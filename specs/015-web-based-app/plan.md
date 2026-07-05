# Implementation Plan: Web Companion App

**Branch**: `015-web-based-app` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

## Summary

Django web aplikácia slúžiaca ako read-only dashboard pre ADHD tracker dáta uložené na FastAPI serveri. Django spravuje web sessions a renderuje HTML stránky; Chart.js renderuje grafy v prehliadači. Existujúci FastAPI server bude rozšírený o 2 nové endpointy pre načítanie histórie a profilu používateľa.

## Technical Context

**Language/Version**: Python 3.11+, Django 5.x

**Primary Dependencies**:
- Django 5.x — web framework, šablóny, session management
- httpx — async HTTP klient pre volania FastAPI zo Django views
- Chart.js 4.x (CDN) — vizualizácie v prehliadači
- Bootstrap 5 (CDN) — CSS framework

**Storage**: Žiadna vlastná DB pre dáta; Django používa SQLite len pre session tabulky (`django.contrib.sessions`)

**Testing**: Django test client pre view testy, `pytest-django` pre unit testy

**Target Platform**: Desktop prehliadač (Chrome, Firefox, Safari), lokálny server

**Project Type**: Web aplikácia (server-side rendering)

**Performance Goals**: Dashboard sa načíta do 3 sekúnd pri lokálnom FastAPI serveri

**Constraints**: Read-only — žiadne write operácie na FastAPI; Django beží na porte 8000, FastAPI na 8095

**Scale/Scope**: Alfa platforma pre jedného používateľa, lokálne nasadenie

## Constitution Check

Táto feature je webová aplikácia — Android constitution (Princípy I, III, V-VII) sa **nevzťahujú**. Relevantné princípy:

- **Princíp II (Doménová logika)**: Web app zobrazuje už vypočítané indexy zo servera — nepočíta vlastný index. ✓ Žiadny konflikt.
- **Princíp IV (UX)**: Webový dashboard nezasahuje do Android UX. Tracker je explicitne vylúčený. ✓

## Project Structure

### Documentation (this feature)

```text
specs/015-web-based-app/
├── plan.md              # Tento súbor
├── research.md          # Tech stack rozhodnutia
├── data-model.md        # API dátové štruktúry
├── quickstart.md        # Validačné scenáre
├── contracts/
│   ├── django-pages.md           # URL routes a page contracts
│   └── fastapi-new-endpoints.md  # Nové FastAPI endpointy
└── tasks.md             # Generuje /speckit-tasks
```

### Source Code

```text
web_app/                          # Nový Django projekt
├── manage.py
├── requirements.txt              # Django, httpx
├── adhd_web/                     # Django projekt settings
│   ├── __init__.py
│   ├── settings.py               # SERVER_URL, SESSION_COOKIE_AGE
│   ├── urls.py                   # Root URL conf
│   └── wsgi.py
├── core/                         # Hlavná Django app
│   ├── __init__.py
│   ├── views.py                  # LoginView, RegisterView, DashboardView, TrendView, AccountView, InfoView
│   ├── urls.py
│   ├── middleware.py             # JWT session middleware / decorator
│   ├── api_client.py             # httpx wrapper pre FastAPI volania
│   └── templates/
│       ├── base.html             # Bootstrap navbar, CDN skripty
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html        # Double-sided bar chart
│       ├── trend.html            # Line chart
│       ├── account.html
│       └── info.html
└── static/
    └── js/
        └── charts.js             # Chart.js konfigurácia

server/app/routers/user.py        # Nový FastAPI router — GET /api/v1/user/history + /me
server/app/main.py                # Zaregistruj nový router
```

## Architecture

```
Prehliadač (HTML/JS/Chart.js)
        ↕  HTTP GET (stránky)
Django :8000
        ↕  HTTP (httpx, Bearer JWT)
FastAPI :8095  ←  existujúci server
        ↕
SQLite DB
```

**Auth flow**:
1. Používateľ odošle login form (POST `/login/`)
2. Django zavolá `POST /api/v1/auth/login` cez httpx
3. FastAPI vráti `access_token`
4. Django uloží token do `request.session["jwt"]`
5. Každá chránená Django view načíta token zo session a použije ho ako `Authorization: Bearer <token>` pri FastAPI volaniach

**Chart data flow**:
1. Django view zavolá `GET /api/v1/user/history?days=30`
2. Spracuje JSON → vytvorí Chart.js-kompatibilný formát
3. Vloží dáta do Django template context ako JSON string
4. Template renderuje `<script>` s Chart.js konfiguráciou

## Implementation Phases

### Phase 1: FastAPI rozšírenie
- Nový router `server/app/routers/user.py`
- `GET /api/v1/user/history` — načíta TrackingDay + DailyIndex + ElementValue
- `GET /api/v1/user/me` — email + created_at + total_days
- Zaregistrovanie routeru v `main.py`

### Phase 2: Django projekt setup
- Inicializácia projektu, konfigurácia `settings.py`, `requirements.txt`

### Phase 3: Auth views (US1)
- `api_client.py` — httpx wrapper pre FastAPI volania
- Login, Register, Logout views + templates
- `@login_required_jwt` decorator pre chránené views

### Phase 4: Dashboard (US2)
- `DashboardView` — načíta history, transformuje pre Chart.js
- `dashboard.html` s double-sided stacked bar chartom
- Prázdny stav + error handling

### Phase 5: Trend + Account + Info (US3–US5)
- `TrendView` — line chart
- `AccountView` — zavolá `/api/v1/user/me`
- `InfoView` — statická stránka

### Phase 6: Polish
- `base.html` s Bootstrap navigáciou
- Error stránky (server offline, session expirovaná)
