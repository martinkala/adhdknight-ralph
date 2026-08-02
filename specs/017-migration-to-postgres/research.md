# Research: Migrácia servera na PostgreSQL — dátový migračný skript

**Feature**: 017 — SQLite → PostgreSQL dátová migrácia (`server/scripts/migrate_sqlite_to_postgres.py`)
**Date**: 2026-08-02

Scope tejto fázy je úzky — FR-001–FR-003 (nasaditeľnosť, `DATABASE_URL` switch, Alembic proti Postgres) sú už implementované a overené v produkcii (018). Zostáva len FR-004/FR-005: samotný skript na prenos dát.

---

## Decision 1: SQLAlchemy ORM dual-engine namiesto externého nástroja (pgloader, `pg_dump`/`pg_restore`)

**Decision**: Skript použije dva SQLAlchemy async engine — jeden na zdrojovú SQLite (`sqlite+aiosqlite:///...`), druhý na cieľovú PostgreSQL (`get_settings().database_url` z `.env`) — a existujúce modely z `server/app/models/`.

**Rationale**:
- Server už má SQLAlchemy modely definované raz, zdieľané medzi SQLite aj PostgreSQL (`app/db/database.py` `_make_engine()` už prepína dialekt podľa `DATABASE_URL`) — netreba žiadny nový nástroj ani závislosť.
- `pgloader`/`pg_dump`+`pg_restore` sú mocnejšie pre veľké datasety, ale vyžadujú inštaláciu ďalšieho systémového balíka a nevedia priamo pracovať s SQLite ORM vrstvou — pri dev-scale objeme dát (rádovo stovky-tisícky riadkov, jeden vývojár) je to zbytočná komplexita.
- ORM prístup umožňuje jednoducho overiť FK integritu a poradie vkladania cez existujúce `relationship()` definície.

**Alternatives considered**:
- **`pgloader`**: rýchlejšie pre veľké objemy, ale nový systémový dependency a menej kontroly nad chybovými stavmi/rollbackom v rámci existujúceho `.venv`.
- **Raw SQL export/import**: krehké pri type coercion (SQLite je typovo voľné, Postgres striktný — napr. `Boolean`, `DateTime(timezone=True)`), ORM vrstva to rieši automaticky.

---

## Decision 2: Poradie prenosu — podľa FK závislostí

**Decision**: Pevné poradie tabuliek: `users` → `tracking_days` → `element_values` + `daily_indices` → `weight_configs` → `sync_records`.

**Rationale**: `tracking_days.user_id`, `weight_configs.user_id`, `sync_records.user_id` MUST odkazovať na existujúci `users.id`; `element_values.tracking_day_id`/`daily_indices.tracking_day_id` MUST odkazovať na existujúci `tracking_days.id`. Vkladanie v tomto poradí garantuje, že FK constraint nikdy nezlyhá.

---

## Decision 3: Primárne kľúče a cudzie kľúče sa prenášajú bez zmeny (žiadny remapping)

**Decision**: Všetky `id` stĺpce sú už UUID stringy (`String(36)`) generované v Pythone (`default=lambda: str(uuid.uuid4())`) — pri migrácii sa hodnoty kopírujú 1:1, nič sa negeneruje nanovo.

**Rationale**: Keďže PK aj FK sú UUID (nie auto-increment integer), nehrozí kolízia medzi zdrojom a cieľom ani potreba prekladovej mapy starý-ID → nový-ID. Zjednodušuje to logiku na priamy `INSERT` s pôvodnými hodnotami.

---

## Decision 4: `daily_indices.index_value` sa prenáša tak ako je, NEPREPOČÍTAVA sa

**Decision**: Historické hodnoty indexu (`DailyIndex.index_value`, `detail_json`, `config_version`) sa kopírujú presne tak, ako boli pôvodne vypočítané — skript ich nikdy neprepočítava cez `index_calculator.py`.

**Rationale**: Prepočet by mohol dať iný výsledok, ak sa medzičasom zmenil výpočtový algoritmus alebo váhy (Constitution Principle II — zmena parametrov vyžaduje explicitné zdôvodnenie v PR). Dátová migrácia MUST byť čisto kópia, nie reprocessing — inak by "bez straty dát" (SC-003) nebolo pravda (hodnoty by sa mohli tíško zmeniť).

