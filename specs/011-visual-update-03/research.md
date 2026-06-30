# Research: Visual Update 03

**Date**: 2026-06-30 | **Feature**: 011-visual-update-03

---

## Decision 1: Oprava Home date bugy — prístup k dátam

**Decision**: Pridať date-scoped metódy do `TrackerRepository` namiesto modifikácie `getLatest*()` metód.

**Rationale**: `getLatest*()` metódy sú stále potrebné inde (WeeklySummary, notifikácie). Nové metódy ako `getIndexForDate(date)`, `getSatisfactionForDate(date)` a `getSubIndicesForDate(date)` sú čisté additive zmeny bez regresie.

**Konkrétne nové metódy** (`TrackerRepository.kt`):
- `getIndexForDate(date: String): Double?` — `db.indexDao()` dotaz podľa `EventDayEntity.date`
- `getSatisfactionForDate(date: String): Int?` — `db.satisfactionDao()` join cez `EventDayEntity`
- `getSubIndicesForDate(date: String): Pair<Double?, Double?>` — z `IndexDailyEntity` cez `EventDayEntity.id`
- `getCompletionCountsForDate(date: String): Pair<Int, Int>?` — count active values pre daný deň
- `getAllEventDates(): List<String>` — `db.eventDayDao().getAllDates()` zoradené DESC

**Note**: `getVectorEntitiesForDate(date)` už existuje ako `getValuesForDate(date: String)` — žiadna zmena.

**Alternatives considered**:
- Úprava `getLatest*()` — odmietnuté: breaking change pre existujúce callery
- Flow/StateFlow s dátumovým filtrom — odmietnuté: nadmerná komplexnosť pre jednoduché read queries

---

## Decision 2: Auto-save stratégia (US2)

**Decision**: `saveCurrent(date: String)` na `TrackerViewModel` extrahuje logiku z existujúcej `onSave` lambdy a volá `viewModel.saveDay()` s aktuálnym formState; Switch triggeruje okamžité volanie; Slider triggeruje `LaunchedEffect` s `delay(500L)`.

**Rationale**: `LaunchedEffect(key = state.scale.value)` v Compose sa spustí vždy keď sa kľúč zmení. Ak používateľ posunie slider znova pred uplynutím 500ms, predchádzajúci effect sa zruší (cancellation) a spustí sa nový — prirodzený debounce bez externej knižnice.

**Dôležité**: `saveCurrent()` musí volať `repository.getOrCreateDay(date)` ako prvý krok keď dnešok ešte nemá záznam — to zaistí, že auto-save nevyprodukuje `NullPointerException` pri prvom ukladaní.

**Alternatives considered**:
- Kotlin `Flow.debounce()` — odmietnuté: vyžaduje konverziu MutableState na Flow, oveľa viac kódu
- `Handler.postDelayed()` — odmietnuté: nie Compose idiomatické; memory leak riziko

---

## Decision 3: Dual bar chart category pairing (US3)

**Decision**: Nová trieda `BarRow(negEntry: BarEntry?, posEntry: BarEntry?)`. Párovanie prebehne tak, že entity sú zoskupené podľa `el.parent` (categoryKey z `ElementConfig`). Pre každú kategóriu sa vytvorí zoznam riadkov kde neg[i] a pos[i] z rovnakej kategórie sú na rovnakom riadku. Entity bez kategórie (`parent == null`) sú standalone riadky.

**Weight value inside bar**: Zobrazuje `element.weight` (konfiguráciu váhy entity, nie efektívnu váhu). Dôvod: `element.weight` je statický, zrozumiteľný ("váha tejto aktivity je 8"), kým `w * e_i` závisí na dennej hodnote a mení sa každý deň — menej zrozumiteľné.

**Text rendering**: `Canvas.drawIntoCanvas { canvas.nativeCanvas.drawText(text, x, y, paint) }` kde `paint.color = android.graphics.Color.WHITE`. Zobraziť len keď `fraction > 0.2f` (bar aspoň 20% šírky).

**Alternatives considered**:
- `drawText` na Compose Canvas — nie je natívne podporované; `nativeCanvas` je štandardný prístup
- Separate Text composable pred barom — odmietnuté: text by prekrýval label entity

---

## Decision 4: Pie chart implementácia (US4)

**Decision**: `Canvas.drawArc(color, startAngle, sweepAngle, useCenter = false, style = Fill)` v kruhku, s vnútorným bielym kruhom (donut efekt).

