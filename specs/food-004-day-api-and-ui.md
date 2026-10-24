# Specification: food-004 — Deň: API a obrazovka dňa

## Status: COMPLETE

## Feature: Vytvorenie, zobrazenie, hodnoty a mazanie dňa (UC2, časť UC4)

### Overview
Používateľ si vytvorí deň (predvolene dnešný), otvorí jeho detail a zadá hodnoty dňa (spánok,
stolica/vetry). Deň vie zmazať po dvoch potvrdeniach. Obrazovka dňa je kostra, do ktorej food-005
doplní záznamy a merania.

### User Stories
- Ako používateľ chcem jedným ťuknutím otvoriť dnešný deň, aby som mohol hneď zapisovať.
- Ako používateľ chcem pridať aj starší deň, ale nie budúci.
- Ako používateľ chcem, aby sa deň nedal zmazať omylom.

---

## Functional Requirements

### FR-1: Day API (`routers/food_days.py`, `services/food_days.py`)
Všetko pod `/api/v1/food`, vyžaduje auth, filtrované podľa používateľa (constitution A1).
- `GET /today` → `{schema_version, date, exists}` (dnes podľa časovej zóny používateľa).
- `POST /days` `{date?, id?}` (bez `date` = dnes) → 201 + `DayDetail`.
  Budúci dátum → 422 `{"detail": "future_date"}`. Neplatný formát → 422. Existujúci nezmazaný → 409
  `{"detail": "day_exists"}`. Soft-zmazaný → obnoví sa prázdny (staré záznamy ostanú zmazané) → 201.
- `GET /days/{date}` → `DayDetail`, neexistujúci/zmazaný → 404.
- `PATCH /days/{date}` `{sleep_quality?, stool?, gas?}` (null = vymazať hodnotu, mimo rozsahu → 422) → `DayDetail`.
- `DELETE /days/{date}` → 204 (soft delete dňa aj všetkých jeho záznamov a meraní).
- `DayDetail` (schéma v `schemas/food.py`, použijú ju ďalšie specs):
  `{schema_version, id, date, sleep_quality, stool, gas, updated_at,
    entries: {<category>: [Entry...]} (všetky kategórie z D2, aj prázdne),
    weights: [Weight...], blood_pressures: [BloodPressure...]}`.
  `Entry = {id, category, text, quantity, unit, intensity, position, updated_at}`.

**Acceptance Criteria:**
- [x] API testy pre všetky stavové kódy vyššie (201, 409 `day_exists`, 422 `future_date`, 404, 204)
- [x] API test: obnova zmazaného dňa vráti prázdny deň
- [x] API test izolácie: používateľ B dostane 404 na GET/PATCH/DELETE dňa používateľa A a A môže vytvoriť ten istý dátum nezávisle od B
- [x] API test: `GET /today` s podvrhnutým časom (dependency override hodín) vráti dátum podľa `Europe/Bratislava`
- [x] OpenAPI obsahuje endpointy a schému `DayDetail`

### FR-2: Food domovská stránka a nový deň (Django)
- `/food/` (dočasne, kým food-008 nepridá kalendár): veľké tlačidlo „Dnes“ (`data-testid="open-today"`).
  Ak dnešný deň existuje, otvorí ho, inak ho vytvorí a otvorí. Pod ním formulár „Pridať deň“
  (`data-testid="new-day-form"`) s `<input type="date">` (default dnes, `max` = dnes).
- Chyba `day_exists` → hláška „Deň už existuje“ (`data-testid="error-day-exists"`) + odkaz na existujúci deň.
- Chyba `future_date` → hláška (`data-testid="error-future-date"`).

**Acceptance Criteria:**
- [x] e2e: „Dnes“ na prázdnom účte vytvorí a otvorí dnešný deň; druhé ťuknutie otvorí ten istý deň (nevznikne duplicita)
- [x] e2e: pridanie existujúceho dátumu zobrazí `error-day-exists`
- [x] Django test: budúci dátum (obídená klientska validácia) → `error-future-date`

### FR-3: Obrazovka dňa (Django) `/food/day/<YYYY-MM-DD>/`
- Hlavička: dátum (deň v týždni), šípky na predchádzajúci/nasledujúci existujúci deň (`data-testid="prev-day"`, `"next-day"`).
- Sekcie v poradí: Raňajky, Desiata, Obed, Olovrant, Večera, Po večeri, Nezaradené, Lieky, Doplnky,
  Tlak, Váha, Stolica/vetry, Spánok, Šport, Poznámky. Každá sekcia má `data-testid="section-<category>"`
  (tlak `section-bp`, váha `section-weight`, stolica/vetry `section-digestion`, spánok `section-sleep`).
  V tejto spec sekcie záznamov iba zobrazujú obsah (pridávanie je vo food-005).
