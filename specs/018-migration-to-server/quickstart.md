# Quickstart: HTTPS/TLS + Basic Auth + PostgreSQL — Validačný sprievodca

**Feature**: 018 — HTTPS / TLS Setup pre produkčné nasadenie
**Prerekvizity**: Debian produkčný server s verejnou IP, DNS `A` záznamy pre `api.adhdknight.com` a `console.adhdknight.com` smerujúce naň, Nginx nainštalovaný, PostgreSQL nainštalovaný, dátová migrácia zo SQLite dostupná z **017** (blocker, ak chýba — pozri `research.md` Decision 8).

Tento sprievodca sa spúšťa **na produkčnom serveri** (alebo staging kópii) po dobehnutí `deploy/scripts/install.sh` (viď `tasks.md`). Kroky zodpovedajú acceptance scenárom v `spec.md`.

---

## Scenár 1: HTTPS bez cert warningu (US1, SC-001)

```bash
curl -vI https://api.adhdknight.com/api/v1/health 2>&1 | grep -E "SSL certificate|HTTP/"
curl -vI https://console.adhdknight.com/ 2>&1 | grep -E "SSL certificate|HTTP/"
```

**Očakávanie**: `curl` neohlási `SSL certificate problem`; TLS handshake prebehne cez Let's Encrypt reťazec.

---

## Scenár 2: HTTP → HTTPS redirect (FR-003)

```bash
curl -I http://api.adhdknight.com/
curl -I http://console.adhdknight.com/
```

**Očakávanie**: obe vrátia `301` s `Location: https://...`.

---

## Scenár 3: Basic Auth len na konzole (US2, SC-004)

```bash
# Bez credentials → 401 skôr, než Django appka dostane request
curl -I https://console.adhdknight.com/
# Očakávanie: HTTP/1.1 401 Unauthorized, WWW-Authenticate: Basic ...

# S credentials → prejde na Django
curl -I -u admin:<heslo> https://console.adhdknight.com/
# Očakávanie: 200/302 (Django login redirect), NIE 401

# API doména nemá basic auth vôbec
curl -I https://api.adhdknight.com/api/v1/health
# Očakávanie: žiadna WWW-Authenticate hlavička
```

---

## Scenár 4: Certifikát — obnova (US1 edge case, SC-002)

```bash
sudo certbot renew --dry-run
systemctl status certbot.timer
```

**Očakávanie**: dry-run prebehne bez chyby; `certbot.timer` je `active` (obnova beží automaticky, žiadna app-side zmena).

---

## Scenár 5: Lokálny dev mód nezmenený (FR-004, SC-003)

Na vývojovom stroji (nie produkčný server):

```bash
cd server && make dev      # beží na http://192.168.x.x:8095 bez TLS
cd web_app && python manage.py runserver
```

**Očakávanie**: oba bežia ako doteraz, žiadna TLS konfigurácia sa nevyžaduje. Android app s `network_security_config.xml` (016) sa pripojí cez plain HTTP na private IP bez zmeny.

---

## Scenár 6: PostgreSQL len na localhost (SC-005)

Zo servera:

```bash
psql -h 127.0.0.1 -U adhd_server -d adhd_server -c "select 1;"   # očakávaný úspech (po zadaní hesla)
```

Z **externého** stroja (iný než produkčný server):

```bash
psql -h <verejná-ip-produkčného-servera> -U adhd_server -d adhd_server -c "select 1;"
# Očakávanie: connection refused / timeout
```

```bash
sudo -u postgres psql -c "SHOW listen_addresses;"
# Očakávanie: localhost
```

---

## Scenár 7: Dátová migrácia zo SQLite (spustenie nástroja z 017)

```bash
# Spúšťa existujúci nástroj z 017 — 018 ho NEIMPLEMENTUJE, len volá
./deploy/scripts/install.sh --step migrate-data
```

**Očakávanie**: ak nástroj z `017-migration-to-postgres` chýba, skript zlyhá s explicitnou chybou (`"017 migration tool not found — see specs/017-migration-to-postgres"`), nie s tichým preskočením.

---

## Rollback poznámka

Ak niektorý krok zlyhá:
- Nginx: `nginx -t` pred `systemctl reload nginx` — nikdy needitovaný config priamo reloadovať bez syntax-checku.
- Postgres: dáta zostávajú v SQLite (`server/dev.db`, `web_app/db.sqlite3`) nedotknuté, kým migrácia neprebehne úspešne — appka môže dočasne bežať aj so SQLite `DATABASE_URL` fallbackom (017 FR-002).
