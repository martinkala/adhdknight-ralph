# Tasks: Visual Update 03 (011-visual-update-03)

**Input**: `specs/011-visual-update-03/spec.md` + codebase analýza
**Feature**: 8 vizuálnych a UX vylepšení: oprava date bugy na Home, auto-save, category grouping v dual bar charte, pie chart, swipe navigácia, Info obrazovka, ikona domu, user entity bug.
**No plan.md** — tasky generované priamo zo spec.md + code review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Možno spustiť paralelne (rôzne súbory, bez závislostí)
- **[Story]**: Ktorej user story sa task týka

---

## Phase 1: Foundational

**Purpose**: Overiť a doplniť Repository metódy potrebné pre date-scoped načítanie na Home obrazovke.

**Analysis result**: `TrackerRepository` má `getValuesForDate(date)` (pre Tracker), ale `HomeViewModel` používa `getLatestDailyIndex()`, `getLatestSatisfaction()`, atď. bez filtrovania podľa dátumu — to je príčina bugy US1. Takisto je potrebné `getAllEventDates()` pre US5 swipe navigáciu.

- [X] T001 Prečítať `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` a overiť existenciu date-scoped metód: `getIndexForDate(date: String)`, `getSatisfactionForDate(date: String)`, `getSubIndicesForDate(date: String)`, `getCompletionForDate(date: String)` a `getAllEventDates(): List<String>`; chýbajúce metódy pridať do Repository + príslušného DAO v `android_app/app/src/main/java/com/example/madhdtracker/data/`

**Checkpoint**: Repository má všetky potrebné metódy pre date-scoped načítanie Home dát a zoznam existujúcich dátumov.

---

## Phase 2: User Story 1 — Oprava: Home zobrazuje data aktuálneho dňa (Priority: P1) 🎯 MVP

**Goal**: Home vždy kontroluje dátum a zobrazuje dáta iba ak dnes existuje záznam. Ak nie, zobrazí sivý placeholder.

**Independent Test**: Zmeniť systémový dátum na zajtra (alebo vyčistiť DB) → otvoriť Home → musí sa zobraziť placeholder (sivé bary, bez hodnôt), nadpis musí ukazovať dnešný dátum.

### Implementation for User Story 1

- [X] T002 [US1] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`: pridať `displayedDate = mutableStateOf(LocalDate.now())`; zmeniť `refresh()` na `loadForDate(date: LocalDate = LocalDate.now())` ktorá načíta dáta pomocou date-scoped Repository metód (z T001) pre konkrétny dátum; pridať `hasTodayData = mutableStateOf(false)` nastavený na `true` iba ak záznam pre `LocalDate.now()` existuje v DB; `init { loadForDate() }` namiesto `init { refresh() }`

- [X] T003 [US1] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt`: pridať `PlaceholderBarChart` composable — horizontálny Row s 3 sivými Canvas barmi rôznych frakcií (0.30f, 0.60f, 0.45f) na ľavej strane a 3 sivými barmi (0.50f, 0.35f, 0.65f) na pravej strane, farba `Color(0xFFD0D0D0)`, bez popiskov ani hodnôt; zobraziť `PlaceholderBarChart` namiesto `EntityDoubleBarChart` keď `!viewModel.hasTodayData.value`; opraviť `LaunchedEffect(Unit) { viewModel.refresh() }` na `LaunchedEffect(Unit) { viewModel.loadForDate() }`

**Checkpoint**: US1 hotová — Home zobrazuje sivý placeholder keď dnes nie je vyplnené; EntityDoubleBarChart sa zobrazí len keď dnes existuje záznam.

---

## Phase 3: User Story 2 — Auto-ukladanie pri prepnutí aktivity (Priority: P1)

**Goal**: Každá zmena v Trackeri sa uloží okamžite (Switch) alebo po 500ms pauze (Slider). Tlačidlo "Uložiť deň" je odstránené.

**Independent Test**: Otvoriť Tracker → prepnúť Switch entity → bez kliknutia na akékoľvek tlačidlo navigovať na Home → vrátiť sa na Tracker pre rovnaký deň → switch musí zostať zapnutý.

### Implementation for User Story 2