**Entity pre výseč**: Všetky aktívne entity okrem `overall_feeling`. Proporcionalita: `radarValue(entity)` (existujúca funkcia v EntityBarChart.kt) — normalizuje scale/binary na 0–1.

**Max entities**: Ak viac ako 6 entít → zobraziť top 5 podľa `radarValue` + ostatné zlúčiť do sivej "Ostatné" výseče.

**Labels**: Nie — popis entity v bare je dostatočný (US3 zobrazuje labelsy v dual bare). Pie chart je len vizuálny prehľad kompozície.

**Alternatives considered**:
- Externá chart knižnica (Vico, MPAndroidChart) — odmietnuté: §VII zakazuje, Canvas je dostatočný
- `drawArc(useCenter = true)` — odmietnuté: vizuálne horšie (zerorový stred kliná)

---

## Decision 5: Swipe navigácia (US5)

**Decision**: `Modifier.pointerInput(Unit) { detectHorizontalDragGestures { _, dragAmount -> ... } }` s prahom `abs(dragAmount) > 60f` pre spustenie navigácie.

**`availableDates`**: Načítané z `getAllEventDates()` pri `init {}` v `HomeViewModel`. Vracia `List<String>` (ISO date strings), konvertovaný na `List<LocalDate>`.

**Swipe threshold 60dp**: Dostatočne veľké na zabránenie náhodných swipe pri vertikálnom scrollovaní; dostatočne malé pre pohodlné ovládanie.

**Conflict s vertikálnym scrollom**: `detectHorizontalDragGestures` nezasahuje do vertikálneho scrollu — Compose gesture system ich automaticky rozlíši podľa smeru.

**Alternatives considered**:
- `HorizontalPager` (Compose Foundation) — odmietnuté: naviguje medzi stránkami, nie dňami; vyžadovalo by mapovanie dátumov na stránky; nadmerná komplexnosť
- `rememberSwipeableState` — deprecated v Material3

---

## Decision 6: Info obrazovka — zdroj váh (US6)

**Decision**: `InfoScreen` prijíma `repository: TrackerRepository` ako parameter. Váhy načítava cez `repository.getWeightsSnapshot()` (existujúca metóda alebo `db.weightsDao().getAll()`). Personalizovaná váha sa zobrazí ak `weightPersonal != null`.

**Načítanie**: Jednorázové `LaunchedEffect(Unit)` pri otvorení obrazovky — `LazyColumn` s entitami zoskupenými podľa kategórie.

**Groupovanie**: `elementConfig.elements.values.groupBy { it.parent ?: "__root__" }` — kategórie sú `elementConfig.categories`, root elementy (bez kategórie) tvoria samostatnú skupinu.

---

## Decision 7: Home icon — material-icons-core (US7)

**Decision**: Pridať `implementation(composeBom)` + `implementation("androidx.compose.material:material-icons-core")` do `build.gradle.kts`. Použiť `Icons.Filled.Home`.

**BOM verzia**: `2024.06.00` — `material-icons-core` je súčasťou tohto BOM; verzia sa nevyžaduje explicitne.

**Alternatives considered**:
- Canvas ikona domu — odmietnuté: nadmerná komplexnosť bez benefitu; maintenance záťaž
- Unicode emoji "🏠" v Text — odmietnuté: vizuálne nezodpovedá Material Design štandardu; rendering závislý od systémovej fonty

---

## Decision 8: User entity bug (US8)

**Finding**: `buildElementList(elementConfig)` v `TrackerViewModel.kt` iteruje len cez `elementConfig.elements` (YAML/assets). `getUserElements()` z `TrackerRepository` nie je volaný v TrackerViewModel. Toto je **potvrdený bug** — user-defined entity sú zahrnuté v `getActiveElementKeys()` pre výpočet indexu, ale nie v zozname zobrazených entít v Trackeri.

**Fix**: V `TrackerViewModel.init {}` po načítaní `elementConfig` asynchrónne zavolať `repository.getUserElements()` a merge-núť ich do `elements` listu. Každý `UserElementEntity` sa konvertuje na `ElementUiState(key, label, hasScale, impact)` — `hasScale = entity.scale != null`.

**Potential issue**: `elements` je `val List<ElementUiState>` — zmena na mutable `mutableStateListOf` alebo `MutableState<List>` bude potrebná ak sa nemá list znovu-buildovať pri každom compose.
