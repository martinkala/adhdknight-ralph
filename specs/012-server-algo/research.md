# Research: Backend Weight Vector Server

**Date**: 2026-06-30 | **Feature**: 012-server-algo

---

## R-001: Tech Stack — FastAPI vs Flask vs Django

**Decision**: FastAPI

**Rationale**:
- Auto-generovaná OpenAPI dokumentácia (Swagger UI na `/docs`) — kritická pre testovací server kde vývojár ručne skúša endpointy
- Pydantic v2 validácia requestov — identická štruktúra ako Android data classes, ľahký port
- Native async — batch sync 30 dní spracovaný efektívne bez blocking
- Rýchlosť prototypovania: endpoint + validácia + docs = ~10 riadkov

**Alternatives considered**:
- Flask: sync-only, žiadne auto-docs, viac boilerplate pre JSON validation
- Django+DRF: admin UI zadarmo (benefit pre debug), ale overkill pre testovací server; DRF serializers sú verbose vs Pydantic

---

## R-002: Vstupno-výstupný formát

**Decision**: B2 — YAML pre testovacie fixturové súbory, JSON pre API komunikáciu

**Rationale**:
- YAML je human-editable bez quoted strings a zátvorkového noiseu — vývojár edituje fixture pre 30 dní ručne
- JSON je strojovo spoľahlivejší pre HTTP komunikáciu a natívny pre Android
- Oba formáty sú rozdelené podľa kontextu: YAML = vstup do BDD, JSON = API transport

**Backward compatibility stratégia**:
- Response JSON vždy obsahuje `"schema_version": "1.0"`
- Nové polia sú vždy nullable/optional
- Klienti ignorujú neznáme polia (Pydantic `model_config = ConfigDict(extra='ignore')`)

---

## R-003: Algoritmus pre elementy so subpoložkami

**Decision**: C1 — priemer aktívnych subpoložiek × váha rodiča

**Rationale**:
- Identické s aktuálnou implementáciou `computeDailyIndexGrouped` v Android appke
- Zaručuje backward compatibility: výsledky na serveri = výsledky v appke pre rovnaké vstupy (SC-002)
- Vzorec: `contribution = parent.weight × avg(active_children_effective)`
- Ak rodiča nemá aktívne deti → rodič prispieva priamo (existujúce správanie)
- Ak rodiča nemá deti vôbec → prispieva priamo vlastnou `value_effective`

**Alternatives considered**:
- C2 distribuovaná váha: iný výsledok ako Android app → poruší SC-002
- C3 explicitné váhy subpoložiek: vyžaduje migráciu konfigurácie, priveľa zmien pre MVP

---

## R-004: Databázové riešenie

**Decision**: PostgreSQL pre produkciu, SQLite pre localhost-dev (prepínač cez `DATABASE_URL` env var)

**Rationale**:
- PostgreSQL: ACID, native JSON/JSONB stĺpce pre `EntityConfig` flexibilitu, row-level locking pre sync conflict detection
- SQLite: nulová inštalácia pre lokálny dev, vývojár si serverový stav nemusí nastaviť
- Alembic migrácie sú kompatibilné s oboma (dialect-aware)

**Alternatives considered**:
- Len PostgreSQL: blokuje "easy-to-start" na čistom Linuxe bez Docker
- MongoDB: schemaless flexibilita nie je potrebná; SQL relačné garancie sú dôležité pre sync

---

## R-005: Autentifikácia

**Decision**: JWT (JSON Web Tokens) s bcrypt hashing hesiel

**Rationale**:
- Stateless — Android appka nemusí spravovať session cookies
- Access token (15 min) + Refresh token (30 dní) — štandard pre mobilné klienty
- bcrypt: adaptívny hash, odolný voči brute-force
- `python-jose` + `passlib[bcrypt]` — overené knižnice, štandardný FastAPI pattern