- [X] T004 [US2] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt`: extrahovať logiku z `onSave` lambda v TrackerScreen do verejnej metódy `fun saveCurrent(date: String)` na ViewModel — táto metóda uloží aktuálny stav všetkých formStates bez `onSaved()` callback; zachovať existujúci `saveDay()` pre prípadné iné použitie

- [X] T005 [US2] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt`: pre každý `Switch` entity (`onCheckedChange`) pridať volanie `viewModel.saveCurrent(date)` po zmene stavu; pre každý `Slider` entity pridať `LaunchedEffect(state.scale.value) { delay(500L); viewModel.saveCurrent(date) }` — debounce ukladanie 500ms po poslednej zmene

- [X] T006 [US2] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt`: odstrániť `Button(onClick = onSave) { Text("Uložiť deň") }` z hlavičky TrackerScreen a Row ktorý ho obsahuje; odstrániť `val onSave: () -> Unit = { ... }` lambda (logika je teraz v `viewModel.saveCurrent()`); zjednodušiť `onSaved` callback iba na navigáciu ak je stále potrebná

**Checkpoint**: US2 hotová — žiadne tlačidlo "Uložiť deň"; každý prepnutý switch alebo posun slideru sa automaticky uloží; navigácia preč zo záznamov nestrácanie.

---

## Phase 4: User Story 3 — Dual bar chart: kategórie, váhy, zoskupenie (Priority: P2)

**Goal**: Dual bar chart zoskupuje entity podľa kategórie — entity z rovnakej kategórie sú vedľa seba, protichodné (neg/pos) z tej istej kategórie sú naproti sebe. Vo vnútri každého baru je zobrazená efektívna váha.

**Independent Test**: Vyplniť deň s aspoň 1 neg a 1 pos entitou z tej istej kategórie → otvoriť Home → entity tejto kategórie sú zobrazené naproti sebe na rovnakom riadku; vo vnútri baru je číslo váhy.

### Implementation for User Story 3

- [X] T007 [US3] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: rozšíriť `data class BarEntry` o polia `categoryKey: String?` a `effectiveWeight: Double`; aktualizovať `buildBarEntries()` aby plnil `categoryKey` z `el.parent` (kľúč nadriadenej kategórie) a `effectiveWeight` = aktuálna váha entity z `elementConfig` (keď je dostupná z WeightEntity) krát `radarValue(entity)`, alebo len `value * defaultWeight` — presný výpočet odvodiť z existujúcej `IndexCalculator` logiky

- [X] T008 [US3] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: pridať `data class BarRow(val negEntry: BarEntry?, val posEntry: BarEntry?, val categoryKey: String?)`; pridať funkciu `buildBarRows(negEntries: List<BarEntry>, posEntries: List<BarEntry>): List<BarRow>` — zoskupiť neg a pos záznamy podľa `categoryKey`; pre každú kategóriu spárovať entity postupne (1. neg s 1. pos, 2. neg s prázdnou pos ak chýba protipart, atď.); entity bez kategórie spárovať podľa indexu

- [X] T009 [US3] Prepísať kompozovateľnú funkciu `EntityDoubleBarChart` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: namiesto oddelených `negEntries`/`posEntries` iterovať cez `buildBarRows(negEntries, posEntries)`; každý `BarRow` renderovať ako jeden horizontálny riadok — ľavý Canvas pre `negEntry` (right-anchored), pravý Canvas pre `posEntry` (left-anchored); ak je jedna strana `null`, Canvas zobrazí prázdnu plochu (transparentný bar 0 šírky)

- [X] T010 [US3] Aktualizovať Canvas rendering v `EntityDoubleBarChart` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: pridať text hodnoty efektívnej váhy dovnútra každého baru pomocou `drawIntoCanvas { canvas -> canvas.nativeCanvas.drawText(weightText, x, y, paint) }` — text biely alebo tmavo sfarbený pre kontrast; text centrovaný vertikálne v bare; zobraziť len keď bar je dostatočne dlhý (fraction > 0.2f)

**Checkpoint**: US3 hotová — kategórie sú zoskupené, entity z rovnakej kategórie sú na rovnakých riadkoch, efektívna váha je viditeľná vo vnútri každého baru.

---

## Phase 5: User Story 4 — Koláčový graf na Denný detail (Priority: P2)

**Goal**: VectorScreen zobrazuje koláčový graf s relatívnym zastúpením všetkých vyplnených aktivít.

**Independent Test**: Vyplniť aspoň 3 entity → otvoriť VectorScreen → koláčový graf je viditeľný s farebnými výsečami pre každú entitu.

### Implementation for User Story 4

- [X] T011 [P] [US4] Pridať `PieChart` composable do `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`: `Canvas` s `drawArc(color, startAngle, sweepAngle, useCenter=false, style=Stroke)` pre každú vyplnenú entitu; rozmer výseče proporcionálny k `radarValue(entity)`; farba zelená `Color(0xFF81C784)` pre `impact == 1`, červená `Color(0xFFE57373)` pre `impact == -1`; vynechať `overall_feeling`; pridať centrálny biely/sivý kruh (donut efekt)

- [X] T012 [US4] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/VectorScreen.kt`: pridať `PieChart(entities = entities, elementConfig = viewModel.elementConfig, modifier = Modifier.fillMaxWidth().height(200.dp))` nad existujúci zoznam entít (pred `RADAR_AXES.forEach`); zobraziť len keď `entities.isNotEmpty()`

