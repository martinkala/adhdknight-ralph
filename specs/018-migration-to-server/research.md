# Research: HTTPS / TLS Setup pre produkčné nasadenie

**Feature**: 018 — HTTPS/TLS + Basic Auth + PostgreSQL hardening
**Date**: 2026-08-01

---

## Decision 1: Reverse proxy a TLS terminácia

**Decision**: Nginx server bloky per doména (`api.adhdknight.com`, `console.adhdknight.com`), TLS terminuje Nginx; `proxy_pass` na lokálne bežiace aplikačné servery (Uvicorn na `127.0.0.1:8095`, Gunicorn na `127.0.0.1:8000`).

**Rationale**:
- Spec (Assumptions) explicitne vyžaduje Nginx ako jediný webserver — Caddy sa nezvažuje.
- Jeden Nginx proces zvláda TLS terminaciu pre obe domény cez samostatné `server {}` bloky (SNI).
- Aplikačné servery zostávajú viazané na `127.0.0.1` — nie sú priamo vystavené do internetu.

**Alternatives considered**:
- **Caddy** (automatický HTTPS): jednoduchšie, ale spec explicitne vylučuje — Nginx je už na serveri.
- **TLS terminácia priamo v Uvicorne/Gunicorne**: zbytočná duplicita cert správy na dvoch miestach, žiadny benefit oproti Nginx.

---

## Decision 2: Certifikáty — Let's Encrypt

**Decision**: `certbot` s `python3-certbot-nginx` pluginom, samostatný certifikát per doména (`certbot --nginx -d api.adhdknight.com`, `certbot --nginx -d console.adhdknight.com`). Obnova cez systémový `certbot.timer` (súčasť Debian balíčka `certbot`), žiadny vlastný cron.

**Rationale**:
- `--nginx` plugin automaticky upraví `server {}` blok (pridá `listen 443 ssl`, cert cesty) a nastaví HTTP→HTTPS redirect.
- Debian `certbot` balík inštaluje `certbot.timer` (beží 2× denne, obnovuje certifikáty <30 dní pred expiráciou) — spĺňa FR-002 (žiadna manuálna údržba) a edge case "obnova 30 dní pred vypršaním".
- Samostatné certifikáty (nie jeden SAN cert) — jednoduchšia rotácia, doména môže byť obnovená nezávisle.

**Alternatives considered**:
- **DNS challenge** (spomenuté v spec Edge Cases ako alternatíva): potrebné len ak server nemá verejnú IP pre HTTP-01 challenge. Podľa Assumptions server MÁ verejnú IP → HTTP-01 (webroot/nginx plugin) je primárna cesta; DNS challenge sa dokumentuje ako fallback poznámka v quickstart, nie ako default.

---

## Decision 3: HTTP → HTTPS redirect

**Decision**: Nginx `server { listen 80; server_name <domena>; return 301 https://$host$request_uri; }` pre obe domény — vygenerované automaticky certbot `--nginx` pluginom.

**Rationale**: FR-003 vyžaduje redirect na oboch doménach; certbot nginx plugin toto rieši bez manuálnej úpravy configu.

---

## Decision 4: HTTP Basic Auth len na konzole

**Decision**: `auth_basic` + `auth_basic_user_file /etc/nginx/.htpasswd_console;` v `server {}` bloku pre `console.adhdknight.com` (443, `location /`). Súbor `.htpasswd_console` sa generuje na serveri príkazom `htpasswd -c /etc/nginx/.htpasswd_console admin` s placeholder heslom `admin` pri prvej inštalácii — **mimo repozitára**, nie je súčasťou verzovaných configov.

**Rationale**:
- FR-005: basic auth iba na konzole, nikdy na API doméne — realizované tým, že `auth_basic` direktíva sa objaví len v `console.adhdknight.com` config súbore.
- Nginx vyhodnotí `auth_basic` skôr, než požiadavka dôjde k `proxy_pass` → Django appka basic auth vôbec nevidí (spĺňa acceptance scenár 1 v US2).
- Heslo sa nikdy nezapisuje do repozitára — inštalačný skript vytvorí `.htpasswd_console` s placeholder heslom a vypíše explicitnú výzvu operátorovi, aby ho zmenil (`htpasswd /etc/nginx/.htpasswd_console admin`) manuálne po inštalácii.

**Alternatives considered**:
- **Basic auth v Django middleware**: zbytočné, request by musel prejsť celým WSGI stackom skôr, než sa zamietne — Nginx-level je lacnejšie a spĺňa "predtým, než sa načíta čokoľvek z Django appky" (acceptance scenár 1).

---

## Decision 5: Proces supervision — systemd

**Decision**: Dve `systemd` unit služby:
- `adhd-api.service` — spúšťa `uvicorn app.main:app --host 127.0.0.1 --port 8095` z `server/` adresára, `EnvironmentFile=server/.env`, `Restart=on-failure`.
- `adhd-web.service` — spúšťa `gunicorn adhd_web.wsgi:application --bind 127.0.0.1:8000` z `web_app/` adresára.

**Rationale**:
- FastAPI aplikácia je async (ASGI) → Uvicorn priamo je štandardná voľba pre jeden proces za Nginx (Nginx sám robí load-balancing/queueing na TCP úrovni, netreba Gunicorn+workers navrstvu pre tento scale).
- Django je WSGI → Gunicorn je štandardná produkčná voľba (nie `manage.py runserver`, ktorý nie je pre produkciu).
- `systemd` (nie Supervisor/PM2) — už je súčasť Debianu, žiadna nová závislosť.

