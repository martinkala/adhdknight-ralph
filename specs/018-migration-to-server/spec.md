# Feature Specification: HTTPS / TLS Setup pre produkčné nasadenie

**Feature Branch**: `018-migration-to-server`

**Created**: 2026-07-10

**Status**: Draft

**Prerekvizita**: 016-application-server-connect (F1), 017-migration-to-postgres

---

## Kontext a účel

Server beží v lokálnom prostredí cez HTTP. Pred produkčným nasadením je potrebné zabezpečiť komunikáciu cez HTTPS/TLS. Let's Encrypt poskytuje automaticky obnovované certifikáty. Klienti (mobilná app, web app) nevyžadujú zmeny — TLS je na transportnej vrstve servera.

Vlastné end-to-end šifrovanie sa **neimplementuje** — TLS/HTTPS je dostatočná úroveň zabezpečenia pre tento use case. Certifikátový pinning v mobilnej app sa **neimplementuje** — systémový trust store je dostatočný.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Bezpečná komunikácia cez HTTPS (Priority: P1)

Komunikácia medzi klientmi (mobilná app, web app) a serverom je zabezpečená štandardným HTTPS/TLS. Certifikáty sú spravované automaticky (Let's Encrypt) na strane servera. Klienti nevyžadujú vlastné certifikáty.

**Why this priority**: Bezpečnosť je prerekvizitou pre produkčné nasadenie. HTTP je akceptovateľné len pre lokálny vývoj.

**Independent Test**: Nasaď server s HTTPS certifikátom → mobilná app aj web app sa pripoja bez chybového hlásenia. Certifikát vyprší a obnoví sa automaticky → klienti pokračujú bez zmeny.

**Acceptance Scenarios**:

1. **Given** server beží na HTTPS doméne s platným certifikátom, **When** mobilná app odošle dáta, **Then** komunikácia prebehne bez varovania o certifikáte.
2. **Given** certifikát sa automaticky obnoví (napr. Let's Encrypt každých 90 dní), **When** k obnove dôjde, **Then** mobilná app ani web app nevyžadujú žiadnu aktualizáciu.
3. **Given** server beží lokálne na HTTP (dev prostredie), **When** app sa pripojí, **Then** app akceptuje HTTP pripojenie v dev móde bez nutnosti inštalovať vlastný certifikát.

### Edge Cases

- Čo ak certifikát vyprší pred obnovením? → Let's Encrypt obnovuje 30 dní pred vypršaním; monitoring alertuje pri zlyhaní obnovy.
- Čo ak server nemá verejnú IP pre Let's Encrypt challenge? → DNS challenge ako alternatíva k HTTP challenge.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Komunikácia medzi klientmi a serverom MUST byť zabezpečená TLS (HTTPS) v produkčnom prostredí.
- **FR-002**: Certifikáty MUST byť spravované automaticky (Let's Encrypt) bez nutnosti aktualizovať mobilnú app ani web app.
- **FR-003**: HTTP → HTTPS redirect MUST byť aktívny v produkcii (port 80 → 443).
- **FR-004**: Lokálny dev mód (HTTP na `localhost` / private IP) MUST fungovať bez TLS — `network_security_config.xml` v Android app to už umožňuje.

### Non-functional Requirements

- Certifikátový pinning sa **neimplementuje** — systémový trust store je dostatočný.
- Vlastné E2E šifrovanie sa **neimplementuje**.

---

## Success Criteria *(mandatory)*

- **SC-001**: Mobilná app a web app sa pripoja k produkčnému serveru cez HTTPS bez varovania o certifikáte.
- **SC-002**: Obnova certifikátu nevyžaduje žiadnu aktualizáciu mobilnej app ani web app.
- **SC-003**: `make dev` (lokálne HTTP) naďalej funguje bez akejkoľvek TLS konfigurácie.

---

## Assumptions

- Produkčný server bude na doméne s verejnou IP — potrebné pre Let's Encrypt HTTP challenge.
- Nginx alebo Caddy ako reverse proxy pred FastAPI (TLS termination na proxy vrstve).
- Android `network_security_config.xml` (z feature 016) už povoľuje cleartext HTTP pre private IP — žiadna zmena v mobilnej app nie je potrebná.