**Checkpoint**: US4 hotová — koláčový graf je viditeľný na VectorScreen pre každý deň s aspoň 1 entitou.

---

## Phase 6: User Story 5 — Swipe navigácia medzi dňami (Priority: P2)

**Goal**: Home obrazovka umožňuje swipe doľava (predchádzajúci deň) a doprava (nasledujúci deň). Swipe na neexistujúci deň nemá efekt. Nadpis sa mení podľa zobrazeného dňa.

**Independent Test**: Otvoriť Home → swipnúť doľava → zobrazí sa predchádzajúci deň (ak existuje); swipnúť doprava → zobrazí sa ďalší deň; nadpis mení na "Historické dáta – [dátum]".

**Dependency**: Závisí na T002 (US1) — HomeViewModel musí mať `displayedDate` a `loadForDate()` pred pridaním navigácie.

### Implementation for User Story 5

- [X] T013 [US5] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`: pridať `fun loadAvailableDates()` ktorá načíta `getAllEventDates()` z Repository a skonvertuje na `List<LocalDate>`; ak `LocalDate.now()` nie je v zozname, pridať ho na koniec zoznamu pred uložením do `availableDates = mutableStateOf<List<LocalDate>>(emptyList())` — dnešok je vždy platný navigačný stop (zobrazí placeholder keď nemá záznam); pridať `fun loadPreviousDay()` — nájde predchádzajúci dátum v `availableDates` oproti `displayedDate`, ak existuje nastaví `displayedDate` a zavolá `loadForDate()`; pridať `fun loadNextDay()` — analogicky pre nasledujúci deň (blokuje ak nie je); zavolať `loadAvailableDates()` v `init {}`

- [X] T014 [US5] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt`: obalit hlavný `Column` modifier o `Modifier.pointerInput(Unit) { detectHorizontalDragGestures { _, dragAmount -> if (dragAmount < -60f) viewModel.loadPreviousDay() else if (dragAmount > 60f) viewModel.loadNextDay() } }`; zmeniť title text: keď `viewModel.displayedDate.value == LocalDate.now()` → "Dnešný prehľad – $today"; keď historický → "Historické dáta – ${viewModel.displayedDate.value.format(formatter)}"

**Checkpoint**: US5 hotová — swipe doľava/doprava naviguje medzi existujúcimi dňami; nadpis reflektuje zobrazený deň.

---

## Phase 7: User Story 6 — Info obrazovka s váhami entít (Priority: P3)

**Goal**: Nová obrazovka "Info" dostupná z menu zobrazuje zoznam všetkých entít s ich aktuálnymi váhami a popismi.

**Independent Test**: Otvoriť menu → kliknúť Info → zobrazí sa zoznam entít s váhami.

### Implementation for User Story 6

- [X] T015 [US6] Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/InfoScreen.kt`: `LazyColumn` so všetkými entitami z `elementConfig.elements`; každá položka zobrazuje `el.description` (alebo `el.label`), aktuálnu váhu (z `WeightEntity.weightPersonal ?: weightDefault`) a krátky popis (ak dostupný); použiť štýl `MaterialTheme.typography.bodyMedium` pre popis a `MaterialTheme.typography.titleSmall` pre názov; skupinovať podľa `el.parent` kategórie

- [X] T016 [US6] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt`: pridať `const val INFO = "info"` do `AppRoutes`; pridať parameter `repository: TrackerRepository` alebo `infoData: ...` do `AppNavGraph` (podľa toho ako InfoScreen načíta váhy); pridať `composable(AppRoutes.INFO) { InfoScreen(repository) }`

