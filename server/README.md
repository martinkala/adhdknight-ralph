# ADHD Weight Vector Server

FastAPI server for computing the ADHD behavioural index — identical algorithm to the Android app.

**Primary purpose**: Regression testing of the weight-vector algorithm without a mobile device.

## Prerequisites

- Python 3.11+
- pip

## Quick Start

```bash
cd server
make dev
```

This will:
1. Verify Python 3.11+
2. Install dependencies from `requirements.txt`
3. Copy `.env.example` → `.env` if not present
4. Run Alembic migrations (SQLite by default)
5. Start Uvicorn on `http://192.168.77.24:8095`

> **Note**: the `dev` target in `Makefile` binds to a hardcoded LAN IP (`192.168.77.24`) so a phone on the same network can reach it — this is *not* `0.0.0.0`, so if your machine's IP differs, `make dev` will fail to bind. Either edit the `--host` value in `Makefile`, or run Uvicorn directly with `--host 0.0.0.0` to listen on all interfaces:
> ```bash
> .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8095
> ```

## Running Tests

```bash
make test        # pytest (unit + API)
make test-bdd    # behave BDD feature files
make test-all    # both with coverage report
```

## API Documentation

Once running, open: **http://192.168.77.24:8095/docs** (or `http://localhost:8095/docs` if you started Uvicorn with `--host 0.0.0.0`/`localhost` yourself)

### Key endpoints

```bash
# Health check
curl http://192.168.77.24:8095/api/v1/health

# Compute daily index
curl -X POST http://192.168.77.24:8095/api/v1/compute/daily \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","date":"2026-06-30","entity_config":{"sleep":{"weight":15.0,"impact":1,"parent":null,"scale":true}},"values":[{"element_key":"sleep","value_binary":1,"value_scale":4}],"active_keys":["sleep"]}'

# Compute range (multiple days)
curl -X POST http://192.168.77.24:8095/api/v1/compute/range \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","entity_config":{"sleep":{"weight":15.0,"impact":1,"parent":null,"scale":true}},"days":[{"date":"2026-06-30","values":[{"element_key":"sleep","value_binary":1,"value_scale":5}],"active_keys":["sleep"]}]}'
```

## Configuration

Copy `.env.example` to `.env` and edit as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./dev.db` | Database connection string |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | JWT refresh token TTL |
| `MONITORING_API_KEY` | `change-me-in-production` | `X-Monitoring-Key` value required by `GET /internal/monitoring/status` |
| `MONITORING_ACCOUNT_EMAIL` / `MONITORING_ACCOUNT_PASSWORD` | `monitor@adhdknight.internal` / `change-me-in-production` | Dedicated account the synthetic checks log in as (seeded by the `187ee05ae8ff_...` migration) |
| `MONITORING_CHECK_INTERVAL_MINUTES` | `15` | How often `adhd-monitoring.timer` runs the checks |
| `MONITORING_ESCALATION_THRESHOLD` | `2` | Consecutive failures before an escalation warning is logged |
| `MONITORING_API_BASE_URL` / `MONITORING_WEB_CONSOLE_BASE_URL` | `http://127.0.0.1:8095` / `http://127.0.0.1:8000` | Where the synthetic checks point |
| `INTEGRITY_USER_COUNT_GROWTH_THRESHOLD` / `INTEGRITY_USER_DATA_GROWTH_THRESHOLD` | `20` / `100` | Growth-between-checks thresholds before an integrity warning is raised |

## Monitoring (feature 020)

`server/app/monitoring/` implements two scheduled checks, run together by
`scripts/run_monitoring_checks.py` on the `adhd-monitoring.timer` systemd timer
(see `deploy/systemd/adhd-monitoring.{service,timer}`):

- **Synthetic uptime**: logs into the web console and the API as the
  dedicated monitoring account, confirming real data is returned (catches a
  repeat of the dashboard "no data" bug, not just a down login page).
- **Integrity**: captures a snapshot of total user count and per-user data
  volume, comparing it against the previous snapshot and raising a warning on
  excessive growth.

Operators check current status via:

```bash
curl -H "X-Monitoring-Key: $MONITORING_API_KEY" http://127.0.0.1:8095/internal/monitoring/status
```

Both check failures and escalations (2+ consecutive failures by default) are
logged at WARNING/ERROR level into `logs/api.log` (see "Logging" below) —
consumed by whatever log-watching an operator already has in place.

