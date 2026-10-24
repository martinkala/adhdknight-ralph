# Specification: food-005 — Záznamy, množstvo a merania

## Status: COMPLETE

## Feature: Pridanie, úprava a mazanie záznamov dňa, váhy a tlaku (UC3, UC4)

### Overview
Jadro aplikácie: rýchle zadávanie. V každej sekcii dňa je pole, Enter pridá záznam(y), čiarka oddeľuje
viac záznamov naraz a množstvo sa rozpozná zo začiatku textu. Záznam sa dá upraviť ťuknutím a zmazať
jedným ťuknutím. Váha a tlak majú vlastné rýchle vstupy. Autocomplete pridá food-006.

### User Stories
- Ako používateľ chcem napísať „2 toasty, kafe“ + Enter a mať 2 záznamy, aby bol zápis čo najrýchlejší.
- Ako používateľ chcem zmeniť množstvo výberom z toho, čo zvyčajne jem.
- Ako používateľ chcem zapísať tlak jedným reťazcom „130/85 72 7:30“.

---

## Functional Requirements

### FR-1: Entries API
- `POST /api/v1/food/days/{date}/entries` `{category, text, quantity?, unit?, intensity?, id?}` → 201
  `{schema_version, created: [Entry...]}`.
  - `text` sa rozdelí cez `split_entries` (pre kategóriu `note` sa NEDELÍ, poznámka je celý text).
  - Ak `quantity` nie je zadané, použije sa `parse_quantity` na každú časť. Potom `merge_duplicates`.
  - Nové záznamy idú na koniec sekcie (`position`). `text_norm` sa vypočíta.
  - `intensity` je povolené iba pre `sport` (inak 422). Neznáma kategória → 422.
  - Deň neexistuje (alebo je zmazaný) → 404. Prázdny text po rozdelení → 422 `empty_text`.
  - `id` (UUID od klienta) je povolené iba pri jednom zázname. Pri duplicite `id` → 409.
- `PATCH /api/v1/food/entries/{id}` `{text?, quantity?, unit?, intensity?, category?, position?}` → 200 Entry.
  Zmena textu prepočíta `text_norm` (bez delenia čiarkou a bez parsovania množstva). `quantity: null` = bez množstva.
  Presun do inej kategórie ho zaradí na koniec cieľovej sekcie.
- `DELETE /api/v1/food/entries/{id}` → 204 (soft delete).
- `GET /api/v1/food/quantities?text=...&category=...` → `{schema_version, options: [{quantity, unit, count}]}`:
  najčastejšie (max. 5) kombinácie množstvo+jednotka pre daný `normalize(text)` v skupine kategórie (D5),
  iba vlastné nezmazané záznamy, zoradené podľa početnosti.

**Acceptance Criteria:**
- [x] API test: `"2 toasty, kafe"` do `breakfast` → 2 záznamy: (toasty, 2) a (kafe, bez množstva)
- [x] API test: `"emanera , prestarium, emanera"` do `medication` → emanera množstvo 2, prestarium
- [x] API test: `note` `"rano prujem, unava"` → 1 záznam s celým textom
- [x] API test: `intensity` pre `lunch` → 422; pre `sport` 1–5 OK, 6 → 422
- [x] API test: PATCH textu prepočíta `text_norm`; presun kategórie funguje
- [x] API test: `quantities` vráti najčastejšie množstvá zoradené podľa počtu a ignoruje zmazané záznamy
- [x] API testy izolácie: B nevie PATCH/DELETE záznam A (404), `quantities` nepočíta záznamy B

### FR-2: Measurements API
- `POST /api/v1/food/days/{date}/weights` `{kg, measured_at?, note?, id?}` → 201 Weight. Validácia D4.
- `POST /api/v1/food/days/{date}/blood-pressures` buď `{raw: "130/85 72 7:30", note?}`, alebo
  `{systolic, diastolic, pulse?, measured_at?, note?}` → 201 BloodPressure. Chyby 422
  `{"detail": "bp_format" | "bp_range"}`.
- `PATCH` a `DELETE` pre `/api/v1/food/weights/{id}` a `/api/v1/food/blood-pressures/{id}`.
- Viac meraní za deň, v `DayDetail` zoradené podľa `measured_at` (bez času na konci), potom podľa `created_at`.

**Acceptance Criteria:**
- [x] API testy: `raw` všetkých formátov z food-003 FR-5, chyby `bp_range`/`bp_format`, váha mimo rozsahu → 422
- [x] API test: 2 merania tlaku v jeden deň sú obe v `DayDetail`
- [x] API testy izolácie pre PATCH/DELETE meraní

### FR-3: UI záznamov na obrazovke dňa
Pre každú kategóriu (D2) okrem `note`:
- Zoznam záznamov: množstvo ako čip (`2×`, `0,5 l`, `200 g`, bez čipu ak chýba) + text + ✕.
  `data-testid="entry"` na riadku, `"entry-qty"`, `"entry-text"`, `"entry-delete"`.
