# Research: Web Companion App

## Decision 1: Webový backend — Django vs rozšírenie FastAPI

**Decision**: Django ako samostatný web backend (`web_app/` adresár)

**Rationale**:
- Používateľ má skúsenosti s Djangom → rýchlejší vývoj, prirodzenejší kód
- Django šablóny (DTL) sú vhodné pre server-side rendering HTML dashboardov
- Čistá separácia zodpovedností: FastAPI = dátový/výpočtový server, Django = webový frontend server
- Django spravuje webové sessions bez nutnosti localStorage/cookie JWT logiky v prehliadači
- Alfa platforma — v budúcnosti môže Django dostať vlastnú logiku (nové grafy, transformácie)

**Alternatives considered**:
- Rozšírenie FastAPI o Jinja2 templates: menej kódu, ale mieša web-routing s API routingom; komplikuje budúce oddelenie
- Pure SPA (HTML+JS bez backendu): JWT v localStorage, CORS issues, žiadny server-side rendering — nevhodné pre alfa testovanie

---

## Decision 2: Auth flow Django ↔ FastAPI

**Decision**: Django view zavolá FastAPI `/api/v1/auth/login` → JWT uloží do Django session → JS na stránkach ho nevidí

**Rationale**:
- JWT v Django session (server-side) je bezpečnejšie ako localStorage
- Prehliadačový JS nepotrebuje JWT — všetky API volania robí Django server-side
- Django `requests` knižnica volá FastAPI synchrónne (httpx pre async ak treba)

**Alternatives considered**:
- JWT v cookie: komplikuje CSRF ochranu
- JWT v localStorage + priame AJAX volania FastAPI z browsera: CORS konfigurácia, XSS risk

---

## Decision 3: Charting knižnica

**Decision**: Chart.js (CDN, vanilla JS)

**Rationale**:
- Žiadny build pipeline (npm/webpack) — jednoduchosť pre alfa platformu
- Natívna podpora double-sided bar chart (positive/negative stacked bars)
- Voľne dostupná, stabilná, rozšíriteľná
- Dáta zo Django view → JSON kontext → Chart.js konfigurácia v `<script>` tagu

**Alternatives considered**:
- D3.js: príliš nízkoúrovňová pre jednoduché grafy
- Plotly.js: väčší bundle, viac závislostí
- Recharts/ApexCharts: vyžadujú React/build systém

---

## Decision 4: Nový FastAPI endpoint — história používateľa

**Decision**: Pridať `GET /api/v1/user/history` do existujúceho FastAPI servera

**Rationale**:
- Existujúce endpointy (`/compute/range`, `/sync/batch`) sú "push" operácie — vyžadujú poslanie dát, nevracajú uložené záznamy
- Web app potrebuje "pull" — načítať uložené `TrackingDay` + `DailyIndex` pre prihláseného používateľa
- Endpoint vracia polia `{date, index_value, detail_json}` pre posledných N dní
- Autentifikácia cez existujúci `get_current_user` dependency (JWT Bearer)

**Alternatives considered**:
- Repurpose `/sync/status`: vracia len počet dní, nie hodnoty — nedostatočné
- Django priamo prístup k SQLite DB: porušuje separáciu, krehké

---

## Decision 5: CSS framework

**Decision**: Bootstrap 5 (CDN)

**Rationale**:
- Žiadny build pipeline
- Responzívny grid, navbar, cards — presne to čo alfa dashboard potrebuje
- Konzistentný vzhľad bez vlastného CSS
- Django + Bootstrap je zavedená kombinácia

---

## Zhrnutie stacku

| Vrstva | Technológia |
|--------|-------------|
| Webový server | Django 5.x + Python 3.11+ |
| Šablóny | Django Template Language (DTL) |
| HTTP klient | `httpx` (async, Django volá FastAPI) |
| Grafy | Chart.js 4.x (CDN) |
| CSS | Bootstrap 5 (CDN) |
| Dátový server | FastAPI (existujúci, port 8095) |
| Auth | FastAPI JWT → Django session |
| Nový endpoint | `GET /api/v1/user/history` v FastAPI |
