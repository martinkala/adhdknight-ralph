# Specification: food-011 — Import vloženého textu a merge (najnižšia priorita)

## Status: COMPLETE

## Feature: Import TSV/CSV z Google Sheets a JSON (výstup LLM importu) s náhľadom, merge a riešením konfliktov (UC5)

### Overview
Používateľ vloží do textového poľa export z Google Sheets (kopírovanie cez schránku = TSV, súbor = CSV)
alebo JSON vo formáte exportu (food-009, aj výstup LLM importu). Aplikácia ukáže náhľad: čo pribudne,
čo sa preskočí ako duplicita a kde je konflikt. Pri konflikte sa používateľ rozhodne, ktorá hodnota platí.
Všetko sa uloží v jednej transakcii. **Aplikácia neopravuje preklepy** (constitution D8).

### User Stories
- Ako používateľ chcem vložiť niekoľko dní z tabuľky a nemať duplicity s tým, čo už v appke je.
- Ako používateľ chcem rozhodnúť, ktorá hodnota platí, keď sa import a appka líšia.

---

## Functional Requirements

### FR-1: Parser (`services/food_import_parser.py`, čistá funkcia)
- Vstup: text + `format` ∈ `auto|tsv|csv|json`. `auto`: JSON ak začína `{`, TSV ak prvý riadok obsahuje TAB, inak CSV.
- TSV/CSV podporuje **formát C** (`docs/food/import-mapping.md`, sekcia 4):
  - Hlavička sa hľadá podľa názvov (trim, bez ohľadu na veľkosť písmen), varianty `oills|pils|pills`,
    `symptoms 12|symptoms 1`. Neznáme stĺpce sa ignorujú a uvedú v reporte. `pohyb` sa ignoruje.
  - Deň = riadok s dátumom `YYYY-MM-DD` v 1. stĺpci + nasledujúce riadky bez dátumu (1 až N riadkov).
  - Bunky: `split_entries` (čiarka + nový riadok), `parse_quantity`, v jednej bunke `merge_duplicates`.
  - `dig problemy (1-10) s/v`: `a/b` alebo `a,b` → stool, gas (nedelí sa ako záznamy).
  - `presure`: každý `sys/dia` → tlak (validácia D4). `w` → váha. `spanok` → sleep_quality.
  - `oills|pils|pills` → položky liekov/doplnkov (zaradenie cez slovník, FR-3), `+` delí položky.
  - `medical note`, `symptoms*`, `note` → `note` (celá bunka = 1 poznámka).
- JSON: schéma `FoodExport` (food-009).
- Neplatné hodnoty (mimo rozsahu, zlý formát) sa nezahodia potichu: idú do `issues` s dátumom, stĺpcom a hodnotou.
- Prázdne dni (iba dátum) sa preskočia (`skipped_empty_days`). Budúce dátumy → `issues`, deň sa neimportuje.

**Acceptance Criteria (testy s fixtures skopírovanými zo `specs/food-000-input/` do `server/tests/fixtures/food/`):**
- [x] `2026.csv` (TSV): 2026-10-23 má breakfast [ryza], morning_snack [banan, bebe oplatky],
      lunch [ryza 1/2 konzzervy tuniak], afternoon_snack [ryza 1/2 konzzervy tuniak, (jablko, 2)],
      dinner [(toasty, 2), zemiaky jogurt], after_dinner [maly marhulovy kompot, bebe oplatky],
      tlak 125/90, stool 6, gas 3, váha 80.6, sport [bike 30 km], lieky emanera (2), prestarium
- [x] `2026.csv`: 2026-09-21 je v `skipped_empty_days`
- [x] `data_sample.txt` (CSV): 2026-07-10 má breakfast [salamy chleba, sunka, 2 nealko piva→(nealko piva, 2)], stool 4, gas 6
- [x] `data_sample.txt`: 2026-07-06 doplnky zn, mg, omega, fe, D a lieky prestarium, emanera (po klasifikácii)
- [x] Vlastný testovací vstup vo formáte C: bunka `"kolac 2 perniky, "` nevytvorí prázdny záznam; preklep `konzzervy` (z `2026.csv`) ostane nezmenený
- [x] Vlastný testovací vstup vo formáte C s `presure` = `145/02`: hodnota skončí v `issues`, nie v dátach
- [x] Hlavička `2025.csv` alebo `2022.csv` → chyba `unsupported_format_legacy`
- [x] JSON z food-009 exportu → parser vráti tie isté dáta (round-trip test export → import do prázdneho účtu → export = rovnaký JSON okrem `exported_at`)

### FR-2: Merge pravidlá (`services/food_import_merge.py`)
Porovnáva sa s existujúcimi nezmazanými dátami používateľa:
- **Záznamy (zoznamy):** zjednotenie. Duplicita = rovnaká kategória + rovnaký `text_norm` + rovnaké
  množstvo a jednotka → preskočí sa (nie je konflikt). Inak sa pridá na koniec sekcie.
- **Merania:** duplicita = rovnaké hodnoty a rovnaký čas → preskočí sa. Inak sa pridá.
- **Hodnoty dňa (sleep_quality, stool, gas):** existujúca prázdna → doplní sa. Rovnaká → nič.
  **Rozdielna → konflikt** `{date, field, existing, incoming}`.