---

## Decision 5: Idempotencia — odmietni beh, ak cieľová DB už má dáta

**Decision**: Pred akýmkoľvek zápisom skript skontroluje `SELECT COUNT(*) FROM users` na cieľovej PostgreSQL. Ak je nenulový, skript **skončí s chybou** (exit code ≠ 0) a nič nezapíše, pokiaľ nie je explicitne spustený s `--force`.

**Rationale**: Chráni pred duplicitným behom (napr. omylom spustený `install.sh --step migrate-data` druhýkrát) — bez tejto poistky by druhý beh buď zlyhal na UNIQUE constraint (čiastočne, chaoticky) alebo v horšom prípade duplicity tíško vytvoril. `--force` existuje pre vedomé re-migrácie (napr. po oprave chyby v skripte), nie pre bežný prevádzkový beh.

---

## Decision 6: Transakčnosť — celý prenos v jednej transakcii, rollback pri akejkoľvek chybe

**Decision**: Všetky INSERTy do PostgreSQL prebehnú v rámci jednej `AsyncSession` transakcie; pri akejkoľvek výnimke sa spraví `rollback()` a skript skončí s nenulovým exit kódom — cieľová DB ostane presne v stave pred spustením (buď prázdna, alebo nezmenená pri `--force` behu na existujúcich dátach... pozn: `--force` prípad nie je v scope MVP tejto feature, len guard na prvý spustiteľný beh).

**Rationale**: Priamo rieši Edge Case zo spec.md: *"Čo ak PostgreSQL migrácia zlyhá na polovici? → transakcie zabezpečia rollback — databáza ostane v konzistentnom stave."* Predtým sa to vzťahovalo na Alembic schema migrácie; tu sa rovnaký princíp aplikuje na dátovú migráciu.

---

## Decision 7: Zdroj a cieľ — odkiaľ skript berie connection stringy

**Decision**:
- **Cieľ** (PostgreSQL): `get_settings().database_url` — rovnaký `.env` mechanizmus, aký používa bežiaci server. Skript MUST odmietnuť beh, ak `is_sqlite` je `True` (t.j. `.env` ešte nemá nastavený produkčný `DATABASE_URL`) — inak by "migroval" SQLite → SQLite, čo je nezmysel.
- **Zdroj** (SQLite): pozičný CLI argument, default `./dev.db` (relatívne k `server/`, rovnaký default ako `config.py`'s `sqlite+aiosqlite:///./dev.db`). `deploy/scripts/install.sh` volá skript bez argumentov (`"$SERVER_DIR/.venv/bin/python" "$migration_tool"`), takže default MUST fungovať bez parametrov v bežnom produkčnom scenári, kde operátor predtým nakopíruje svoj `dev.db` do `server/dev.db` na serveri (manuálny krok, mimo scope — pozri spec.md Assumptions).

**Rationale**: Konzistentné s existujúcim `.env`-driven vzorom v `config.py`; nulová dodatočná konfigurácia potrebná na strane 018's `install.sh` volania.

---

## Decision 8: Testovanie bez potreby živého PostgreSQL v CI

**Decision**: Unit testy použijú **dve dočasné SQLite databázy** (jedna ako "zdroj" s naseedovanými dátami, druhá prázdna ako "cieľ") namiesto reálneho PostgreSQL — samotná ORM transferová logika je DB-agnostická (rovnaké modely, rovnaký `Base.metadata`), takže korektnosť prenosu (FK integrita, počty riadkov, guard pri neprázdnom cieli, rollback pri chybe) sa dá plne overiť bez PostgreSQL závislosti v `make test`.

**Rationale**: `make test` (Constitution VI — "Zakázané: Reálne sieťové volania v testoch... deterministické a offline-spustiteľné") by inak vyžadoval bežiaci PostgreSQL v CI. Skutočná PostgreSQL kompatibilita je už overená in-produkcii (018) a v `quickstart.md` (manuálny beh na serveri).
