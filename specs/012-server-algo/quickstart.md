# Quickstart & Validation Guide: Backend Weight Vector Server

**Date**: 2026-06-30 | **Feature**: 012-server-algo

---

## Prerekvizity

- Python ≥ 3.11 (`python3 --version`)
- pip
- git
- Voliteľne: PostgreSQL 14+ (inak SQLite automaticky)

---

## Inštalácia a spustenie

```bash
cd server/
cp .env.example .env          # SQLite dev config prednastavený
make dev                      # install deps + migrate DB + spustiť server
```

Server beží na `http://localhost:8000`.

Swagger UI: `http://localhost:8000/docs`

Health check: `curl http://localhost:8000/api/v1/health`

---

## Scenáre validácie (SC-*)

### SC-001: Spustenie za < 5 minút (FR-005)

```bash
time make dev
```
Očakávaný výsledok: server beží, health check vráti `{"status": "ok"}`, elapsed < 5 min.

---

### SC-002: Výpočet identický s Android appkou (FR-001)

Testovací fixture pre 1 deň s default váhami:

```bash
curl -X POST http://localhost:8000/api/v1/compute/daily \
  -H "Content-Type: application/json" \
  -d @tests/bdd/fixtures/1_day.yaml.json
```

Alebo cez BDD:
```bash
cd server/
make test-bdd FEATURE=index_calculation
```

Očakávaný výsledok: `index_value` zodpovedá ručnému výpočtu podľa vzorca:
`Index = 100 × Σ(w_i × e_i) / Σ(w_i)`

Pre fixture `1_day.yaml` s `sleep=1 (scale=4), overall_feeling=1 (scale=5)`:
- `e_sleep = (4-1)/4 = 0.75`, contribution = `15.0 × 0.75 = 11.25`
- `e_overall = (5-1)/4 = 1.0`, contribution = `13.0 × 1.0 = 13.0`
- Len tieto 2 aktívne: `Index = 100 × 24.25 / 28.0 = 86.61`

---

### SC-003: BDD suita — 10+ scenárov (FR-004)

```bash
make test-bdd
```

Očakávaný výsledok: ≥ 10 scenárov, 0 failov, 0 externých sieťových volaní.

```
10 features passed, 0 failed, 0 skipped
42 scenarios passed, 0 failed, 0 skipped
```

---

### SC-004: Batch sync 30 dní < 10 sekúnd (FR-010)

```bash
# Registruj testovacie konto
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Spusti batch sync test
cd server/
make test-sync-perf
```

Očakávaný výsledok: `elapsed < 10.0s` v test output.

---

### SC-005: Backward compatibility (FR-012)

```bash
make test-compat
```

Test pošle response z v1.0 klientovi, pridá nové pole do schémy a overí, že klient nevyhodí chybu.

---

### SC-006: Conflict resolution (FR-010)

```bash
make test-bdd FEATURE=sync_offline
```

Scenár "mobile wins": mobile timestamp je novší → server prepíše. Scenár "server wins": server timestamp je novší → mobile dáta ignorované. Obidva scenáre vracajú správny `resolution` v odpovedi.

---

### SC-007: Nový používateľ — prázdne dáta (FR-014)

```bash
curl -X POST http://localhost:8000/api/v1/compute/range \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","entity_config":{},"days":[]}'
```

Očakávaný výsledok: `200 OK`, `{"results": [], "summary": {"days_requested": 0, ...}}` — žiadna chyba.

---

## Spustenie všetkých testov

```bash
make test          # pytest unit + API testy
make test-bdd      # behave BDD testy
make test-all      # oboje + coverage report
```

---

## YAML Fixture štruktúra (human-editable)

Súbory v `tests/bdd/fixtures/` — editovateľné bez znalosti Pythonu:

```yaml
# tests/bdd/fixtures/1_day.yaml
description: "Single day - sleep and overall feeling filled"
entity_config:
  sleep:
    weight: 15.0
    impact: 1
    parent: null
    scale: true
  overall_feeling:
    weight: 13.0
    impact: 1
    parent: null
    scale: true

days:
  - date: "2026-06-30"
    values:
      - element_key: sleep
        value_binary: 1
        value_scale: 4
      - element_key: overall_feeling
        value_binary: 1
        value_scale: 5
    active_keys: [sleep, overall_feeling]

expected:
  index_value: 86.61
  tolerance: 0.01
  status: computed
```

---

## Referenčné dokumenty

- API contracts: [contracts/compute.md](contracts/compute.md), [contracts/auth.md](contracts/auth.md), [contracts/sync.md](contracts/sync.md), [contracts/migrate.md](contracts/migrate.md)
- Data model: [data-model.md](data-model.md)
- Research & decisions: [research.md](research.md)
