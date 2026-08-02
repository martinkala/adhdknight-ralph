# Feature Specification: HTTPS / TLS Setup pre produkčné nasadenie

**Feature Branch**: `018-migration-to-server`

**Created**: 2026-07-10

**Status**: Draft

**Prerekvizita**: 016-application-server-connect (F1), 017-migration-to-postgres

**Produkčné domény**: API na `https://api.adhdknight.com`, web konzola na `https://console.adhdknight.com`.

---

## Kontext a účel

Server beží v lokálnom prostredí cez HTTP. Pred produkčným nasadením je potrebné zabezpečiť komunikáciu cez HTTPS/TLS. Let's Encrypt poskytuje automaticky obnovované certifikáty. Klienti (mobilná app, web app) nevyžadujú zmeny — TLS je na transportnej vrstve servera.

Vlastné end-to-end šifrovanie sa **neimplementuje** — TLS/HTTPS je dostatočná úroveň zabezpečenia pre tento use case. Certifikátový pinning v mobilnej app sa **neimplementuje** — systémový trust store je dostatočný.

**Vzťah k 017-migration-to-postgres**: 017 je vlastníkom logiky a nástrojov na migráciu SQLite → PostgreSQL (migračný skript, Alembic schéma). 018 túto migráciu **nerieši nanovo** — produkčný install postup (018) len **spúšťa už existujúce nástroje z 017** ako jeden krok v deploymente na produkčnom serveri. Ak nástroje z 017 ešte neexistujú/nie sú hotové, je to blocker pre 018, nie duplicitná práca v 018.

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

### User Story 2 — Basic auth na web konzole (Priority: P1)

Web konzola (`console.adhdknight.com`) je okrem TLS chránená aj HTTP Basic Auth na úrovni reverse proxy (nginx) — dodatočná vrstva, keďže konzola vystavuje dáta všetkých používateľov. API (`api.adhdknight.com`) basic auth nemá — používa vlastnú JWT autentifikáciu (016).

**Why this priority**: Web konzola nemá per-request autentifikáciu ako mobilná app/API; bez basic auth by bola verejne dostupná komukoľvek, kto pozná doménu.

**Independent Test**: Otvor `https://console.adhdknight.com` bez prihlasovacích údajov → prehliadač vyžiada Basic Auth predtým, než sa načíta čokoľvek z Django appky. Zadaj správne údaje → stránka sa načíta normálne (a následne rieši svoj vlastný login/session ako doteraz).

**Acceptance Scenarios**:

1. **Given** používateľ otvorí `https://console.adhdknight.com` bez credentials, **When** nginx prijme request, **Then** vráti `401` s `WWW-Authenticate` hlavičkou skôr, než request dôjde k Django aplikácii.
2. **Given** používateľ zadá platné Basic Auth credentials, **When** request prejde cez nginx, **Then** je proxy-ovaný na Django appku a pokračuje normálny login flow appky.
3. **Given** `api.adhdknight.com`, **When** príde ľubovoľný request, **Then** basic auth sa NEAPLIKUJE (len na konzolu, API si rieši auth sám cez JWT).

**Edge Case**: Aké heslo sa použije? → Pri prvotnej instalácii sa nastaví len placeholder (`admin`/`admin` — pozri `facts.txt`); **skutočné produkčné heslo MUSÍ nastaviť človek manuálne priamo pri inštalácii** (mimo repozitára, napr. `htpasswd` interaktívne na serveri). Placeholder sa nikdy nesmie dostať do produkcie ani do gitu ako reálne heslo.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Komunikácia medzi klientmi a serverom MUST byť zabezpečená TLS (HTTPS) v produkčnom prostredí — konkrétne `https://api.adhdknight.com` (API) a `https://console.adhdknight.com` (web konzola).
- **FR-002**: Certifikáty MUST byť spravované automaticky (Let's Encrypt) bez nutnosti aktualizovať mobilnú app ani web app.
- **FR-003**: HTTP → HTTPS redirect MUST byť aktívny v produkcii (port 80 → 443) pre obe domény.
- **FR-004**: Lokálny dev mód (HTTP na `localhost` / private IP) MUST fungovať bez TLS — `network_security_config.xml` v Android app to už umožňuje.
- **FR-005**: `console.adhdknight.com` MUST byť chránená HTTP Basic Auth na úrovni nginx, navyše k TLS — `api.adhdknight.com` basic auth MUST NOT mať (rieši si vlastnú JWT autentifikáciu). Placeholder credentials pri instalácii (`admin`/`admin`) MUST byť nahradené reálnym heslom manuálne človekom pri deployi, nie automatizovane ani natvrdo v repozitári.
- **FR-006**: PostgreSQL MUST byť viazaný len na localhost (unix socket alebo `127.0.0.1`) bez prístupu z vonkajšej siete — pristupovať k nemu MUST iba API a web konzola, obe bežiace na tom istom produkčnom serveri.

### Non-functional Requirements

- Certifikátový pinning sa **neimplementuje** — systémový trust store je dostatočný.
- Vlastné E2E šifrovanie sa **neimplementuje**.

---

## Success Criteria *(mandatory)*

- **SC-001**: Mobilná app a web app sa pripoja k produkčnému serveru cez HTTPS bez varovania o certifikáte.
- **SC-002**: Obnova certifikátu nevyžaduje žiadnu aktualizáciu mobilnej app ani web app.
- **SC-003**: `make dev` (lokálne HTTP) naďalej funguje bez akejkoľvek TLS konfigurácie.
- **SC-004**: `console.adhdknight.com` vyžiada Basic Auth pred akýmkoľvek obsahom; `api.adhdknight.com` basic auth nevyžiada.
- **SC-005**: Pokus o pripojenie na PostgreSQL z inej adresy než localhost produkčného servera zlyhá (connection refused / timeout).

---

## Assumptions

- Produkčný server bude na doméne s verejnou IP — potrebné pre Let's Encrypt HTTP challenge.
- Reverse proxy pred FastAPI aj Django appkou je **Nginx** — na produkčnom serveri je už nainštalovaný a je jediný webserver, žiadna alternatíva (Caddy) sa nezvažuje.
- Android `network_security_config.xml` (z feature 016) už povoľuje cleartext HTTP pre private IP — žiadna zmena v mobilnej app nie je potrebná.
- Doména API (`api.adhdknight.com`) a doména konzoly (`console.adhdknight.com`) smerujú na ten istý produkčný server, odlíšené cez nginx `server_name`/virtual hosty.
- Basic Auth credentials sa pri prvej inštalácii nastavia na placeholder (`admin`/`admin`) a manuálne ich zmení človek vykonávajúci inštaláciu — nikdy sa nemá do repozitára zapísať reálne produkčné heslo.
