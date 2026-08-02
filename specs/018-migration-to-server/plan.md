# Implementation Plan: HTTPS / TLS Setup pre produkčné nasadenie

**Branch**: `018-migration-to-server` | **Date**: 2026-08-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-migration-to-server/spec.md`

---

## Summary

018 pripravuje produkčné nasadenie na Debian serveri: Nginx ako reverse proxy s TLS terminovaným cez Let's Encrypt (certbot) pre `api.adhdknight.com` (FastAPI) a `console.adhdknight.com` (Django), HTTP→HTTPS redirect na oboch doménach, HTTP Basic Auth len na konzole (na úrovni Nginx, pred Django appkou), a PostgreSQL viazaný len na `localhost`. Klienti (mobilná app, web app) sa nemenia — TLS je čisto na transportnej vrstve. Dátovú SQLite→PostgreSQL migráciu **nerieši** táto feature — len spúšťa nástroj z `017-migration-to-postgres` ako krok v deploymente; ak ten nástroj neexistuje, je to externý blocker pre 018, nie práca navyše.

---

## Technical Context

**Language/Version**: Bash (inštalačné skripty), Nginx config DSL, systemd unit files; existujúci Python 3.12 (FastAPI server) a Django 6.0 (web konzola) sa menia len v konfiguračných bodoch (env-driven settings), nie v doménovej logike.

**Primary Dependencies**: Nginx (reverse proxy + TLS + Basic Auth), `certbot` + `python3-certbot-nginx` (Let's Encrypt), PostgreSQL 16 (Debian balík), `apache2-utils` (`htpasswd`), systemd (process supervision), Gunicorn (nový — WSGI server pre Django, chýba v `web_app/requirements.txt`)

**Storage**: PostgreSQL, viazaný na `127.0.0.1`/unix socket — dve databázy (`adhd_server` pre FastAPI, `adhd_web` pre Django). SQLite zostáva pre lokálny dev (nezmenené).

**Testing**: Bez tradičných unit testov (infra konfigurácia, nie aplikačný kód). Validácia cez `quickstart.md` — `curl`/`psql`/`certbot --dry-run` scenáre spustené na reálnom/staging serveri, 1:1 mapované na acceptance scenáre v spec.md. Existujúce Django/FastAPI test suites MUSIA prejsť bez zmeny (settings zmeny sú backward-compatible cez env fallback).

**Target Platform**: Debian (produkčný VPS s verejnou IP a DNS pre obe domény)

**Project Type**: Infraštruktúra / deployment — nová `deploy/` zložka s config templatemi a inštalačným skriptom, plus cielené env-driven úpravy `web_app/adhd_web/settings.py`

**Performance Goals**: Nešpecifikované nad rámec normálneho HTTP request handlingu jedného produkčného servera (spec neuvádza konkrétne req/s ciele)

**Constraints**:
- Žiadne zmeny na strane klientov (mobilná app, web app) — FR-002, FR-004
- `console.adhdknight.com` basic auth MUST byť pred Django, `api.adhdknight.com` basic auth MUST NOT mať — FR-005
- PostgreSQL MUST byť nedostupný mimo localhost — FR-006
- Lokálny `make dev` MUST fungovať bez TLS/Nginx závislosti — SC-003
- Reálne produkčné basic auth heslo sa nikdy nezapisuje do gitu — len placeholder `admin`/`admin` v dokumentácii, skutočné heslo nastavuje človek manuálne

**Scale/Scope**: 1 produkčný server, 2 domény, 2 aplikačné procesy (Uvicorn + Gunicorn), 2 Postgres databázy, ~5 nových konfiguračných artefaktov (`deploy/nginx/*`, `deploy/systemd/*`, `deploy/scripts/install.sh`) + cielené úpravy `web_app/adhd_web/settings.py` a `web_app/requirements.txt`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution (`/.specify/memory/constitution.md`) je explicitne scoped na Android aplikáciu (MVVM, Room, Compose, index algoritmus). 018 sa nedotýka `android_app/` ani doménovej logiky indexu — je to serverová/deployment infraštruktúra.

| Princíp | Status | Poznámka |
|---|---|---|
| I. Architektúra a kódová disciplína (MVVM/Repository) | ✅ N/A | Netýka sa `android_app/`; žiadna zmena v Compose/ViewModel/Repository vrstvách |
| II. Doménová logika indexu | ✅ N/A | Výpočet indexu sa nemení — TLS je transportná vrstva |
| III. Dátový model (Room) | ✅ N/A | Žiadne Room entity sa nemenia; PostgreSQL zmeny sú na serverovej strane (017/018), nie Room |
| IV. UX | ✅ PASS | FR-004 explicitne zachováva bezproblémový dev flow (žiadne nové trenie pre používateľa appky) |
| V. Notifikácie | ✅ N/A | Nedotknuté |
| VI. Testovanie | ✅ PASS (upravené kritérium) | Infra feature nemá JVM/Room testy — validácia cez `quickstart.md` behaviorálne scenáre namiesto unit testov; existujúce Django/FastAPI testy MUSIA prejsť bez zmeny |
| VII. Tech stack — nové závislosti | ✅ JUSTIFIED | Nginx/certbot/PostgreSQL/Gunicorn — štandardné produkčné nástroje, žiadna alternatíva k Nginx (spec to explicitne vyžaduje), Gunicorn je štandardná WSGI voľba pre Django v produkcii (`runserver` nie je produkčne bezpečný) |

**Výsledok Constitution Check: PASS — žiadne bloky, žiadny Complexity Tracking záznam potrebný.**

**Cross-feature blocker (nie constitution violation)**: `017-migration-to-postgres` zatiaľ nemá `plan.md`/`tasks.md` ani implementovaný SQLite→PostgreSQL dátový migračný skript. 018 tento nástroj len **volá** (spec.md, sekcia "Vzťah k 017"), nereimplementuje ho. Task pre "spusti migráciu" v `tasks.md` musí byť explicitne označený ako blokovaný, kým 017 nedodá nástroj — pozri `research.md` Decision 8.

## Project Structure

### Documentation (this feature)

```text
specs/018-migration-to-server/
├── plan.md                        ← tento súbor
├── research.md                    ← 9 rozhodnutí: Nginx, certbot, basic auth, systemd, Postgres binding, Django settings, 017 blocker, verifikácia
├── data-model.md                  ← konfiguračné entity: NginxSite, TLSCertificate, BasicAuthCredential, SystemdUnit, PostgresDatabase, EnvironmentConfig
├── contracts/
│   └── http-behavior.md           ← sieťový kontrakt (redirect, 401, TLS) per doména
├── quickstart.md                  ← 7 validačných scenárov na produkčnom/staging serveri
└── tasks.md                       ← generuje /speckit-tasks
```

### Source Code (repository root)

```text
deploy/                                          # NOVÉ — deployment artefakty
├── nginx/
│   ├── api.adhdknight.com.conf                  # NOVÝ — proxy_pass 127.0.0.1:8095, redirect, žiadny auth_basic
│   └── console.adhdknight.com.conf              # NOVÝ — proxy_pass 127.0.0.1:8000, redirect, auth_basic
├── systemd/
│   ├── adhd-api.service                         # NOVÝ — uvicorn unit
│   └── adhd-web.service                         # NOVÝ — gunicorn unit
└── scripts/
    └── install.sh                               # NOVÝ — orchestrácia: postgres setup, venv/deps, migrate (FastAPI alembic), volanie 017 dátovej migrácie, collectstatic, nginx+certbot, systemd enable

server/
├── .env.example                                 # MODIFY — pridaj produkčné poznámky (DATABASE_URL už existuje z 017)
└── README.md                                    # MODIFY — pridaj sekciu "Produkčné nasadenie" s odkazom na deploy/

web_app/
├── adhd_web/settings.py                         # MODIFY — env-driven DEBUG/ALLOWED_HOSTS/SECRET_KEY/DATABASES/STATIC_ROOT/CSRF_TRUSTED_ORIGINS/SECURE_PROXY_SSL_HEADER
├── .env.example                                  # NOVÝ — DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DJANGO_SECRET_KEY, DJANGO_DATABASE_URL
└── requirements.txt                              # MODIFY — pridaj gunicorn, psycopg[binary] (Postgres driver pre Django)
```

**Structure Decision**: Nová `deploy/` zložka na úrovni repo root (sourced z `server/` aj `web_app/`, ale sama je samostatná — nepatrí pod ani jeden z nich, keďže orchestruje oba). Zmeny v `web_app/` sú minimálne a výhradne env-driven, aby lokálny dev beh (`python manage.py runserver`) zostal nezmenený bez nastavených env premenných. `server/` sa mení len dokumentačne — samotný `DATABASE_URL` env-switch mechanizmus už existuje (017 pripravil `config.py`/`database.py`).

## Complexity Tracking

*Žiadne porušenia Constitution Check — táto sekcia sa nevyžaduje.*