**Alternatives considered**:
- **Gunicorn s uvicorn workers pre FastAPI**: viac procesov = viac RAM za bezvýznamný benefit pri tomto scale (1 produkčný server, nízka záťaž). Ponechané ako budúca optimalizácia, nie súčasť tejto feature.

---

## Decision 6: PostgreSQL — localhost-only binding

**Decision**: Ponechať Debian default `listen_addresses = 'localhost'` v `postgresql.conf` (Debian balík `postgresql` toto nastavuje ako default, netreba meniť) a overiť/zdokumentovať `pg_hba.conf` tak, aby akceptoval len `127.0.0.1/32` a `local` (unix socket) spojenia s `scram-sha-256` heslom. Dve databázy: `adhd_server` (FastAPI, vlastník `017-migration-to-postgres`) a `adhd_web` (Django, vlastník tejto feature) — každá s vlastným DB rolem.

**Rationale**:
- FR-006: PostgreSQL prístupný len z localhost, používajú ho API aj web konzola na tom istom serveri — Debian default `listen_addresses='localhost'` už toto zabezpečuje bez zásahu; explicitná verifikácia v quickstart (`psql` z externej adresy zlyhá) namiesto zmeny configu naslepo.
- Oddelené databázy pre FastAPI a Django — logická izolácia, žiadne zdieľané schémy, jednoduchšie zálohovanie/rollback.

**Alternatives considered**:
- **Jedna spoločná databáza pre FastAPI aj Django**: zbytočné previazanie dvoch nezávislých aplikácií cez zdieľanú schému; Django navyše nemá vlastné doménové modely (len auth/sessions), netreba zdieľať s FastAPI dátami.

---

## Decision 7: Django produkčné nastavenia

**Decision**: `web_app/adhd_web/settings.py` sa rozšíri o env-driven konfiguráciu (rovnaký vzor ako `server/app/config.py` — dev-friendly default, produkcia cez `.env`):
- `DEBUG` ← `DJANGO_DEBUG` env (default `True` pre nezmenené lokálne správanie)
- `ALLOWED_HOSTS` ← `DJANGO_ALLOWED_HOSTS` env (comma-separated, default `[]`)
- `SECRET_KEY` ← `DJANGO_SECRET_KEY` env (default = existujúci insecure kľúč, len pre dev)
- `DATABASES` ← ak je nastavené `DJANGO_DATABASE_URL`, použiť PostgreSQL; inak fallback na existujúce SQLite (`db.sqlite3`)
- `CSRF_TRUSTED_ORIGINS = ['https://console.adhdknight.com']` (staticky, keďže doména je pevne daná v spec)
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` — Nginx posiela `X-Forwarded-Proto`, Django tak správne rozpozná HTTPS request cez proxy
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` (nový) — `collectstatic` pre produkčné servovanie statiky priamo cez Nginx

**Rationale**: Zachováva `make dev`/lokálny beh bez zmeny (žiadne env premenné nastavené = súčasné správanie), pridáva len to, čo produkcia potrebuje. Rovnaký env-var-driven vzor ako FastAPI server (`server/app/config.py`) — konzistentnosť naprieč repozitárom.

---

## Decision 8: SQLite → PostgreSQL dátová migrácia — závislosť na 017

**Decision**: Inštalačný postup 018 obsahuje krok "spusti migračný skript", ktorý **volá** nástroj vlastnený featurou `017-migration-to-postgres` (očakávaná cesta: `server/scripts/migrate_sqlite_to_postgres.py`, alebo ekvivalent, podľa toho, čo 017 dodá). K dátumu tohto plánu (2026-08-01) `017` má iba `spec.md` — samotný migračný skript **neexistuje**.

**Rationale**: Spec 018 explicitne stanovuje: *"018 túto migráciu nerieši nanovo... Ak nástroje z 017 ešte neexistujú/nie sú hotové, je to blocker pre 018, nie duplicitná práca v 018."* Preto:
- Tasks pre 018 NEBUDÚ implementovať SQLite→Postgres dátovú migračnú logiku.
- Inštalačný skript (`deploy/scripts/install.sh`) bude mať krok, ktorý referencuje nástroj z 017 a **zlyhá s jasnou chybovou hláškou**, ak nástroj chýba, namiesto tichého preskočenia alebo re-implementácie.
- Toto je zdokumentovaný externý blocker, nie súčasť Complexity Tracking (nejde o architektonickú výnimku, ale o cross-feature dependency).

**Poznámka k stavu 017 v kóde**: Časť infraštruktúry, ktorú 017 vyžaduje, už v `server/` existuje (`DATABASE_URL` env-switch v `config.py`, `asyncpg` v `requirements.txt`, Alembic migrácie sú DB-agnostické cez SQLAlchemy). Chýba konkrétne: skript na prenos existujúcich riadkov zo `dev.db` (SQLite) do PostgreSQL.

---

## Decision 9: Verifikácia (namiesto automatizovaných testov)

**Decision**: Táto feature nemá tradičné unit/integration testy (nie je to aplikačný kód, ale infraštruktúrna konfigurácia). Validácia prebieha cez `quickstart.md` — sada `curl`/`psql`/prehliadačových krokov spustených na reálnom (alebo staging) produkčnom serveri, mapovaných 1:1 na acceptance scenáre v spec.md.

**Rationale**: Nginx/systemd/Postgres konfiguračné súbory sa netestujú JVM/pytest testami — validujú sa behaviorálne (HTTP status kódy, TLS handshake, connection refused). Toto zodpovedá "Independent Test" sekciám v spec.md, ktoré sú už formulované ako manuálne overiteľné kroky.
