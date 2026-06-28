# Tasks: Visual UI Updates – Home, Trend, Menu & Tracker

**Input**: Design documents from `specs/006-visual-updates-1/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Nie sú súčasťou tejto feature (UI testy sú mimo MVP scope). Validácia prebieha ručne podľa `quickstart.md`.

**Organization**: Tasky sú zoskupené podľa user story. Fáza Foundational odblokuje US2; US1, US3 a US4 sú nezávislé.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Dá sa spraviť paralelne (rôzne súbory, žiadne závislosti)
- **[Story]**: US1–US4 mapuje na user stories zo spec.md

---

## Phase 1: Foundational – Routing & ViewModel (Blocking pre US2)

**Purpose**: Pridanie VECTOR_DATE route a VectorViewModel.loadForDate – tieto zmeny blokujú US2 (Trend → Vector navigácia). US1, US3, US4 môžu začať bez tejto fázy.

**⚠️ CRITICAL pre US2**: US2 nemôže začať, kým nie je táto fáza hotová.

- [x] T001 Pridať `AppRoutes.VECTOR_DATE = "vector/{date}"` konštantu a `fun vectorForDate(date: String): String` helper do `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt`
- [x] T002 [P] Rozšíriť `VectorViewModel` – pridať `val loadedDate = mutableStateOf<String?>(null)` a metódu `fun loadForDate(date: String)` volajúcu `repository.getValuesForDate(date)` v `android_app/app/src/main/java/com/example/madhdtracker/ui/VectorViewModel.kt`
- [x] T003 Pridať `composable(AppRoutes.VECTOR_DATE)` blok do `AppNavGraph` s `navArgument("date")` a `LaunchedEffect(date) { vectorViewModel.loadForDate(date) }` v `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt` (závisí od T001, T002)

**Checkpoint**: VECTOR_DATE route je funkčný, VectorViewModel.loadForDate existuje → US2 môže začať

---

## Phase 2: User Story 1 – Home: dátum, swap sekcií, shortcut tlačidlo (Priority: P1) 🎯 MVP

**Goal**: Oprava dátumu, vizuálna hierarchia (pozitívne/negatívne prominentnejšie), skratkový prístup na tracker

**Independent Test**: Otvoriť Home tab → vidieť dátum v hlavičke, Pozitívne/Negatívne navrchu s veľkým fontom, ADHD index pod ním s malým fontom, tlačidlo "Upraviť denný záznam" otvorí Tracker na jedno kliknutie.

### Implementácia US1

- [x] T004 [US1] Pridať `val today = remember { LocalDate.now().format(DateTimeFormatter.ofPattern("d. M. yyyy")) }` a zmeniť `Text("Dnešný prehľad")` na `Text("Dnešný prehľad – $today")` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt`
- [x] T005 [US1] Preusporiadať Card content v `HomeScreen.kt` – sekcia Pozitívne/Negatívne sa presunie na začiatok Column (pred ADHD index), ADHD index sa presunie pod ňu; zmeniť `positiveText`/`negativeText` TextStyle na `displaySmall`, `indexText` TextStyle na `titleMedium` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt` (závisí od T004)
- [x] T006 [US1] Pridať `onEditClick: () -> Unit` parameter do `HomeScreen` signatúry a pridať `Button(onClick = onEditClick) { Text("Upraviť denný záznam") }` do `Row` napravo od sekcie Pozitívne/Negatívne v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt` (závisí od T005)
- [x] T007 [US1] Aktualizovať `composable(AppRoutes.HOME)` volanie v `AppNavGraph.kt` – pridať `onEditClick = { navController.navigate(AppRoutes.TRACKER) }` parameter pre `HomeScreen` v `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt`

**Checkpoint**: US1 hotová – Home stránka zobrazuje dátum, správne fonty+poradie, shortcut button funguje

---

## Phase 3: User Story 2 – Trend: popisky dní a klikateľné dni (Priority: P2)

**Goal**: Stĺpcový graf má popisky dní, kliknutie na deň otvára Vector stránku pre daný deň