- Pole „Pridať…“ (`data-testid="add-<category>"`): Enter odošle (HTMX), sekcia sa prekreslí,
  pole sa vyprázdni a **ostane vo focuse** (rýchle zadávanie viacerých položiek po sebe).
- ✕ zmaže záznam jedným ťuknutím (bez potvrdenia, constitution D1).
- Ťuk na text → inline úprava (Enter uloží, Esc zruší).
- Ťuk na čip množstva (alebo na „+ množstvo“, ak chýba) → popover (`data-testid="qty-popover"`)
  s najčastejšími množstvami z `/quantities` ako tlačidlá (`data-testid="qty-option"`) + pole na ručné
  zadanie (číslo + jednotka) + „bez množstva“. Výber hneď uloží.
- Šport: navyše výber intenzity 1–5 pri zázname (voliteľné, `data-testid="entry-intensity"`).
- Poznámky (`note`): textarea, Enter + Shift = nový riadok, Enter = uložiť. Každá poznámka je
  samostatný záznam s úpravou a ✕.

**Acceptance Criteria:**
- [x] e2e: do raňajok „2 toasty, kafe“ + Enter → 2 riadky, prvý s čipom `2×`; focus ostal v poli
- [x] e2e: ✕ zmaže záznam bez dialógu a po reloade nie je
- [x] e2e: úprava textu inline + reload → zmena ostala
- [x] e2e: po 3 dňoch s „2 toasty“ a 1 dni s „3 toasty“ ponúkne popover množstvá v poradí 2, 3
- [x] e2e: šport „eBike 60 km“ + intenzita 3 → po reloade ostalo
- [x] e2e (mobil 360 px): pridanie záznamu funguje, ✕ a čip majú cieľovú plochu ≥ 44 × 44 px

### FR-4: UI meraní
- Tlak: jedno pole (`data-testid="add-bp"`, placeholder „130/85 72 7:30“), Enter uloží. Pri prázdnom
  čase a dnešnom dni sa doplní aktuálny lokálny čas. Chyby sa zobrazia pri poli (`data-testid="bp-error"`).
  Zoznam: `130/85 · pulz 72 · 07:30` + ✕ + ťuk = úprava, voliteľná poznámka.
- Váha: pole kg (`data-testid="add-weight"`, `inputmode="decimal"`, čiarka aj bodka), voliteľný čas,
  rovnaký zoznam.

**Acceptance Criteria:**
- [x] e2e: „130/85 72 7:30“ → riadok s 130/85, pulz 72, 07:30
- [x] e2e: „145/02“ → zobrazí `bp-error`, nič sa neuloží
- [x] e2e: váha „80,6“ → uloží 80.6

---

## Success Criteria
- Zápis 5 jedál do jednej sekcie bez použitia myši/ťukania mimo poľa (iba písanie + Enter).

## Dependencies
- food-004

## Assumptions
- Lieky a Doplnky majú v tejto spec každý vlastné pole (kategória explicitne). Spoločný vstup so slovníkom pridá food-007.

---

## Completion Signal

### Implementation Checklist
- [x] Entries API + quantities
- [x] Measurements API
- [x] UI sekcií záznamov (pridanie, inline edit, ✕, popover množstva, intenzita, poznámky)
- [x] UI tlaku a váhy

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0
- [x] Žiadne JS chyby v konzole, žiadne 4xx/5xx v sieti počas e2e (okrem testovaných chýb)

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- Server: `services/food_entries.py` (add / update / delete / quantities), `services/food_measurement_records.py`
  (weights, blood pressures), router `routers/food_entries.py`. Domain errors are `FoodDayError` codes:
  404 `entry_not_found` / `measurement_not_found`, 409 `id_exists`, everything else 422
  (`empty_text`, `text_too_long`, `unknown_category`, `intensity_not_allowed`, `invalid_unit`,
  `unit_without_quantity`, `id_requires_single_entry`, `bp_format`, `bp_range`, `weight_range`, `time_format`).
- `split_entries` no longer splits a decimal comma between two digits (`0,5 l kofoly` stays one entry,
  constitution D6 has priority over a plain comma split).
- Explicit `quantity` in POST is used for every part as is (no parsing). `unit: "ks"` is stored as no unit.
  `unit` without `quantity` is 422. Moving an entry out of `sport` clears its intensity.
- Notes keep line breaks (each line trimmed, empty lines dropped) and are not quantity-parsed.
- "Current time when the time is empty on today's day" is done on the server: `fill_time: true` in POST
  weights / blood-pressures (the web sends it for blood pressure). Android can use the same flag.
- `quantities` ties (same count) are ordered by the most recent use.
- Web: HTMX partials `_entries.html`, `_bp.html`, `_weight.html`, `_qty_popover.html`; a failed save returns
  the list with an error and the `X-Food-Error` header (HTTP 200, so no 4xx in the network log) and
  `static/js/food_entries.js` puts the typed text back. Quick-add fields are cleared as soon as the
  request is sent, so typing can continue immediately.
- Quantity chip uses the localized decimal separator (`0,5 l` in sk once food-010 activates the language).

<!-- NR_OF_TRIES: 1 -->