- [X] T017 [US6] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt`: pridať `INFO` do `Screen` enum; pre INFO `NavigationBarItem` nastaviť `label = { Text("Info") }` a `icon = { Text("i") }`; pridať route mapping `Screen.INFO -> AppRoutes.INFO` v `when` bloku

**Checkpoint**: US6 hotová — nová Info položka v menu; InfoScreen zobrazuje entity s váhami.

---

## Phase 8: User Story 7 — Ikona domu v menu (Priority: P3)

**Goal**: Dolné menu zobrazuje ikonu domu pre Home namiesto textu "H".

**Independent Test**: Otvoriť aplikáciu → dolné menu → Home položka má ikonu domu (nie písmeno "H").

### Implementation for User Story 7

- [X] T018 [US7] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt`: pre `Screen.HOME` `NavigationBarItem` zmeniť `icon = { Text("H") }` na `icon = { Icon(Icons.Filled.Home, contentDescription = "Home") }`; pridať import `androidx.compose.material.icons.Icons` a `androidx.compose.material.icons.filled.Home`; ak `material-icons-core` nie je v `android_app/app/build.gradle.kts`, pridať `implementation("androidx.compose.material:material-icons-core")` — zdôvodnenie: štandardná prvostranná Compose knižnica z BOM, nie externá závislosť; žiadne iné ikony nedoplniť v tomto tasku

**Checkpoint**: US7 hotová — Home v menu má ikonu domu.

---

## Phase 9: User Story 8 — Vyšetrovanie: user-defined entity v trackeri (Priority: P3)

**Goal**: Potvrdiť či user-definované entity (pridané cez EntityManagementScreen) sa objavujú v Trackeri. Ak nie, opraviť bug.

**Independent Test**: Pridať novú entitu v EntityManagementScreen → otvoriť Tracker → nová entita je viditeľná s on/off switchom.

### Implementation for User Story 8

- [X] T019 [US8] Prečítať `android_app/app/src/main/java/com/example/madhdtracker/ui/EntityManagementViewModel.kt` a porovnať zdroj dát s `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt`: zistiť či `buildElementList(elementConfig)` v TrackerViewModel zahŕňa user-pridané entity (uložené cez EntityManagementScreen); ak `elementConfig` sa načítava iba raz z assets a nezahŕňa DB záznamy — potvrdiť to je bug

- [X] T020 [US8] Ak T019 potvrdí bug: aktualizovať `TrackerViewModel.kt` a/alebo `TrackerRepository.kt` aby `buildElementList()` mergoval entity z `elementConfig` (YAML/assets) s user-definovanými entitami z DB; zachovať existujúce entity v pôvodnom poradí; user entity zaradiť na koniec zoznamu; zabezpečiť že majú `hasScale`, `impact`, `label` polia nastavené zo záznamu v DB

**Checkpoint**: US8 hotová — user-definované entity sú viditeľné a ovládateľné v Trackeri.

---

## Phase 10: Polish & Validation

