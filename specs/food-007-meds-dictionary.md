# Specification: food-007 — Lieky a doplnky so slovníkom

## Status: COMPLETE

## Feature: Jedno pole „Lieky a doplnky“, automatické zaradenie podľa slovníka používateľa

### Overview
Používateľ píše lieky aj doplnky do jedného poľa („zn, mg, omega, prestarium, emanera“).
Aplikácia ich podľa osobného slovníka zaradí do Liekov alebo Doplnkov. Pri neznámej položke sa raz
spýta a odpoveď si zapamätá (constitution D7).

### User Stories
- Ako používateľ chcem písať lieky a doplnky spolu, ako som bol zvyknutý v tabuľke.
- Ako používateľ chcem odpovedať „liek alebo doplnok“ iba raz pre každú položku.

---

## Functional Requirements

### FR-1: Dictionary API
- `GET /api/v1/food/med-dictionary` → `{schema_version, items: [{text_norm, display_text, kind, usage_count}]}` (abecedne).
- `PUT /api/v1/food/med-dictionary/{text_norm}` `{kind, display_text?}` → 200 (upsert). Zmena `kind`
  **presunie** všetky existujúce záznamy s daným `text_norm` medzi `medication` a `supplement`.
- `DELETE /api/v1/food/med-dictionary/{text_norm}` → 204 (záznamy v dňoch ostanú).
- Pridanie záznamu priamo do kategórie `medication`/`supplement` cez entries API (food-005) zapíše
  položku do slovníka, ak tam ešte nie je.

**Acceptance Criteria:**
- [x] API testy CRUD + presun existujúcich záznamov pri zmene `kind`
- [x] API test: POST entry do `supplement` „zn“ vytvorí slovníkovú položku `zn → supplement`
- [x] API testy izolácie (slovník A nevidí ani nemení B; rovnaký `text_norm` môže mať u A a B iný `kind`)

### FR-2: Spoločný vstup
`POST /api/v1/food/days/{date}/meds` `{text, classify?: {<text_norm>: "medication"|"supplement"}}`:
1. `split_entries`, `parse_quantity`, `merge_duplicates` (rovnako ako food-005). Navyše sa časť
   obsahujúca `+` (napr. `omega+fe+D`) rozdelí podľa `+` na samostatné položky.
2. Položky v slovníku (alebo v `classify`) sa vytvoria v správnej kategórii. Položky z `classify` sa uložia do slovníka.
3. Ak zostane aspoň jedna neznáma položka, **nevytvorí sa nič** a vráti sa 200
   `{schema_version, created: [], needs_classification: [{text, text_norm}]}`. Klient sa spýta a pošle request znova s `classify`.
4. Inak 201 `{schema_version, created: [Entry...], needs_classification: []}`.

**Acceptance Criteria:**
- [x] API test: prázdny slovník, „prestarium, zn“ → `needs_classification` obsahuje obe, nič sa nevytvorilo
- [x] API test: druhý request s `classify` → 201, prestarium v `medication`, zn v `supplement`, slovník doplnený
- [x] API test: tretí request „zn, prestarium, emanera“ → pýta sa iba na emanera
- [x] API test: „omega+fe+D“ → 3 položky
- [x] API test: „emanera, prestarium, emanera“ (všetko známe) → emanera s množstvom 2

### FR-3: UI
- Na obrazovke dňa nahradí samostatné polia Liekov a Doplnkov jedno pole „Lieky a doplnky“
  (`data-testid="add-meds"`) s autocomplete skupiny `meds`. Sekcie Lieky a Doplnky sa zobrazujú
  ďalej oddelene (zoznamy, úprava, ✕ ako food-005).
- Pri `needs_classification` sa zobrazí dialóg (`data-testid="classify-dialog"`): pre každú položku
  dve tlačidlá „Liek“ / „Doplnok“ (`data-testid="classify-medication"`, `"classify-supplement"`).
  Potvrdenie odošle request s `classify`. Zrušenie nič neuloží a ponechá text v poli.
- Pri zázname v sekcii Lieky/Doplnky je akcia „presunúť do Doplnkov/Liekov“ (zmení slovník, FR-1).
- Stránka `/food/settings/meds/` (`data-testid="meds-dictionary"`): zoznam slovníka, prepínač druhu, zmazanie.
  Odkaz z obrazovky dňa (pri sekcii) a z food navigácie.

**Acceptance Criteria:**
- [x] e2e: „prestarium, zn“ → dialóg → Liek / Doplnok → záznamy v správnych sekciách
- [x] e2e: druhý deň „zn, prestarium“ → bez dialógu, priamo uložené
- [x] e2e: na stránke slovníka zmena zn na Liek → zn sa v dňoch zobrazuje v sekcii Lieky

---

## Success Criteria
- Bežné denné lieky a doplnky sa zapíšu jedným riadkom bez akéhokoľvek dialógu.

## Dependencies
- food-006

## Assumptions
- Slovník sa neprednapĺňa. Prvotné hodnoty vzniknú pri LLM importe alebo pri prvom použití.

---

## Completion Signal

### Implementation Checklist
- [x] Dictionary API + presun pri zmene druhu
- [x] `/meds` endpoint s `needs_classification`
- [x] UI spoločného vstupu, dialóg, stránka slovníka

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- Slovník je soft delete (`deleted_at`); PUT zmazanú položku obnoví (unique `user_id + text_norm`).
  `text_norm` v URL sa na serveri znova normalizuje (`PUT /med-dictionary/Prestárium` → `prestarium`), cesta je
  `{text_norm:path}`, takže funguje aj `/` v texte (Django ho kóduje ako `%2F`).
- PUT bez `display_text` pri novej položke použije `text_norm`; pri existujúcej ponechá pôvodný tvar.
- `usage_count` = nezmazané záznamy v Liekoch + Doplnkoch (bez zmazaných dní).
- Presun pri zmene `kind` dáva záznamy na koniec cieľovej sekcie daného dňa.
- POST entry do `medication`/`supplement` pridá do slovníka iba chýbajúcu položku; existujúca si druh ponechá.
- `/meds`: `classify` sa použije iba pre položky, ktoré v slovníku nie sú (známe položky sa riadia slovníkom).
  Kľúče `classify` sa normalizujú.
- `Entry` v API má navyše `text_norm` (kľúč slovníka pre akciu „presunúť“ na webe).
- Web: jedna karta „Lieky a doplnky“ (`section-meds`) obsahuje podsekcie `section-medication` /
  `section-supplement` a pole `add-meds`. Akcia presunu = tlačidlo `entry-move` (⇅). Dialóg má pre každú
  položku Liek/Doplnok a Uložiť (`classify-submit`, aktívne až po výbere všetkých), Zrušiť (`classify-cancel`) alebo Esc.

<!-- NR_OF_TRIES: 1 -->
