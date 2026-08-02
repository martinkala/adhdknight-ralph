# Quickstart: SQLite → PostgreSQL dátová migrácia — Validačný sprievodca

**Feature**: 017 — `server/scripts/migrate_sqlite_to_postgres.py`

---

## Scenár 1: Lokálny suchý beh (pred nasadením)

```bash
cd server
cp dev.db /tmp/dev_test.db   # nepracuj priamo s ostrým dev.db

# Nastav dočasne DATABASE_URL na lokálnu Postgres inštanciu (docker/lokálny postgres)
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/adhd_server_test
.venv/bin/alembic upgrade head   # priprav prázdnu cieľovú schému

.venv/bin/python scripts/migrate_sqlite_to_postgres.py /tmp/dev_test.db
```

**Očakávanie**: exit code `0`, výpis počtu riadkov per tabuľka, zdroj == cieľ pre každú z nich.

---

## Scenár 2: Guard proti duplicitnému behu

```bash
.venv/bin/python scripts/migrate_sqlite_to_postgres.py /tmp/dev_test.db
```

**Očakávanie** (spustené znova na tej istej, už naplnenej cieľovej DB): exit code `1`, chyba "Destination database is not empty — pass --force to re-run". Cieľová DB sa nezmenila (over cez `psql -c "select count(*) from users;"` — počet ostáva rovnaký ako po prvom behu).

---

## Scenár 3: Produkčný beh (na serveri, súčasť `install.sh --step migrate-data`)

Predpoklad: `server/.env` na produkčnom serveri už má nastavený `DATABASE_URL` na `adhd_server` (pozri `specs/018-migration-to-server/quickstart.md` krok 3).

```bash
# Na dev hoste — nakopíruj svoj lokálny dev.db na server (mimo scope tejto feature, manuálny krok):
scp server/dev.db root@<server>:/opt/adhknight/server/dev.db

# Na serveri:
cd /opt/adhknight
bash deploy/scripts/install.sh --step migrate-data
```

**Očakávanie**: exit code `0` (ak `server/scripts/migrate_sqlite_to_postgres.py` existuje a cieľová `adhd_server` DB je prázdna — čo je stav po `install.sh --step databases`), výpis počtu riadkov per tabuľka.

---

## Scenár 4: Overenie po migrácii — počty riadkov sedia (SC-003)

```bash
# Na serveri, porovnaj SQLite (zdroj) vs PostgreSQL (cieľ):
sqlite3 server/dev.db "SELECT count(*) FROM users; SELECT count(*) FROM tracking_days; SELECT count(*) FROM element_values; SELECT count(*) FROM daily_indices; SELECT count(*) FROM weight_configs; SELECT count(*) FROM sync_records;"

sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM users;"
sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM tracking_days;"
sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM element_values;"
sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM daily_indices;"
sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM weight_configs;"
sudo -u postgres psql -d adhd_server -c "SELECT count(*) FROM sync_records;"
```

**Očakávanie**: každý pár čísiel je zhodný.

---

## Scenár 5: Funkčné overenie cez API (nie len počty riadkov)

```bash
# Prihlás sa existujúcim (zmigrovaným) účtom cez produkčné API:
curl -X POST https://api.adhdknight.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<existujúci-email-z-dev-dát>","password":"<jeho-heslo>"}'
```

**Očakávanie**: `200` s platným JWT tokenom — potvrdzuje, že `password_hash` a ostatné dáta prešli bez poškodenia (nielen že riadky existujú, ale sú aj funkčne správne).