## Logging

The API writes to `server/logs/api.log` (rotating, 10MB × 5 backups) — see
`app/logging_config.py`. This is separate from the Django web console's own
`web_app/logs/web.log`, so each service's log output can be monitored
independently (feature 020, goal 4).

## PostgreSQL Setup (optional)

```bash
# Install PostgreSQL driver
pip install asyncpg

# Set in .env:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adhd_tracker
```

### Dátová migrácia zo SQLite (feature 017)

Po tom, čo `DATABASE_URL` ukazuje na PostgreSQL a `alembic upgrade head` vytvoril prázdnu schému, prenes existujúce dáta z lokálneho `dev.db`:

```bash
.venv/bin/python scripts/migrate_sqlite_to_postgres.py [cesta-k-dev.db]   # default: server/dev.db
```

Skript je transakčný (rollback pri akejkoľvek chybe) a odmietne beh, ak cieľová DB už obsahuje dáta (pridaj `--force` na vedomé opakovanie). Podrobnosti a validačné scenáre: `specs/017-migration-to-postgres/quickstart.md`, kontrakt (exit kódy): `specs/017-migration-to-postgres/contracts/cli-contract.md`.

### Reset hesla používateľa

Appka nemá "forgot password" flow — ak si niekto zabudne heslo, resetuje sa priamo v DB:

```bash
.venv/bin/python scripts/reset_user_password.py used-email@example.com          # opýta sa na nové heslo (2x)
.venv/bin/python scripts/reset_user_password.py used-email@example.com --password 'novehesolo'
```

Funguje proti aktuálne nakonfigurovanej `DATABASE_URL` (SQLite lokálne, PostgreSQL na produkcii).

## Produkčné nasadenie (feature 018)

Cieľ: `https://api.adhdknight.com` (tento FastAPI server) a `https://console.adhdknight.com`
(Django web konzola, `web_app/`) na jednom Debian produkčnom serveri, za Nginx reverse
proxy s Let's Encrypt certifikátmi, konzola navyše chránená HTTP Basic Auth, PostgreSQL
viazaný len na `localhost`. Podrobný kontext: `specs/018-migration-to-server/`
(`plan.md`, `research.md`, `data-model.md`, `quickstart.md`).

Všetky kroky nižšie spúšťa **inštalačný skript `deploy/scripts/install.sh`** — bud ho
spusti celý (`./deploy/scripts/install.sh`), alebo krok po kroku cez `--step <name>`
(pozri hlavičku skriptu pre presné názvy krokov). Skript predpokladá checkout repozitára
v `/opt/adhknight` a systémového používateľa `adhdmad` (uprav `deploy/systemd/*.service`
a `APP_ROOT`/`APP_USER` v skripte, ak sa tvoj server líši).

> **Feature 020**: `install.sh` zostáva pre jednorazové nastavenie servera (balíky,
> PostgreSQL, certbot). Pre opakované, idempotentné nasadenie novej verzie kódu (vrátane
> `adhd-monitoring` timeru) použi `deploy/ansible/` — pozri `deploy/ansible/README.md`.

### Predpoklady na serveri

- Debian s verejnou IP, DNS `A` záznamy pre obe domény smerujúce na túto IP
- `apt` prístup na inštaláciu balíkov (krok `packages` nižšie doinštaluje Nginx,
  PostgreSQL, certbot, rsync a ostatné — netreba nič pripravovať vopred)
- SSH prístup z dev hosta na server (bežný admin prístup — **žiadny GitHub kľúč sa na
  server neukladá**, zámerne, viď nižšie)
- SQLite→PostgreSQL migračný nástroj z **017-migration-to-postgres** — pozri
  `specs/018-migration-to-server/research.md` Decision 8. Ak `server/scripts/migrate_sqlite_to_postgres.py`
  ešte neexistuje, krok `migrate-data` nižšie zlyhá zámerne — je to blocker z 017, nie chyba tohto skriptu.

### Nasadenie kódu na server — bez GitHub kľúča na serveri

Server **neklonuje** repozitár z GitHubu sám (`git clone`) — to by vyžadovalo uložiť
deploy kľúč priamo na produkčnom stroji, čo pri kompromitácii servera zároveň
kompromituje prístup k repozitáru. Namiesto toho sa kód pushuje **z dev hosta** cez SSH,
ktorý na server aj tak už máš (bežný admin prístup):