**Independent Test**: Otvoriť Trend → vidieť skrátený dátum pod každým stĺpcom → kliknúť na stĺpec → otvoriť Vector stránku s nadpisom daného dňa → Back vráti na Trend.

**⚠️**: Závisí od dokončenia Phase 1 (T001–T003)

### Implementácia US2

- [x] T008 [US2] Aktualizovať `VectorScreen.kt` – pridať `date: String? = null` parameter, zmeniť `LaunchedEffect` logiku (ak `date != null` → `viewModel.loadForDate(date)`, inak → `viewModel.refresh()`), aktualizovať nadpis na `"Radar – $date"` ak date nie je null v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/VectorScreen.kt`
- [x] T009 [US2] Pridať `onDayClick: (String) -> Unit` parameter do `TrendScreen` a prúdat ho do `DualBarChart(dualSeries, onDayClick)` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` (závisí od T008)
- [x] T010 [US2] Refaktorovať `DualBarChart` v `TrendScreen.kt` – wrapping Canvas do `Column`, pridať `Row(modifier = Modifier.fillMaxWidth())` pod Canvas s `items.size` kusmi `Text` (každý `Modifier.weight(1f)`, `textAlign = TextAlign.Center`) zobrazujúcimi skrátený dátum `LocalDate.parse(date).format(DateTimeFormatter.ofPattern("EE\nd.M", Locale("sk")))` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` (závisí od T009)
- [x] T011 [US2] Pridať `Modifier.pointerInput(items)` s `detectTapGestures { offset -> val idx = (offset.x / (size.width / items.size)).toInt().coerceIn(0, items.lastIndex); onDayClick(items[idx].date) }` na Canvas v `DualBarChart` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` (závisí od T010, vyžaduje import `androidx.compose.foundation.gestures.detectTapGestures`)
- [x] T012 [US2] Aktualizovať `composable(AppRoutes.TREND)` v `AppNavGraph.kt` – pridať `onDayClick = { date -> navController.navigate(AppRoutes.vectorForDate(date)) }` parameter pre `TrendScreen` v `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt`

**Checkpoint**: US2 hotová – Trend zobrazuje popisky dní, kliknutie otvára správny vector detail

---

## Phase 4: User Story 3 – Menu: odstránenie Vector (Priority: P3)

**Goal**: NavigationBar neobsahuje položku Vector; Vector stránka zostáva dostupná cez Trend

**Independent Test**: Otvoriť aplikáciu → NavigationBar má 4 položky bez "Vector" → cez Trend je Vector stránka stále dostupná.

**Note**: Táto fáza je plne nezávislá a môže byť vykonaná kedykoľvek (aj pred Foundational).

### Implementácia US3

- [x] T013 [US3] Odstrániť `VECTOR` z `Screen` enum v `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt` (enum ostane: `HOME, TRACKER, TREND, SETTINGS`)

**Checkpoint**: US3 hotová – menu má 4 položky, Vector nie je v NavigationBar

---

## Phase 5: User Story 4 – Denný tracker: presun tlačidla Uložiť (Priority: P4)

**Goal**: Tlačidlo "Uložiť deň" je viditeľné napravo od nadpisu bez scrollovania

**Independent Test**: Otvoriť Tracker tab → vidieť tlačidlo "Uložiť deň" v hornej časti bez scrollovania → stlačiť → záznam sa uloží rovnako ako predtým.

**Note**: Táto fáza je plne nezávislá od všetkých ostatných.

### Implementácia US4

- [x] T014 [US4] Nahradiť `Text("Denný tracker", style = titleLarge)` + `Spacer` za `Row(Modifier.fillMaxWidth(), SpaceBetween, CenterVertically)` obsahujúci `Text("Denný tracker")` a `Button(onClick = { /* save logic */ }) { Text("Uložiť deň") }` na začiatku Column v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt`
- [x] T015 [US4] Odstrániť pôvodný `Button(onClick = { ... }) { Text("Uložiť deň") }` zo spodku Column v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` (závisí od T014)