- [ ] T021 Manuálna validácia na emulátore / zariadení (zostáva na manuálne overenie) na emulátore / zariadení (po dokončení všetkých US):
  - **US1**: Otvoriť app bez dnešného záznamu → placeholder 3+3 sivé bary; vyplniť Tracker → Home zobrazí skutočné dáta
  - **US2**: Prepnúť switch → navigovať na Home → vrátiť sa → switch ON; posunúť slider → počkať 1s → navigovať preč → vrátiť sa → slider hodnota zachovaná; tlačidlo "Uložiť deň" nie je viditeľné
  - **US3**: Dual bar chart - entity z rovnakej kategórie sú vedľa seba; neg+pos z rovnakej kategórie naproti sebe; číslo váhy viditeľné v bare
  - **US4**: VectorScreen - koláčový graf viditeľný keď sú vyplnené entity; pri prázdnom dni sa nezobrazí
  - **US5**: Swipe doľava → predchádzajúci deň (ak existuje); swipe doprava → ďalší deň; nadpis "Historické dáta –" pre historické dni
  - **US6**: Info v menu → InfoScreen so zoznamom entít a váhami
  - **US7**: Home v menu má ikonu domu
  - **US8**: Pridať entitu cez EntityManagement → otvoriť Tracker → entita viditeľná

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: Bez závislostí — prvý krok
- **Phase 2 (US1)**: Závisí na Phase 1 (Repository metódy musia existovať)
- **Phase 3 (US2)**: Môže bežať paralelne s Phase 2 (rôzne súbory — TrackerViewModel/TrackerScreen vs HomeViewModel/HomeScreen)
- **Phase 4 (US3)**: Závisí na Phase 1; môže bežať paralelne s Phase 2 a 3 (EntityBarChart.kt je nezávislý)
- **Phase 5 (US4)**: Závisí na Phase 4 (PieChart je v tom istom súbore ako EntityBarChart)
- **Phase 6 (US5)**: Závisí na Phase 2 (T002 — HomeViewModel musí mať `displayedDate` a `loadForDate()`)
- **Phase 7 (US6)**: Bez závislostí na predchádzajúcich US; môže bežať po Phase 1
- **Phase 8 (US7)**: Môže bežať paralelne s Phase 7 (ten istý súbor MainActivity.kt — sekvenčné v rámci fázy)
- **Phase 9 (US8)**: Bez závislostí; môže bežať paralelne s inými fázami

### Within Each Phase (Sequential)

- T002 → T003 (HomeViewModel musí byť hotový pred HomeScreen zmenami)
- T004 → T005 → T006 (TrackerViewModel saveCurrent musí existovať pred TrackerScreen zmenami)
- T007 → T008 → T009 → T010 (BarEntry → BarRow → rendering → váhy)
- T011 → T012 (PieChart musí existovať pred VectorScreen integráciou)
- T013 → T014 (HomeViewModel navigácia musí existovať pred HomeScreen swipe)
- T015 → T016 → T017 (InfoScreen → NavGraph → MainActivity)
- T019 → T020 (Investigation pred fix)

### Parallel Opportunities

```
# Phase 2 (US1) a Phase 3 (US2) môžu bežať paralelne:
Task A: T002–T003 (HomeViewModel.kt + HomeScreen.kt)
Task B: T004–T006 (TrackerViewModel.kt + TrackerScreen.kt)

# Phase 4 (US3) môže bežať paralelne s Phase 2+3:
Task C: T007–T010 (EntityBarChart.kt)

# Phase 7 (US6) a Phase 9 (US8) môžu bežať paralelne s fázami 4+5:
Task D: T015–T017 (InfoScreen.kt + NavGraph + MainActivity)
Task E: T019–T020 (EntityManagement investigation)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Dokončiť Phase 1 (T001)
2. Paralelne: Phase 2 US1 (T002–T003) + Phase 3 US2 (T004–T006)
3. **STOP and VALIDATE**: Home zobrazuje placeholder; auto-save funguje; tlačidlo "Uložiť" zmizlo
4. Pokračovať s Phase 4–9

### File Impact Summary

| Súbor | US | Čo sa mení |
|-------|----|-----------|
| `data/TrackerRepository.kt` + DAO | US1, US5 | Nové date-scoped metódy; `getAllEventDates()` |
| `ui/HomeViewModel.kt` | US1, US5 | `displayedDate`, date-scoped loading, navigácia |
| `ui/screens/HomeScreen.kt` | US1, US5 | Placeholder chart, swipe gesture, title update |
| `ui/TrackerViewModel.kt` | US2 | `saveCurrent()` metóda |
| `ui/screens/TrackerScreen.kt` | US2 | Auto-save na switch/slider, remove save button |
| `ui/screens/EntityBarChart.kt` | US3, US4 | BarRow, category pairing, weight text, PieChart |
| `ui/screens/VectorScreen.kt` | US4 | Integrácia PieChart |
| `ui/screens/InfoScreen.kt` | US6 | Nový súbor |
| `ui/navigation/AppNavGraph.kt` | US6 | INFO route |
| `MainActivity.kt` | US6, US7 | INFO BottomNav item, Home icon |
| `ui/TrackerViewModel.kt` | US8 | buildElementList + user entities (ak bug potvrdený) |

**Žiadna zmena**: DB schéma (existujúce polia stačia), YAML config, index formula, notifikačná logika.