**Alternatives considered**:
- Session cookies: nevhodné pre REST API, komplikuje Android klienta
- API keys: jednoduchšie, ale neumožňuje budúce rozlíšenie rôznych zariadení/clientov
- OAuth2 external: overkill pre MVP, závislosť na externom provideri

---

## R-006: Conflict Resolution pre Offline Sync

**Decision**: Last-Write-Wins (LWW) na úrovni `TrackingDay` podľa `updated_at` timestamp

**Rationale**:
- Jednoduchá deterministická implementácia bez user interaction
- Android appka posiela `updated_at` pre každý záznam
- Server porovná: ak `incoming.updated_at > stored.updated_at` → prepíše; inak → zachová server verziu
- Audit trail: obidve verzie zachované v `SyncRecord.conflict_log` (JSON)

**Alternatives considered**:
- Field-level merge: komplexné, UI pre riešenie konfliktov je out-of-scope
- Server vždy wins: strata mobilných dát — neprijateľné
- User resolution: vyžaduje UI — out-of-scope

---

## R-007: Kde v Android appke prebieha výpočet

Analýza Android kódu identifikuje tieto miesta:

| Miesto | Trieda/Metóda | Frekvencia | Server kandidát? |
|--------|--------------|-----------|-----------------|
| Po uložení dňa | `TrackerViewModel.saveCurrent()` → `IndexCalculator.computeDailyIndexGrouped()` | Pri každom toggle/slider | ⚠️ Nie — príliš frequent, offline kritické |
| Týždenný index | `HomeViewModel` → `repository.getWeeklyIndex()` | 1x pri otvorení Home | ✅ Áno — pri zobrazení, nie real-time |
| Adaptácia váh | `TrackerRepository.evaluateAndAdaptWeights()` | 1x týždenne | ✅ Áno — ideálne serverový výpočet |
| Notifikácia worker | `NotificationWorker` → `computeActiveKeys` | 1x denne v noci | ❌ Nie — musí byť offline-capable |
| History/Vector screen | `VectorViewModel`, `HomeViewModel` | Pri navigácii | ✅ Voliteľne |

**Záver — Update-only vs On-display**:

| Stratégia | Výhody | Nevýhody |
|-----------|--------|----------|
| **Update-only** (odporúčaná) | Menej requestov, funguje offline, batéria | Staré dáta na serveri pri dlhom offline |
| On-display | Vždy aktuálne serverové dáta | Request pri každom otvorení = batéria + latencia + offline problém |

**Odporúčanie**: Update-only — po každom `saveCurrent` sa zapíše lokálne; sync so serverom prebieha asynchrónne v pozadí (WorkManager job). Server vypočíta a uloží index, Android si ho stiahne pri ďalšom otvorení Home screenu.

---

## R-008: Android appka — zmeny pre autentifikáciu

Minimálne zmeny potrebné v Android appke (nie súčasť serverového projektu, ale musia byť naplánované):

1. **Settings obrazovka**: nové pole "Email" — povinné pre zapnutie sync
2. **TrackerRepository**: `userId: String?` pole v `UserElementEntity` (už pridané v feature 010)
3. **Sync toggle**: ak email nie je vyplnený → toggle je disabled s tooltipom
4. **Token storage**: `SharedPreferences` (encrypted) pre JWT access + refresh token
5. **Retrofit/Ktor HTTP client**: nová závislosť pre API volania (mimo scope tejto feature)

---

## R-009: Easy-to-Start stratégia

**Makefile targets**:
```
make dev      → pip install + alembic upgrade head + uvicorn --reload
make test     → pytest + behave
make migrate  → alembic upgrade head
make clean    → drop dev SQLite DB
```

**Požiadavky na čistý Linux stroj**:
- Python ≥ 3.11 (kontrola v Makefile)
- pip (štandard)
- Voliteľne: PostgreSQL alebo SQLite (fallback)

**Pre SQLite dev**: `DATABASE_URL=sqlite+aiosqlite:///./dev.db` v `.env` — žiadna externá DB.
