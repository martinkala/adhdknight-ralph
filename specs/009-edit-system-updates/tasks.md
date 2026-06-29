# Tasks: Unified Entity Input (009-edit-system-updates)

**Input**: `specs/009-edit-system-updates/spec.md` + codebase analysis
**Feature**: Každá entita (okrem `overall_feeling`) dostane on/off switch + podmienený slider.
**No plan.md yet** — tasks generated directly from spec + code review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Možno spustiť paralelne (rôzne súbory, bez závislostí)
- **[Story]**: Ktorej user story sa task týka

---

## Phase 1: Foundational

**Purpose**: Overiť, že žiadna zmena DB schémy ani nové súbory nie sú potrebné.

**Analysis result**: `valueBinary` (0=OFF, 1=ON) a `valueScale` (null=OFF) v `EventValueEntity` sú dostačujúce. Žiadna migrácia DB nie je potrebná.

- [X] T001 Prečítať a potvrdiť existujúcu štruktúru `ElementInputState` a `ElementUiState` v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — overiť, že pole `binary` môže slúžiť ako unified on/off switch pre všetky typy entít

**Checkpoint**: Potvrdené — existujúce polia sú dostačujúce, žiadne nové závislosti nie sú potrebné.

---

## Phase 2: User Story 1 — Jednotný on/off switch pre všetky entity (Priority: P1) 🎯 MVP

**Goal**: Každá entita okrem `overall_feeling` zobrazuje switch; slider sa objaví len keď je switch ON. `overall_feeling` zostáva povinný slider bez switcha.

**Independent Test**: Otvoriť tracker → nájsť "Pracovný stres" (dnes má len slider, bez switcha) → overiť, že teraz má switch → prepnúť OFF → uložiť → zobraziť tracker pre rovnaký dátum → switch zostáva OFF, žiadny slider.

### Implementation for User Story 1

- [X] T002 [US1] Aktualizovať inicializáciu `formStates` v `TrackerViewModel.kt` (metóda `buildElementList` + `formStates` blok): všetky entity okrem `overall_feeling` začínajú s `binary = false, detailEnabled = false, scale = 3`; `overall_feeling` zostáva `detailEnabled = true` (povinný slider)

- [X] T003 [US1] Aktualizovať `loadForDate()` v `TrackerViewModel.kt`: pre non-`overall_feeling` entity nastaviť `state.binary.value = entity.valueBinary == 1 || entity.valueScale != null`; pre entitu bez záznamu (entity == null) nastaviť `state.binary.value = false`

- [X] T004 [US1] Aktualizovať renderovanie entít v `TrackerScreen.kt`: nahradiť podmienku `if (element.hasScale)` podmienkou `if (element.key == "overall_feeling")` — vetva `true` zostáva (povinný slider); vetva `false` zmení na: `Switch(checked = state.binary.value)` + podmienený `Slider` iba keď `state.binary.value == true`; odstrániť "Detail 1–5" Checkbox; pole `detailEnabled` v `ElementInputState` ponechať (stále ho číta `overall_feeling` vetva cez existujúci kód) — pre non-`overall_feeling` vetvu sa `detailEnabled` ďalej nepoužíva a môže byť v budúcnosti odstránené

- [X] T005 [US1] Aktualizovať `onSave` lambda v `TrackerScreen.kt`: pre non-`overall_feeling` entity vypočítať `scale = if (state.binary.value) state.scale.value else null` a `binary = if (state.binary.value) 1 else 0`; pre `overall_feeling` zostáva `binary = if (state.scale.value >= 3) 1 else 0, scale = state.scale.value`

**Checkpoint**: US1 hotová — všetky entity okrem `overall_feeling` majú switch; `overall_feeling` zostáva bez switcha; dáta sa správne ukladajú a obnovujú.

---

## Phase 3: User Story 2 — Graf zobrazuje len aktívne entity (Priority: P2)

**Goal**: Bar chart na Home aj Detail obrazovke zobrazuje iba entity, ktoré sú switched ON (majú aktívnu hodnotu). Prázdna polovica grafu sa zobrazí bez pádu.

**Independent Test**: Vypnúť všetky "Negatívne" entity (stress_work, stress_personal, caffeine, alcohol, Adiction) → uložiť → otvoriť Home → ľavá (červená) polovica grafu je prázdna, aplikácia nepadá.

### Implementation for User Story 2

- [X] T006 [US2] Aktualizovať `buildBarEntries()` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: po existujúcom filtrovaní `key != "overall_feeling"` pridať ďalší filter — zaradiť len entity kde `entities[key]` nie je null A `(entity.valueBinary == 1 || entity.valueScale != null)`; entity bez záznamu alebo s `valueBinary=0` a `valueScale=null` sa vynechajú

