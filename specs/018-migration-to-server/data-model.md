# Data Model: HTTPS / TLS Setup pre produkčné nasadenie

**Feature**: 018 — HTTPS/TLS + Basic Auth + PostgreSQL hardening
**Date**: 2026-08-01

**Poznámka**: Táto feature nepridáva žiadne aplikačné dátové entity (DB tabuľky). "Dátový model" tu popisuje konfiguračné entity — súbory a nastavenia, ktoré inštalačný postup vytvára/spravuje na produkčnom serveri.

---

## NginxSite

Konfiguračný súbor per doména v `/etc/nginx/sites-available/`, symlinkovaný do `sites-enabled/`.

| Pole | Popis |
|---|---|
| `server_name` | `api.adhdknight.com` alebo `console.adhdknight.com` |
| `listen_80` | redirect-only blok → 301 na HTTPS (FR-003) |
| `listen_443` | TLS blok, `ssl_certificate`/`ssl_certificate_key` z certbot |
| `proxy_pass` | `http://127.0.0.1:8095` (api) alebo `http://127.0.0.1:8000` (console) |
| `auth_basic` | prítomné len pri `console.adhdknight.com` (FR-005) |
| `static_location` | len pri console — `location /static/` servované priamo Nginxom (Django `STATIC_ROOT`) |

**Validačné pravidlo**: `api.adhdknight.com` config NESMIE obsahovať `auth_basic` direktívu (FR-005, SC-004).

---

## TLSCertificate

Spravované cez `certbot`, uložené v `/etc/letsencrypt/live/<domena>/`.

| Pole | Popis |
|---|---|
| `domain` | jedna z dvoch produkčných domén |
| `issuer` | Let's Encrypt |
| `renewal` | automaticky cez `certbot.timer` (systemd), 30 dní pred expiráciou (FR-002) |
| `challenge_type` | HTTP-01 (nginx plugin) primárne; DNS-01 ako fallback ak server nemá verejnú IP (Edge Case) |

**State transitions**: `requested → issued → (renewing 30 dní pred expiráciou) → renewed`. Zlyhanie obnovy → monitoring alert (Edge Case v spec, mimo scope automatizácie tejto feature — zdokumentované ako odporúčanie v quickstart).

---

## BasicAuthCredential

`.htpasswd` súbor, `/etc/nginx/.htpasswd_console` (mimo repozitára, negenerovaný z verzovaného configu).

| Pole | Popis |
|---|---|
| `username` | `admin` (placeholder pri inštalácii) |
| `password_hash` | bcrypt/crypt hash generovaný `htpasswd` nástrojom |
| `scope` | len `console.adhdknight.com` |

**Validačné pravidlo**: reálne produkčné heslo sa MUSÍ nastaviť manuálne po inštalácii (FR-005) — placeholder `admin`/`admin` sa nesmie nikdy commitnúť do gitu ako skutočné heslo.

---

## SystemdUnit

Dve nové unit súbory v `/etc/systemd/system/`.

| Pole | `adhd-api.service` | `adhd-web.service` |
|---|---|---|
| `ExecStart` | `uvicorn app.main:app --host 127.0.0.1 --port 8095` | `gunicorn adhd_web.wsgi:application --bind 127.0.0.1:8000` |
| `WorkingDirectory` | `server/` | `web_app/` |
| `EnvironmentFile` | `server/.env` | `web_app/.env` (nový) |
| `Restart` | `on-failure` | `on-failure` |

---

## PostgresDatabase

| Pole | `adhd_server` | `adhd_web` |
|---|---|---|
| `owner_role` | dedikovaný DB user pre FastAPI | dedikovaný DB user pre Django |
| `binding` | `listen_addresses=localhost` (Debian default, neupravuje sa) | rovnaké |
| `auth_method` | `scram-sha-256`, obmedzené na `127.0.0.1/32` + `local` socket (`pg_hba.conf`) | rovnaké |
| `owning_feature` | dátová migrácia zo SQLite: **017** (blocker ak nedodané, viď research.md Decision 8) | nová konfigurácia v rámci **018** (Django dosiaľ nemal produkčnú DB) |

**Validačné pravidlo** (SC-005): pokus o pripojenie z inej adresy než `localhost` MUSÍ zlyhať (connection refused/timeout).

---

## EnvironmentConfig

Rozšírenie existujúcich `.env` vzorov (`server/.env.example` už existuje; `web_app/.env.example` je nový).

| Premenná | Súbor | Popis |
|---|---|---|
| `DATABASE_URL` | `server/.env` | už existuje (017); `postgresql+asyncpg://...` v produkcii |
| `ENVIRONMENT` | `server/.env` | už existuje; `production` |
| `DJANGO_DEBUG` | `web_app/.env` (nový) | `false` v produkcii |
| `DJANGO_ALLOWED_HOSTS` | `web_app/.env` (nový) | `console.adhdknight.com` |
| `DJANGO_SECRET_KEY` | `web_app/.env` (nový) | produkčný secret, nikdy v gite |
| `DJANGO_DATABASE_URL` | `web_app/.env` (nový) | `postgresql://...` pre `adhd_web` databázu |
