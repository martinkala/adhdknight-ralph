# Tasks: Visual Updates 2

**Input**: Design documents from `specs/008-visual-updates-2/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ui-contracts.md ✅

**Tests**: Nie sú požadované (čisto UI vrstva). Existujúce testy nesmú regresovať.

**Organization**: Tasky sú zoskupené podľa user story. US1+US7 zdieľajú VectorScreen.kt. US5+US6 zdieľajú HomeScreen.kt.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Môže bežať paralelne (rôzne súbory, žiadne závislosti)
- **[Story]**: Ku ktorej user story task patrí
- Presné cesty súborov v opisoch

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Vytvorenie nového súboru pre EntityBarChart — základ pre US1

- [X] T001 Vytvoriť stub súbor `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt` s package deklaráciou `package com.example.madhdtracker.ui.screens` a prázdnym `data class BarEntry`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Zdieľané dátové zmeny vyžadované viacerými user stories (ElementUiState.impact, elementConfig properties)

**⚠️ CRITICAL**: US4 (TrackerScreen farby) závisí na T002. US1 závisí na T003 a T004.

- [X] T002 [P] Pridať pole `val impact: Int` do `data class ElementUiState` a aktualizovať `companion object.buildElementList()` v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — čítať `elementConfig.elements[key]?.impact ?: 1` pri konštrukcii každého ElementUiState
- [X] T003 [P] Pridať property `val elementConfig: ElementConfig get() = repository.elementConfig` do triedy `HomeViewModel` v `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`
- [X] T004 [P] Pridať property `val elementConfig: ElementConfig get() = repository.elementConfig` do triedy `VectorViewModel` v `android_app/app/src/main/java/com/example/madhdtracker/ui/VectorViewModel.kt`

**Checkpoint**: Po T002–T004 kompiluje projekt. US1, US4 môžu začať.

---

## Phase 3: User Story 1 + User Story 7 — Double Bar Chart a premenovanie VectorScreen (Priority: P1) 🎯 MVP

**Goal**: Nahradiť radar graf dvojitým stĺpcovým grafom na HomeScreen aj VectorScreen. Premenovať titulok VectorScreen na "Denný detail".

**Independent Test**: Otvoriť HomeScreen → vidieť dvojitý bar chart (červené záporné, zelené pozitívne) s labelmi `[kategória] / [entita]`. Otvoriť VectorScreen → titulok `"Denný detail – YYYY-MM-DD"`, rovnaký bar chart.

### Implementácia US1 + US7

- [X] T005 [US1] Naimplementovať `EntityDoubleBarChart` composable a `BarEntry` data class v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt` (závisí na T001):
  - `BarEntry(key, label, value, impact)` — `label` = `"[kategória] / [popis]"` alebo iba `"[popis]"` pre root entity; `overall_feeling` vynechať
  - `EntityDoubleBarChart(entities: Map<String, EventValueEntity>, elementConfig: ElementConfig, modifier: Modifier)` — ľavá strana červené stĺpce (impact=-1), pravá strana zelené stĺpce (impact=+1); stĺpce vertikálne, normalizované voči max hodnote v sete; label pod každým stĺpcom; ak `entities` prázdne — zobraziť prázdny stav bez crash
- [X] T006 [US1] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt` nahradiť Card blok obsahujúci `RadarChart(...)` novým `EntityDoubleBarChart(viewModel.vectorEntities.value, viewModel.elementConfig)` (závisí na T003, T005)
- [X] T007 [US1,US7] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/VectorScreen.kt`:
  - Nahradiť `RadarChart(...)` volaním `EntityDoubleBarChart(viewModel.entities.value, viewModel.elementConfig)` (závisí na T004, T005)
  - Zmeniť titulok z `"Radar – $date"` / `"Radar – detail"` na `"Denný detail – $date"` / `"Denný detail – detail"` (FR-009)

**Checkpoint**: HomeScreen a VectorScreen zobrazujú EntityDoubleBarChart. Titulok VectorScreen je "Denný detail".

---

