# Specification: food-006 — Autocomplete (našepkávač)

## Status: COMPLETE

## Feature: Návrhy z vlastnej histórie podľa početnosti, bez ohľadu na diakritiku

### Overview
Pri písaní do poľa jedla, liekov/doplnkov alebo športu sa ponúknu texty, ktoré používateľ už zadal,
zoradené podľa toho, ako často ich zadáva. Pravidlá sú v constitution D5. Zdroj sú výhradne dáta
prihláseného používateľa.

### User Stories
- Ako používateľ chcem po napísaní „tu“ dostať „ryža 1/2 konzervy tuniak“ a „tuniak“, aby som nemusel písať celý text.
- Ako používateľ chcem, aby „ryza“ našlo aj „ryža“ a „Ryza“.

---

## Functional Requirements

### FR-1: Suggestions API
`GET /api/v1/food/suggestions?group=food|meds|sport&q=<text>&limit=10` → `{schema_version, suggestions: [{text, count}]}`
- `q` sa normalizuje (`normalize`). Zhoda: `text_norm` začína na `q` **alebo** niektoré slovo
  v `text_norm` začína na `q` (implementácia: `text_norm LIKE 'q%' OR text_norm LIKE '% q%'`, escapované `%`/`_`).
- Iba nezmazané záznamy prihláseného používateľa v nezmazaných dňoch, iba kategórie skupiny (D2).
- Zoskupenie podľa `text_norm`. Poradie: počet výskytov zostupne, potom posledné použitie zostupne.
  `text` = najčastejší pôvodný tvar v skupine (pri zhode najnovší).
- Prázdne `q` → najčastejšie položky skupiny (použije sa po focuse prázdneho poľa).
- `limit` 1–20, default 10. Neznáma `group` → 422. Skupina `note` neexistuje.
- Výkon: index (`user_id`,`category`,`text_norm`) z food-003. Dotaz nesmie načítať všetky záznamy do Pythonu.

**Acceptance Criteria:**
- [x] API test: 3× „toasty“, 1× „tuniak“ → `q=t` vráti [toasty(3), tuniak(1)]
- [x] API test: uložené „Ryža“ 2× a „ryza“ 1× → `q=ryz` vráti 1 návrh `Ryža` s count 3
- [x] API test: `q=tuniak` nájde „smazeny tuniak“ (začiatok slova), `q=niak` ho nenájde
- [x] API test: skupiny sú oddelené: liek „emanera“ sa neobjaví v `group=food`
- [x] API test: zmazaný záznam a záznam zo zmazaného dňa sa nepočítajú
- [x] API test izolácie: texty používateľa B sa používateľovi A nikdy neponúknu (ani pri prázdnom `q`)
- [x] API test: `q` s `%` alebo `_` sa správa ako literál
- [x] API test: 1000 záznamov → odpoveď < 300 ms na SQLite (meraný test, toleruj pomalý CI faktorom 3)

### FR-2: UI našepkávača
- Na všetkých poliach `add-<category>` okrem `note` (food, meds, sport), aj pri inline úprave textu.
- Po napísaní (debounce 150 ms) alebo pri focuse prázdneho poľa sa pod poľom zobrazí zoznam
  (`data-testid="suggestions"`, položky `data-testid="suggestion"`), max. 8 položiek na mobile.
- Hľadá sa podľa **poslednej časti** za čiarkou (pri „2 toasty, ka“ hľadá „ka“) a bez úvodného
  množstva (pri „2 to“ hľadá „to“).
- Ťuk/klik na návrh alebo šípky + Enter: nahradí poslednú časť vstupu návrhom (množstvo napísané
  pred ním ostane) a **hneď pridá** záznam(y), ak je vstup jediná položka. Inak iba doplní text a pokračuje sa v písaní.
- Esc alebo klik mimo zoznam zatvorí. Enter bez vybraného návrhu = bežné pridanie (food-005).
- Prístupnosť: `role="listbox"`, `aria-activedescendant`.

**Acceptance Criteria:**
- [x] e2e: po predchádzajúcich záznamoch „toasty“ napíš „to“ → v návrhoch je „toasty“; ťuk ho pridá ako záznam
- [x] e2e: „2 to“ → výber „toasty“ → záznam s množstvom 2
- [x] e2e: „kafe, to“ → výber „toasty“ doplní text „kafe, toasty“ (nepridá hneď) → Enter pridá 2 záznamy
- [x] e2e: šípka dole + Enter vyberie prvý návrh
- [x] e2e: druhý používateľ v inom prehliadačovom kontexte nevidí návrhy prvého

---

## Success Criteria
- Bežné jedlo sa zapíše 2–3 znakmi + 1 ťuknutím.

## Dependencies
- food-005

## Assumptions
- Návrhy berú do úvahy celú históriu, aj importované dni.

---

## Completion Signal

### Implementation Checklist
- [x] Suggestions API
- [x] UI našepkávača (pridávanie aj inline edit)

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0
- [x] Žiadne JS chyby v konzole počas e2e

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- Server: `services/food_suggestions.py`, endpoint in `routers/food_entries.py`. Unknown group → 422
  `unknown_group`. Two SQL queries: top `text_norm` groups (count, then last use = latest day date, then
  latest `created_at`), then the spellings of at most `limit` groups to pick the most used one. Entries are
  joined with their day so a deleted day never contributes, even if an entry were left undeleted.
- LIKE patterns escape `\`, `%`, `_` with `ESCAPE '\'` (works on SQLite and PostgreSQL).
- Web: `/food/suggestions/` is a thin JSON proxy (unknown group or API error → empty list, HTTP 200).
  `static/js/food_suggest.js` handles debounce, listbox, keyboard and choice. Inputs carry
  `data-suggest="<group>"`; inline edit inputs also `data-suggest-whole` (whole text is searched, choice saves).
- Max. 8 suggestions under 600 px width (the food CSS breakpoint), 10 otherwise.
- Esc with an open list only closes the list (inline edit stays open); a second Esc cancels the edit.
- The leading quantity and the comma split in JS mirror the server's `parse_quantity` / `split_entries` regexes.

<!-- NR_OF_TRIES: 1 -->
