# Implementation Plan: Visual UI Updates – Home, Trend, Menu & Tracker

**Branch**: `006-visual-updates-1` | **Date**: 2026-06-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-visual-updates-1/spec.md`

## Summary

Séria UI-only zmien na 4 obrazovkách ADHD trackera: oprava zobrazenia dátumu na Home stránke, výmena poradia a veľkosti fontov medzi ADHD indexom a sekciou Pozitívne/Negatívne, pridanie skratkového tlačidla na tracker, doplnenie popiskov dní do stĺpcového grafu Trendu s klikateľnou navigáciou na Vector stránku pre konkrétny deň, odstránenie Vektora z navigačného menu, a presun tlačidla Uložiť vedľa nadpisu v Dennom trackeri. Žiadna zmena dátového modelu ani domenovej logiky.

## Technical Context

**Language/Version**: Kotlin (JVM 17)

**Primary Dependencies**: Jetpack Compose BOM 2024.06.00, Material3, Navigation Compose 2.7.7

**Storage**: Room 2.6.1 (nemodifikovaný)

**Testing**: JUnit4 (JVM unit testy) — UI zmeny nie sú kryté automatizovanými testami (UI testy nie sú v MVP scope)

**Target Platform**: Android API 26+

**Project Type**: Android mobile app (MVVM + Repository)

**Performance Goals**: Bez zmeny — UI sa renderuje v 60 fps normálnym Compose rasterizovaním

**Constraints**: Offline-first, bez sieťových volaní, bez novej závislosť

**Scale/Scope**: 4 Composable súbory, 1 ViewModel rozšírenie, 1 navigačný súbor, 1 enum v MainActivity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princip | Status | Poznámka |
|---------|--------|----------|
| I – MVVM + Repository | ✅ | Zmeny ostávajú na UI vrstve. Composables → ViewModel → Repository cez callbacky. |
| II – Doménová logika | ✅ | Nedotknutá. Žiadna zmena IndexCalculator, WeightAdapter ani ASRS. |
| III – Dátový model | ✅ | Žiadna nová entita ani DB migrácia. |
| IV – UX (min. kliknutia) | ✅ | Skratkové tlačidlo znižuje kliknutia na tracker. Viditeľné Uložiť tlačidlo znižuje zabudnutie uloženia. |
| VII – Technický stack | ✅ | Žiadna nová závislosť. `pointerInput` a `LocalDate` sú súčasťou existujúcich závislostí. |

**Constitution verdict**: Všetky gates splnené. Pokračovanie povolené.

## Project Structure

### Documentation (this feature)

```text
specs/006-visual-updates-1/
├── spec.md              # Špecifikácia
├── plan.md              # Tento súbor
├── research.md          # Phase 0 výskum
├── data-model.md        # Phase 1 – dátové a UI kontrakty
├── quickstart.md        # Phase 1 – validačné scenáre
├── contracts/
│   └── ui-navigation-contracts.md   # Composable signatúry a route zmeny
└── tasks.md             # Phase 2 – generuje /speckit-tasks
```

### Source Code (repository root)

```text
android_app/app/src/main/java/com/example/madhdtracker/
├── MainActivity.kt                          # Screen enum – odstrániť VECTOR
├── ui/
│   ├── VectorViewModel.kt                   # Pridať loadForDate(date)
│   ├── navigation/
│   │   └── AppNavGraph.kt                   # Pridať VECTOR_DATE route + HomeScreen callback
│   └── screens/
│       ├── HomeScreen.kt                    # Dátum, swap sekcií, shortcut tlačidlo
│       ├── TrendScreen.kt                   # Popisky dní, klikateľné stĺpce
│       ├── TrackerScreen.kt                 # Presun tlačidla Uložiť
│       └── VectorScreen.kt                  # Prijíma date param, LaunchedEffect loadForDate
```

## Implementation Phases

### Phase A – NavigationBar a routing (základ pre ostatné)

**Súbory**: `MainActivity.kt`, `AppNavGraph.kt`, `VectorViewModel.kt`

1. **MainActivity.kt** – odstraniť `VECTOR` z `Screen` enum
2. **AppNavGraph.kt**:
   - Pridať `AppRoutes.VECTOR_DATE = "vector/{date}"` konštantu
   - Pridať helper `fun vectorForDate(date: String): String = "vector/$date"`
   - Pridať `composable(AppRoutes.VECTOR_DATE)` blok s `navArgument("date")` a `LaunchedEffect(date)`
   - Aktualizovať `HomeScreen(...)` volanie – pridať `onEditClick = { navController.navigate(AppRoutes.TRACKER) }`
   - Aktualizovať `TrendScreen(...)` volanie – pridať `onDayClick = { date -> navController.navigate(AppRoutes.vectorForDate(date)) }`
3. **VectorViewModel.kt** – pridať `loadedDate` a `loadForDate(date: String)` metódu

### Phase B – VectorScreen: podpora dátumu

**Súbor**: `ui/screens/VectorScreen.kt`

1. Pridať parameter `date: String? = null`
2. V `LaunchedEffect` – ak `date != null` volaj `viewModel.loadForDate(date)`, inak `viewModel.refresh()`
3. Aktualizovať nadpis: ak `date != null` zobraziť dátum, inak "Radar – detail"

### Phase C – HomeScreen: dátum, swap sekcií, shortcut tlačidlo

**Súbor**: `ui/screens/HomeScreen.kt`

1. Pridať parameter `onEditClick: () -> Unit`
2. Pridať `val today = remember { LocalDate.now().format(DateTimeFormatter.ofPattern("d. M. yyyy")) }` na začiatok Composable
3. Zmeniť `Text("Dnešný prehľad")` na `Text("Dnešný prehľad – $today")`
4. V Card s ADHD dátami:
   - **Presunúť sekciu Pozitívne/Negatívne NA VRCH** s `TextStyle = displaySmall` pre hodnoty
   - Pod ňu pridať `Row` s tlačidlom `"Upraviť denný záznam"` (volaním `onEditClick()`)
   - **ADHD index sekciu PRESUNÚŤ POD** s `TextStyle = titleMedium` pre hodnotu a `labelSmall` pre popis

### Phase D – TrendScreen: popisky dní a klikateľné stĺpce

**Súbor**: `ui/screens/TrendScreen.kt`

1. Pridať parameter `onDayClick: (String) -> Unit` do `TrendScreen`
2. Prúdat `onDayClick` do `DualBarChart`
3. V `DualBarChart`:
   - Pridať parameter `onDayClick: (String) -> Unit`
   - Pridať `Modifier.pointerInput(items)` na Canvas s `detectTapGestures` – vypočítať `tappedIndex = (offset.x / (size.width / items.size)).toInt().coerceIn(0, items.lastIndex)` a zavolať `onDayClick(items[tappedIndex].date)`
   - Zmeniť wrapping z čistého Canvas na `Column`:
     - Canvas ostáva (bary)
     - Pridať `Row(modifier = Modifier.fillMaxWidth())` s `items.size` x `Text` (skrátený dátum, `Modifier.weight(1f)`, `textAlign = Center`)
   - Formátovanie dátumu: `LocalDate.parse(date).format(DateTimeFormatter.ofPattern("EE\nd.M", Locale("sk")))` (2-riadkový label: deň + dátum)

### Phase E – TrackerScreen: presun tlačidla Uložiť

**Súbor**: `ui/screens/TrackerScreen.kt`

1. Nahradiť `Text("Denný tracker")` za:
   ```kotlin
   Row(
       modifier = Modifier.fillMaxWidth(),
       horizontalArrangement = Arrangement.SpaceBetween,
       verticalAlignment = Alignment.CenterVertically
   ) {
       Text("Denný tracker", style = MaterialTheme.typography.titleLarge)
       Button(onClick = { /* pôvodná logika uloženia */ }) { Text("Uložiť deň") }
   }
   ```
2. Extrahovať logiku `onClick` do lokálnej funkcie `fun saveAndNavigate()` pre zdieľanie medzi novým a starým umiestnením (alebo jednoducho presunúť a odstrániť starý Button)
3. Odstrániť pôvodný `Button` na spodku Column

## Complexity Tracking

Žiadne porušenia Constitution – sekcia nie je relevantná.
