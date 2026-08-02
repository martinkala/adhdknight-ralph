# Contract: Produkčné HTTP správanie (Nginx edge)

**Feature**: 018 — HTTPS/TLS + Basic Auth + PostgreSQL hardening
**Date**: 2026-08-01

Toto je "kontrakt" vystavený navonok klientom (mobilná app, web prehliadač) — čo môžu očakávať na sieťovej hrane po nasadení tejto feature. Aplikačné API kontrakty (JSON schémy) sa nemenia — pozri `016-application-server-connect/contracts/`.

---

## `api.adhdknight.com`

| Request | Response | Poznámka |
|---|---|---|
| `GET http://api.adhdknight.com/*` (port 80) | `301 Moved Permanently` → `https://api.adhdknight.com/*` | FR-003 |
| `GET https://api.adhdknight.com/api/v1/health` | `200`, platný TLS reťazec (Let's Encrypt), žiadny cert warning | FR-001, SC-001 |
| ľubovoľná cesta na `api.adhdknight.com` | **žiadny** `401`/`WWW-Authenticate` z Nginxu — auth rieši appka sama (JWT) | FR-005, SC-004, acceptance scenár 3 (US2) |

## `console.adhdknight.com`

| Request | Response | Poznámka |
|---|---|---|
| `GET http://console.adhdknight.com/*` (port 80) | `301` → `https://console.adhdknight.com/*` | FR-003 |
| `GET https://console.adhdknight.com/` bez credentials | `401 Unauthorized` + hlavička `WWW-Authenticate: Basic realm="..."`, **skôr než request dôjde k Django** | FR-005, SC-004, acceptance scenár 1 (US2) |
| `GET https://console.adhdknight.com/` s platnými Basic Auth credentials | Nginx proxy-uje na Gunicorn (`127.0.0.1:8000`) → normálna Django odpoveď (vlastný login flow appky pokračuje za Basic Auth vrstvou) | acceptance scenár 2 (US2) |
| `GET https://console.adhdknight.com/static/*` | servované priamo Nginxom z `STATIC_ROOT` (nejde cez Django/Gunicorn) | Decision 7 v research.md |

## `localhost:5432` (PostgreSQL)

| Request | Response | Poznámka |
|---|---|---|
| `psql -h 127.0.0.1 ...` z toho istého serveru | pripojenie úspešné (po zadaní správnych credentials) | FR-006 |
| `psql -h <verejná IP servera> ...` z externého hosta | connection refused / timeout | FR-006, SC-005 |

## Lokálny dev mód (nezmenené)

| Request | Response | Poznámka |
|---|---|---|
| `GET http://192.168.x.x:8095/*` (priamo Uvicorn, bez Nginx/TLS) | funguje ako doteraz | FR-004, SC-003 — `make dev` sa touto featurou nemení |