```bash
# Na DEV hostovi (nie na serveri):
./deploy/scripts/push-deploy.sh                    # pushne HEAD aktuálnej vetvy do /opt/adhknight na app01
./deploy/scripts/push-deploy.sh master              # alebo konkrétny ref/branch
DEPLOY_SERVER=root@1.2.3.4 ./deploy/scripts/push-deploy.sh   # iný server/IP
```

Skript spraví `git archive` (pushne sa len to, čo je commitnuté — žiadne lokálne
rozrobené zmeny ani gitignored súbory) a `rsync --delete` na server, pričom necháva
nedotknuté server-side stavové veci (`.venv/`, `.env`, `dev.db`, `db.sqlite3`,
`staticfiles/`). GitHub repozitár tak slúži len ako záloha/verzovanie, nie ako zdroj,
z ktorého by server sám ťahal kód.

### Krok za krokom (na serveri, po `push-deploy.sh`)

0. **Systémové balíky** (`./deploy/scripts/install.sh --step packages`)
   `apt-get install` pre `nginx`, `certbot`/`python3-certbot-nginx`, `apache2-utils` (`htpasswd`),
   `rsync`, `python3-venv`. PostgreSQL sa inštaluje cez oficiálny PGDG repozitár (nie distro default —
   Django 6 vyžaduje PostgreSQL 14+, napr. Debian 11 má v repách len 13), pinovaná verzia `postgresql-16`
   (nastaviteľné cez `PG_VERSION` env premennú). Idempotentné — bezpečné spustiť opakovane.

1. **PostgreSQL — localhost-only** (`./deploy/scripts/install.sh --step postgres`)
   Overí/nastaví `listen_addresses = 'localhost'` v `postgresql.conf`. `pg_hba.conf`
   sa manuálne skontroluje (skript vypíše cestu k súboru) — MUST obsahovať len `local`
   (peer) a `host ... 127.0.0.1/32` riadky, žiadne `0.0.0.0/0`.

2. **Vytvor databázy** (`./deploy/scripts/install.sh --step databases`)
   Vytvorí role a databázy `adhd_server` (FastAPI) a `adhd_web` (Django) s placeholder
   heslami. **Zmeň placeholder heslá** (`ALTER ROLE adhd_server PASSWORD '...'` atď.)
   a zapíš skutočné heslá do `server/.env` (`DATABASE_URL`) a `web_app/.env`
   (`DJANGO_DATABASE_URL`) v ďalšom kroku.

3. **Priprav `.env` súbory**
   - `cp server/.env.example server/.env` → nastav `DATABASE_URL=postgresql+asyncpg://adhd_server:<heslo>@127.0.0.1:5432/adhd_server`, `ENVIRONMENT=production`, reálny `SECRET_KEY`.
   - `cp web_app/.env.example web_app/.env` → nastav `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS=console.adhdknight.com`, reálny `DJANGO_SECRET_KEY`, `DJANGO_DATABASE_URL=postgresql://adhd_web:<heslo>@127.0.0.1:5432/adhd_web`, a **`FASTAPI_URL=http://127.0.0.1:8095`** (default v `.env.example` je LAN adresa dev stroja — na produkcii oba servisy bežia na tom istom serveri, inak konzola hlási "Server nie je dostupný").
   - Žiadny z týchto súborov sa necommituje (obidva `.gitignore` ich pokrývajú).

4. **Nainštaluj závislosti, spusti migrácie, naštartuj appky** (`./deploy/scripts/install.sh --step deps-and-migrate`)
   Vytvorí `.venv` pre `server/` aj `web_app/`, nainštaluje `requirements.txt`, spustí
   `alembic upgrade head` (FastAPI) a `manage.py migrate` + `collectstatic` (Django),
   nainštaluje a naštartuje `systemd` jednotky `adhd-api.service` (Uvicorn, `127.0.0.1:8095`)
   a `adhd-web.service` (Gunicorn, `127.0.0.1:8000`). Po tomto kroku appky bežia lokálne,
   ale ešte nie sú dostupné z internetu (Nginx ešte nie je nakonfigurovaný).