- [X] T007 [US2] Aktualizovať `EntityDoubleBarChart` v `EntityBarChart.kt`: nahradiť `if (allEntries.isEmpty()) return` za kontrolu `negEntries.isEmpty()` a `posEntries.isEmpty()` zvlášť; pri prázdnom `negEntries` zobraziť v ľavej časti `Text("–", ...)` alebo `Spacer`; pri prázdnom `posEntries` rovnako v pravej časti — zabrániť pádu pri plne prázdnom grafe

**Checkpoint**: US2 hotová — graf nezobrazuje OFF entity, prázdne skupiny sú zvládané gracefully.

---

## Phase 4: User Story 3 — Vizuálne zvýraznenie vyplnených entít (Priority: P2)

**Goal**: Karta entity v trackeri zobrazuje tmavšie farebné pozadie, keď je entita zapnutá (ON), a svetlé pastelové pozadie keď je vypnutá (OFF). Zmena je okamžitá pri prepínaní switcha.

**Independent Test**: Otvoriť tracker → prepnúť entitu na ON → karta sa vizuálne stmavne (tmavšia zelená/červená) → prepnúť späť na OFF → karta sa vráti na svetlú pastelovu farbu.

### Implementation for User Story 3

- [X] T009 [US3] Aktualizovať výpočet `sectionColor` v `TrackerScreen.kt`: premenná `sectionColor` závisí od `state.binary.value` aj od `element.impact` — pri `binary=true` použiť tmavšiu variantu impaktovej farby (vyššia opacita/sýtosť), pri `binary=false` ponechať súčasnú svetlú pastelovu farbu; pre `overall_feeling` vždy tmavšia farba (vždy "zapnutý")

**Checkpoint**: US3 hotová — farba pozadia karty sa mení reaktívne pri prepínaní switcha, bez uloženia.

---

## Phase 5: Polish & Validation

- [ ] T008 Manuálna validácia na emulátore / zariadení (po dokončení US1, US2 aj US3):
  - Otvoriť tracker → overiť switch pri každej entite okrem `overall_feeling`
  - Prepnúť niekoľko entít OFF → uložiť → reloadovať → stav preserved
  - Zobraziť Home bar chart → OFF entity chýbajú
  - Zobraziť VectorScreen bar chart → OFF entity chýbajú
  - Vypnúť všetky negatívne entity → ľavá polovica grafu prázdna (bez pádu)
  - `overall_feeling` → žiadny switch, povinný slider viditeľný
  - Prepnúť entity ON/OFF → okamžitá zmena farby pozadia karty (tmavšia/svetlejšia)
  - Načítať predtým uložený dátum → entity s hodnotou zobraziť s tmavším pozadím ihneď
  - Overiť, že denný index pre ON entity zostáva konzistentný s hodnotami pred zmenou (FR-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: Bez závislostí — môže začať ihneď
- **Phase 2 (US1)**: Závisí na Phase 1 — T002→T003→T004→T005 sú sekvenčné (rovnaké súbory)
- **Phase 3 (US2)**: Môže začať paralelne s Phase 2 (rôzne súbory — EntityBarChart.kt je nezávislý)
- **Phase 4 (US3)**: Závisí na Phase 2 (T004 musí byť hotový — renderovanie kariet) — rovnaký súbor TrackerScreen.kt
- **Phase 5 (Polish/Validation)**: Závisí na dokončení Phase 2, 3 a 4 — T008 validuje US1 + US2 + US3

### Within Each Phase

- T002 → T003 → T004 → T005 (sekvenčné — TrackerViewModel + TrackerScreen, navzájom závislé zmeny)
- T006 → T007 (sekvenčné — ten istý súbor EntityBarChart.kt)

### Parallel Opportunities

```
# Phase 2 a Phase 3 môžu bežať paralelne:
Task A: T002–T005 (TrackerViewModel.kt + TrackerScreen.kt)
Task B: T006–T007 (EntityBarChart.kt)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Dokončiť Phase 1 (T001)
2. Dokončiť Phase 2 US1 (T002–T005)
3. **STOP and VALIDATE**: Otvoriť tracker, overiť switch pre každú entitu, uložiť a reload
4. Pokračovať s Phase 3 US2

### File Impact Summary

| Súbor | Čo sa mení |
|-------|-----------|
| `ui/TrackerViewModel.kt` | formStates init, loadForDate() switch restore |
| `ui/screens/TrackerScreen.kt` | renderovanie: switch+slider namiesto hasScale-branch; onSave logika |
| `ui/screens/EntityBarChart.kt` | buildBarEntries() filter + empty-state handling |

**Žiadna zmena**: DB schéma, YAML config, ostatné obrazovky, index formula.