- Nový deň → vytvorí sa celý.

### FR-3: API
- `POST /api/v1/food/import/preview` `{raw_text, format}` → `{schema_version, days: [{date, status: new|merge,
  add: {...}, duplicates_skipped: n, conflicts: [...]}], needs_classification: [{text, text_norm}],
  issues: [...], skipped_empty_days: [...], unknown_columns: [...], totals}`. Nič neukladá.
- `POST /api/v1/food/import/commit` `{raw_text, format, resolutions: [{date, field, choice: keep|import}],
  default_resolution?: keep|import, classify: {<text_norm>: medication|supplement}}`:
  server znovu parsuje a merguje. Ak existuje konflikt bez rozhodnutia (a bez `default_resolution`) alebo
  neklasifikovaný liek/doplnok → 409 `{"detail": "unresolved", "preview": ...}` a nič sa neuloží.
  Inak uloží všetko v **jednej transakcii** (pri chybe rollback, nič sa neuloží) → 200 so súhrnom.
- Limit vstupu 1 MB (inak 413).

**Acceptance Criteria:**
- [x] API test: import do prázdneho účtu → preview `new`, commit vytvorí dni; druhý commit toho istého → všetko `duplicates_skipped`, 0 nových záznamov
- [x] API test: existujúci deň so stool 3, import stool 5 → konflikt; commit bez rozhodnutia → 409 a nič sa nezmenilo
- [x] API test: `choice=import` → stool 5; `choice=keep` → stool 3; `default_resolution=import` platí pre všetky konflikty
- [x] API test: neklasifikovaný liek → 409; s `classify` → uloží a doplní slovník
- [x] API test: chyba počas ukladania (simulovaná) → rollback, v DB nepribudol žiadny riadok
- [x] API test izolácie: merge porovnáva iba s dátami prihláseného používateľa

### FR-4: UI `/food/import/`
1. Textarea (`data-testid="import-input"`) + výber formátu (auto/TSV/CSV/JSON) + „Náhľad“.
2. Náhľad (`data-testid="import-preview"`): súhrn (nové dni, doplnené dni, pridané záznamy, preskočené
   duplicity, konflikty, problémy), zoznam dní s rozbaľovacím detailom, zoznam `issues` a neznámych stĺpcov.
3. Konflikty (`data-testid="import-conflict"`): pre každý „Ponechať existujúce (3)“ / „Prepísať importom (5)“
   + tlačidlo „Použiť pre všetky“ (`data-testid="apply-to-all"`).
4. Klasifikácia neznámych liekov/doplnkov (rovnaký dialóg ako food-007).
5. „Importovať“ je aktívne až keď je všetko rozhodnuté → výsledok so súhrnom a odkazom na kalendár.
Odkaz vo food navigácii.

**Acceptance Criteria:**
- [x] e2e: vloženie 2 dní z `2026.csv` (TSV) → náhľad → import → dni sú v kalendári so správnou závažnosťou
- [x] e2e: konflikt → „Použiť pre všetky: prepísať“ → import → hodnota z importu
- [x] e2e: opakovaný import tých istých dát nevytvorí duplicitné záznamy

---

## Success Criteria
- Bežný týždenný paste z Google Sheets sa naimportuje do 1 minúty bez duplicít.

## Dependencies
- food-010 (preklady nových textov: doplň `.po` sk/cs pre všetky nové texty importu)

## Assumptions
- Staré formáty A a B (2022–2025) importuje LLM mimo appky do JSON. Appka ich v TSV/CSV podporovať nemusí,
  ale ich hlavičku rozpozná a vráti jasnú chybu `unsupported_format_legacy` s odkazom na mapovací dokument.

---

## Completion Signal

### Implementation Checklist
- [x] Parser TSV/CSV (formát C) + JSON
- [x] Merge + konflikty
- [x] Preview/commit API (1 transakcia)
- [x] UI importu + preklady

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- Parser `services/food_import_parser.py` is pure (the user's "today" is a parameter); medication items of TSV/CSV
  stay unclassified there and the merge (`services/food_import_merge.py`) sorts them by the dictionary + `classify`.
- Duplicates are matched as a multiset: each existing row can absorb one incoming row (two "melon" in the sheet
  and two in the app = 2 skipped). Intensity and notes are not part of the duplicate key.
- `merge_duplicates` runs per cell (as specified); the same item in two rows of one day stays twice.
- Empty JSON days are imported (an exported empty day must round-trip); only empty TSV/CSV days are skipped.
- A paste without the header row (starts with a date) uses the 2026.csv column order and reports `default_header`.
- Legacy detection: header contains `wlk`, `pos`, `str`, `end` or `problemy (1-10) s/v` → 422 `unsupported_format_legacy`.
- Commit re-parses, `ImportUnresolved` → 409 `{"detail": "unresolved", "preview": ...}`; storing uses flush only and
  one `commit` (rollback on any error). Measurements get increasing `created_at` so the input order is kept.
- Preview also accepts `classify` (the UI keeps the chosen kinds when previewing again).
- UI: classification uses the same choice buttons as the food-007 dialog, but inline in the preview form, so all
  decisions are submitted together. "Use for all" copies the last chosen conflict answer to every conflict.

<!-- NR_OF_TRIES: 1 -->