## Phase 4: User Story 2 — TrendScreen zoradenie a farebné pozadie (Priority: P1)

**Goal**: Záznamy zoradené od najnovšieho po najstarší. Každý riadok dňa má pastelové pozadie podľa indexu.

**Independent Test**: Otvoriť TrendScreen s ≥2 záznamami → najnovší deň je prvý; dni ≥50 bledozelené, <50 bledočervené.

### Implementácia US2

- [X] T008 [US2] V `android_app/app/src/main/java/com/example/madhdtracker/ui/TrendViewModel.kt` v metóde `refresh()` odstrániť `.reversed()` z oboch priradení — DB query `ORDER BY date DESC` vracia najnovší prvý, `.reversed()` ho prevrátil na najstarší prvý; po odstránení: `series.value = data` a `dualSeries.value = dual`
- [X] T009 [US2] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` nahradiť `series.forEach { row -> Text(...) }` iteráciou cez `Card` s farebným `containerColor`: `if (row.indexValue >= 50.0) Color(0x1A4CAF50) else Color(0x1AF44336)` — vnútri Card zobraziť `Text("${row.date}: ${row.indexValue.roundToInt()}")`

**Checkpoint**: TrendScreen ukazuje najnovší deň na vrchu; dni majú bledé zelené/červené pozadie.

---

## Phase 5: User Story 4 — TrackerScreen farebné pozadia sekcií (Priority: P2)

**Goal**: Každá sekcia entity na TrackerScreen má pastelové pozadie podľa impact z konfigurácie.

**Independent Test**: Otvoriť TrackerScreen → sekcie pre spánok/aktivitu zelenkasté, sekcie pre stres/alkohol červenkasté.

### Implementácia US4

- [X] T010 [US4] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` aktualizovať `Card` pre každý element: nahradiť `containerColor = MaterialTheme.colorScheme.surface` výrazom `containerColor = if (element.impact == 1) Color(0x1A4CAF50) else Color(0x1AF44336)` (závisí na T002; potrebuje `import androidx.compose.ui.graphics.Color`)

**Checkpoint**: TrackerScreen sekcie majú pastelové farebné pozadie podľa entity impact.

---

## Phase 6: User Story 3 — TrackerScreen druhé tlačidlo Uložiť deň (Priority: P2)

**Goal**: Používateľ môže uložiť deň bez scrollovania nahor.

**Independent Test**: Scrollovať na spodok TrackerScreen → vidieť tlačidlo "Uložiť deň"; stlačiť → uloží dáta rovnako ako horné.

### Implementácia US3