**Checkpoint**: US4 hotová – tlačidlo Uložiť je v hlavičke, funkcionalita uloženia nezmenená

---

## Final Phase: Polish & Validácia

**Purpose**: Overenie všetkých zmien podľa quickstart.md a drobné doladenia

- [x] T016 Spustiť manuálne validačné scenáre S1–S8 z `specs/006-visual-updates-1/quickstart.md` na emulátore alebo fyzickom zariadení
- [x] T017 [P] Spustiť edge-case scenáre E1–E3 z `specs/006-visual-updates-1/quickstart.md` (prázdny stav, deň bez záznamu, backstack)
- [x] T018 [P] Overiť Slovak locale pre day labels v `DualBarChart` – skontrolovať, že `Locale("sk")` produkuje správne skratky dní (Po, Ut, St, Št, Pi, So, Ne)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: Žiadne závislosti – môže začať ihneď. **Blokuje US2 (Phase 3)**
- **US1 (Phase 2)**: Nezávisí od Phase 1 – môže začať ihneď paralelne
- **US2 (Phase 3)**: Závisí od dokončenia Phase 1 (T001–T003)
- **US3 (Phase 4)**: Plne nezávislá – môže začať kedykoľvek
- **US4 (Phase 5)**: Plne nezávislá – môže začať kedykoľvek
- **Polish (Final)**: Závisí od dokončenia všetkých US1–US4

### User Story Dependencies

| Story | Závisí od | Môže ísť paralelne s |
|-------|-----------|----------------------|
| US1 (P1) | – | Foundational, US3, US4 |
| US2 (P2) | Phase 1 hotová | US1 (ak iný vývojár) |
| US3 (P3) | – | US1, US2, US4 |
| US4 (P4) | – | US1, US2, US3 |

### Within Each User Story

- T004 → T005 → T006 → T007 (US1, sekvenčné v rovnakom súbore)
- T001, T002 [P] → T003 (Foundational)
- T008 → T009 → T010 → T011 → T012 (US2, sekvenčné)
- T013 (US3, single task)
- T014 → T015 (US4, sekvenčné)

---

## Parallel Example: Foundational + US1

```
Paralelne spustiteľné hneď:
  Task T001: Pridať AppRoutes.VECTOR_DATE konštantu do AppNavGraph.kt
  Task T002: Rozšíriť VectorViewModel o loadForDate
  Task T004: Pridať dátum do HomeScreen.kt
  Task T013: Odstrániť VECTOR z Screen enum v MainActivity.kt
  Task T014: Presunúť Button do Row s headingom v TrackerScreen.kt

Po T001+T002:
  Task T003: Pridať composable(VECTOR_DATE) do AppNavGraph.kt

Po T004:
  Task T005: Swap poradia a fontov v HomeScreen.kt
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Dokončiť Phase 2 (US1): T004 → T005 → T006 → T007
2. **STOP a VALIDUJ**: S2, S3 z quickstart.md
3. Ak validácia OK → pokračovať

### Incremental Delivery

1. US1 (P1) + US3 (P3) + US4 (P4) → paralelne (nezávislé)
2. Phase 1 (Foundational) → odblokuje US2
3. US2 (P2) → po Phase 1
4. Polish → validácia všetkého

### Odporúčané poradie pre jedného vývojára

```
T001 → T002 (paralelne) → T003
T004 → T005 → T006 → T007
T013
T014 → T015
T008 → T009 → T010 → T011 → T012
T016 → T017 (paralelne) → T018
```

---

## Notes

- `[P]` tasky = rôzne súbory, žiadne závislosti v rámci fázy
- `[Story]` label mapuje task na konkrétnu user story pre traceability
- `pointerInput` v T011 vyžaduje import `androidx.compose.foundation.gestures.detectTapGestures`
- `LocalDate.parse` v T010 vyžaduje import `java.time.LocalDate` a `java.util.Locale`
- Žiadne nové Room entity → žiadna DB migrácia → žiadne `fallbackToDestructiveMigration` riziko
- Commit po každej dokončenej user story (US1 → US2 → US3 → US4)