5. **Dátová migrácia zo SQLite** (`./deploy/scripts/install.sh --step migrate-data`)
   Spustí nástroj z **017**. Ak chýba, skript **zlyhá s explicitnou chybou** — dorieš
   najprv 017, potom sa vráť k tomuto kroku (appka môže dovtedy bežať aj s SQLite
   fallbackom, viď `017 FR-002`).

6. **Nginx + Let's Encrypt certifikáty** (`./deploy/scripts/install.sh --step nginx-and-certs`)
   Nainštaluje `deploy/nginx/api.adhdknight.com.conf` a `console.adhdknight.com.conf` do
   `/etc/nginx/sites-available/` + symlink do `sites-enabled/`, overí `nginx -t`, a spustí
   `certbot --nginx` pre obe domény (HTTP-01 challenge — vyžaduje funkčný DNS + verejnú IP
   v tomto momente). Certbot pri tomto kroku **priamo upraví** live Nginx config na serveri
   (pridá `listen 443 ssl` blok a HTTP→HTTPS redirect) — súbory v repozitári zostávajú
   zámerne "pred-certbot" verzia, aby opätovné nasadenie z gitu neprepísalo certbotom
   spravovanú TLS konfiguráciu.
   Ak server nemá verejnú IP pre HTTP-01: `sudo certbot certonly --manual --preferred-challenges dns -d <domena>`.

7. **Auto-obnova certifikátov** (`./deploy/scripts/install.sh --step certbot-timer`)
   Povolí `certbot.timer` (súčasť Debian balíčka `certbot`) — obnova beží automaticky,
   žiadna akcia na strane appiek/klientov nie je potrebná (FR-002).

8. **Basic Auth pre konzolu** (`./deploy/scripts/install.sh --step basic-auth`)
   Vytvorí `/etc/nginx/.htpasswd_console` s **placeholder** credentials `admin`/`admin`.
   **AKCIA VYŽADOVANÁ MANUÁLNE**: hneď po tomto kroku spusti na serveri interaktívne:
   ```bash
   sudo htpasswd /etc/nginx/.htpasswd_console admin
   ```
   a zadaj skutočné produkčné heslo. Placeholder sa **nikdy** nesmie dostať do produkcie
   nezmenený a nikdy sa nezapisuje do repozitára (FR-005).

9. **Validácia** — spusti scenáre zo `specs/018-migration-to-server/quickstart.md` (TLS bez
   warningu, HTTP→HTTPS redirect, Basic Auth 401/200 na konzole vs. žiadny na API,
   `certbot renew --dry-run`, PostgreSQL odmietne pripojenie zvonku, `make dev` lokálne
   nezmenené).

### Poznámky

- `api.adhdknight.com` **nikdy** nemá `auth_basic` — `deploy/scripts/install.sh` to pri
  každom behu overí (`assert_api_has_no_basic_auth`) a odmietne pokračovať, ak by niekto
  túto direktívu do `deploy/nginx/api.adhdknight.com.conf` omylom pridal.
- Android `network_security_config.xml` (016) už povoľuje cleartext HTTP pre private IP —
  lokálny dev flow (`make dev`) sa touto featurou vôbec nemení (FR-004, SC-003).
- Rollback: `nginx -t` beží pred každým `systemctl reload nginx` v skripte; SQLite dáta
  (`server/dev.db`, `web_app/db.sqlite3`) zostávajú nedotknuté, kým migrácia neprebehne úspešne.

## Troubleshooting

**`python: command not found`** — use `python3` or ensure Python 3.11+ is on PATH.

**`alembic: command not found`** — run `pip install -r requirements.txt` first.

**`sqlite3.OperationalError: no such table`** — run `alembic upgrade head` or `make migrate`.

**Port 8095 already in use** — `lsof -ti:8095 | xargs kill` or change the port in `Makefile`.

**`make dev` hangs or fails with an address/bind error** — the `dev` target binds to a hardcoded IP (`192.168.77.24`); if that's not this machine's current IP, either update it in `Makefile` or run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8095` directly.

**Web console shows "Server nie je dostupný. Skúste neskôr."** — Django can't reach the FastAPI backend. Check `FASTAPI_URL` in `web_app/.env` — on production it MUST be `http://127.0.0.1:8095` (both services run on the same server), not the LAN dev default. `sudo journalctl -u adhd-web.service -n 100` will show the underlying `httpx.ConnectError`.