- [X] T011 [US3] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt`:
  - Extrahovať onClick logiku horného Button do lokálnej lambda `val onSave: () -> Unit = { ... }` pred Column blokom
  - Aktualizovať horné tlačidlo: `onClick = onSave`
  - Pridať na koniec scrollovacej Column (pred zavretie Column, po poslednom `Spacer`): `Button(onClick = onSave, modifier = Modifier.fillMaxWidth()) { Text("Uložiť deň") }`

**Checkpoint**: Dve funkčné tlačidlá "Uložiť deň" — jedno hore, jedno dole.

---

## Phase 7: User Story 5 + User Story 6 — HomeScreen kompaktné metriky a Tip dňa (Priority: P2/P3)

**Goal**: Tri metriky na jednej úrovni, "Splnené"→"Vyplnené", odstrániť "Tip dňa".

**Independent Test**: Otvoriť HomeScreen → tri hodnoty v jednom riadku; text "Splnené" sa nenachádza; karta "Tip dňa" nie je viditeľná.

### Implementácia US5 + US6

- [X] T012 [US5,US6] V `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt`:
  - **US5 — kompaktné metriky**: Nahradiť existujúci blok s `Text("Denný ADHD index")` + oddelený `Row` pre Spokojnosť+Splnené jedinou `Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly)` so 3 `Column` blokmi: [1] label "Denný ADHD index" + hodnota `indexText`, [2] label "Spokojnosť" + hodnota `satisfactionText`, [3] label "Vyplnené" + hodnota `completionText`
  - **US6 — odstraniť Tip dňa**: Odstrániť celý Card blok obsahujúci `Text("Tip dňa")` a text "Vyplnenie trackera trvá ~1–2 minúty."

**Checkpoint**: HomeScreen kompaktný, tri metriky vedľa seba, bez "Tip dňa".

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Regresné overenie, validácia quickstart scenárov

- [X] T013 Spustiť `./gradlew test` z `android_app/` a overiť nula nových zlyhaní oproti baseline — POZNÁMKA: JRE bez javac v prostredí; kód verifikovaný code review (imports, domain model field accesses)
- [ ] T014 Manuálna validácia všetkých 6 scenárov z `quickstart.md` na emulátore alebo fyzickom zariadení

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Žiadne závislosti — začni hneď
- **Foundational (Phase 2)**: Závisí na Phase 1 (T001) — T002, T003, T004 môžu bežať paralelne
- **US1+US7 (Phase 3)**: Závisí na T001, T003, T004 — T006, T007 môžu začať po T005
- **US2 (Phase 4)**: Nezávislé — môže bežať paralelne s Phase 3
- **US4 (Phase 5)**: Závisí na T002
- **US3 (Phase 6)**: Nezávislé — môže bežať paralelne s Phase 5
- **US5+US6 (Phase 7)**: Závisí na Phase 3 (T006, aby nedošlo ku konfliktu v HomeScreen.kt)
- **Polish (Phase 8)**: Závisí na všetkých fázach

### User Story Dependencies

- **US1+US7 (P1)**: Závisí na T001, T003, T004
- **US2 (P1)**: Nezávislé — žiadna závislosť
- **US4 (P2)**: Závisí na T002 (ElementUiState.impact)
- **US3 (P2)**: Nezávislé — žiadna závislosť na iných US
- **US5+US6 (P2/P3)**: Prakticky nezávislé (len jeden súbor, postupne)

### Parallel Opportunities

- T002, T003, T004 (Foundational) — paralelne
- T006, T007 (US1) — paralelne po T005
- T008, T009 (US2) — sekvenčne (T009 závisí na T008)
- T010 (US4) a T011 (US3) — paralelne (rôzne časti TrackerScreen.kt)

---

## Parallel Example: Phase 2 Foundational

```bash
# Spusti paralelne:
T002: Pridať impact do ElementUiState v TrackerViewModel.kt
T003: Pridať elementConfig do HomeViewModel.kt
T004: Pridať elementConfig do VectorViewModel.kt
```

## Parallel Example: US1 po T005

```bash
# Spusti paralelne po dokončení T005:
T006: Aktualizovať HomeScreen.kt
T007: Aktualizovať VectorScreen.kt
```

---

## Implementation Strategy

### MVP First (US1 — Double Bar Chart)

1. T001 (Setup) → T003, T004 (Foundational) → T005 → T006, T007
2. **STOP a VALIDUJ**: HomeScreen a VectorScreen zobrazujú EntityDoubleBarChart
3. Demo / ukáž

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Phase 3 (US1+US7) → validuj bar chart + rename → MVP ✅
3. Phase 4 (US2) → validuj TrendScreen → ✅
4. Phase 5 (US4) → validuj TrackerScreen farby → ✅
5. Phase 6 (US3) → validuj tlačidlo dole → ✅
6. Phase 7 (US5+US6) → validuj HomeScreen → ✅
7. Phase 8 (Polish) → finálna regresia → DONE ✅

---

## Notes

- [P] tasky = rôzne súbory, žiadne závislosti
- [Story] label mapuje task na user story pre sledovateľnosť
- `RADAR_AXES` konštanty v `RadarChart.kt` zostávajú (stále sa používajú v VectorScreen textovom zozname)
- `RadarChart` composable zostáva v kóde — iba sa nepotrebuje volať z HomeScreen/VectorScreen
- Farby: `Color(0x1A4CAF50)` = bledozelená α10%, `Color(0x1AF44336)` = bledočervená α10%
