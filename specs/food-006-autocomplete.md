# Specification: food-006 — Autocomplete (našepkávač)

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
- [ ] API test: 3× „toasty“, 1× „tuniak“ → `q=t` vráti [toasty(3), tuniak(1)]
- [ ] API test: uložené „Ryža“ 2× a „ryza“ 1× → `q=ryz` vráti 1 návrh `Ryža` s count 3
- [ ] API test: `q=tuniak` nájde „smazeny tuniak“ (začiatok slova), `q=niak` ho nenájde
- [ ] API test: skupiny sú oddelené: liek „emanera“ sa neobjaví v `group=food`
- [ ] API test: zmazaný záznam a záznam zo zmazaného dňa sa nepočítajú
- [ ] API test izolácie: texty používateľa B sa používateľovi A nikdy neponúknu (ani pri prázdnom `q`)
- [ ] API test: `q` s `%` alebo `_` sa správa ako literál
- [ ] API test: 1000 záznamov → odpoveď < 300 ms na SQLite (meraný test, toleruj pomalý CI faktorom 3)

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
- [ ] e2e: po predchádzajúcich záznamoch „toasty“ napíš „to“ → v návrhoch je „toasty“; ťuk ho pridá ako záznam
- [ ] e2e: „2 to“ → výber „toasty“ → záznam s množstvom 2
- [ ] e2e: „kafe, to“ → výber „toasty“ doplní text „kafe, toasty“ (nepridá hneď) → Enter pridá 2 záznamy
- [ ] e2e: šípka dole + Enter vyberie prvý návrh
- [ ] e2e: druhý používateľ v inom prehliadačovom kontexte nevidí návrhy prvého

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
- [ ] Suggestions API
- [ ] UI našepkávača (pridávanie aj inline edit)

### Testing Requirements
- [ ] `./scripts/test-food.sh` → exit 0
- [ ] Žiadne JS chyby v konzole počas e2e

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 0 -->
