# Contract: `server/scripts/migrate_sqlite_to_postgres.py` CLI

**Feature**: 017 — SQLite → PostgreSQL dátová migrácia
**Date**: 2026-08-02

Toto je kontrakt, na ktorý sa už spolieha `deploy/scripts/install.sh` (018, funkcia `migrate_data()`) — mení sa len so zodpovedajúcou zmenou na strane 018.

---

## Invokácia

```bash
# Bežný produkčný beh (018's install.sh volá presne takto, bez argumentov):
.venv/bin/python server/scripts/migrate_sqlite_to_postgres.py

# Explicitná zdrojová cesta (voliteľné, default "./dev.db" relatívne k server/):
.venv/bin/python server/scripts/migrate_sqlite_to_postgres.py /path/to/dev.db

# Vynútený beh aj pri neprázdnej cieľovej DB (mimo bežného flow, manuálne):
.venv/bin/python server/scripts/migrate_sqlite_to_postgres.py --force
```

## Vstupy

| Vstup | Zdroj | Povinné |
|---|---|---|
| Cieľová PostgreSQL | `DATABASE_URL` v `server/.env` (cez `get_settings()`) | áno — MUST byť `postgresql+asyncpg://...`, inak skript odmietne beh |
| Zdrojová SQLite | pozičný CLI argument, default `./dev.db` | nie |
| `--force` | CLI flag | nie (default `False`) |

## Výstupy / Exit kódy

| Scenár | Exit code | stdout/stderr |
|---|---|---|
| Úspešná migrácia | `0` | tabuľka `source_count → dest_count` per tabuľka, celkový súhrn |
| Cieľová DB nie je prázdna, bez `--force` | `1` | jasná chyba: "Destination database is not empty — pass --force to re-run" |
| `DATABASE_URL` je stále SQLite (nie je nastavený produkčný Postgres) | `1` | jasná chyba: "DATABASE_URL is not PostgreSQL — configure server/.env first" |
| Zdrojový SQLite súbor neexistuje | `1` | jasná chyba s cestou, ktorú skript hľadal |
| Chyba počas prenosu (akákoľvek) | `2` | traceback + "Rolled back — destination database unchanged" |

**Kontrakt s 018**: `deploy/scripts/install.sh`'s `migrate_data()` beží pod `set -euo pipefail` — akýkoľvek nenulový exit kód tohto skriptu zastaví celý `install.sh` beh. To je zámerné (žiadny "tichý" čiastočný úspech).