- Spánok: 3 tlačidlá 1/2/3 (zlý/priemer/ok), stolica a vetry: výber 1–10 (tlačidlá alebo select vhodný
  na mobil). Zmena sa ihneď uloží cez HTMX `PATCH` (autosave), bez tlačidla Uložiť. Opätovné ťuknutie na
  zvolenú hodnotu ju vymaže. Indikátor uloženia (`data-testid="save-status"`).
- Neexistujúci deň → 404 stránka s tlačidlom „Vytvoriť tento deň“ (ak nie je budúci).

**Acceptance Criteria:**
- [x] e2e: nastavenie spánku 2, stolica 4, vetry 6 → reload → hodnoty ostali
- [x] e2e: opätovné ťuknutie na spánok 2 hodnotu vymaže
- [x] e2e (mobil 360 px): bez horizontálneho scrollu, všetky tlačidlá hodnôt majú výšku ≥ 44 px
- [x] Django test: neexistujúci deň → 404 s tlačidlom vytvorenia

### FR-4: Mazanie dňa (2 potvrdenia)
- Tlačidlo „Zmazať deň“ (`data-testid="delete-day"`) dole na obrazovke dňa.
- 1. potvrdenie: dialóg „Naozaj zmazať deň DD. MM. YYYY so všetkými záznamami?“ (`data-testid="delete-day-confirm-1"`).
- 2. potvrdenie: používateľ musí prepísať dátum dňa (`YYYY-MM-DD`) do poľa (`data-testid="delete-day-confirm-input"`).
  Tlačidlo potvrdenia je aktívne až pri presnej zhode. Kontrola zhody prebehne aj na serveri (Django view).
- Po zmazaní redirect na `/food/` s hláškou.

**Acceptance Criteria:**
- [x] e2e: zrušenie v 1. alebo 2. kroku deň nezmaže
- [x] e2e: nesprávny dátum v 2. kroku → tlačidlo neaktívne
- [x] e2e: správny postup deň zmaže a deň už nie je dostupný (404)
- [x] Django test: POST na zmazanie bez zhodného potvrdzovacieho dátumu → deň sa nezmaže

---

## Success Criteria
- Od otvorenia konzoly po dnešný deň: 1 ťuknutie.

## Dependencies
- food-003

## Assumptions
- Prechod na predchádzajúci/nasledujúci deň preskakuje dni, ktoré neexistujú.

## Implementation notes
- `DayDetail` má navyše `prev_date` / `next_date` (najbližší existujúci nezmazaný deň používateľa) pre šípky
  v hlavičke; Android ich môže použiť tiež.
- Hodiny sú FastAPI dependency `app.dependencies.get_now` (testy ju prepíšu). Neplatný formát dátumu v ceste → 422.
- `POST /days` s `id` od klienta, ktoré už existuje (aj u iného používateľa) → 409 `id_exists`. Pri obnove
  zmazaného dňa sa `id` ignoruje a deň si nechá pôvodné `id`. Obnova vymaže hodnoty dňa.
- Merania v `DayDetail` sú už teraz zoradené podľa `measured_at` (bez času na konci), potom `created_at` (food-005).
- „Dnes“ je POST formulár `/food/today/` (otvorí alebo vytvorí deň, CSRF), nie GET odkaz.
- Autosave: HTMX `hx-patch` na Django `/food/day/<date>/values/`, ktorý volá API `PATCH` a vráti partial
  `_day_values.html` (stolica/vetry + spánok sú v poradí sekcií vedľa seba, preto jeden partial). Tlačidlá majú
  `data-testid` `sleep-N`, `stool-N`, `gas-N` a `aria-pressed`.
- UI texty sú `{% translate %}` s anglickými msgid (rovnako ako food-001). Kým food-010 nepridá `.po`, UI je po anglicky.
- Mazanie: 2 `<dialog>` (`delete-day-confirm-1`, `delete-day-confirm-2`), Django view overí zhodu dátumu znova.

---

## Completion Signal

### Implementation Checklist
- [x] Day API + schémy
- [x] `/food/` (Dnes + nový deň)
- [x] Obrazovka dňa so sekciami a autosave hodnôt dňa
- [x] Mazanie dňa v 2 krokoch

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0
- [x] Žiadne JS chyby v konzole na obrazovke dňa

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 1 -->
