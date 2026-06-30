# UI Contracts: Visual Updates 2

**Feature**: 008-visual-updates-2
**Date**: 2026-06-29

---

## Contract 1: EntityDoubleBarChart composable

**Súbor**: `ui/screens/EntityBarChart.kt`

```kotlin
@Composable
fun EntityDoubleBarChart(
    entities: Map<String, EventValueEntity>,  // hodnoty z DB
    elementConfig: ElementConfig,             // konfigurácia entít
    modifier: Modifier = Modifier
)
```

**Správanie**:
- Stĺpce ľavá strana = entity kde `elementConfig.elements[key].impact == -1`, červené (`Color(0xFFE57373)`)
- Stĺpce pravá strana = entity kde `elementConfig.elements[key].impact == +1`, zelené (`Color(0xFF81C784)`)
- Label každého stĺpca: `"[kategória] / [popis entity]"` alebo len `"[popis entity]"` ak parent == null
- Hodnota normalizovaná: `radarValue(entities[key])` z `0.0` do `1.0`
- Entita `overall_feeling` je vynechaná
- Ak `entities` je prázdna mapa — zobrazí sa prázdny chart (žiadny radarchart fallback)

**Vstupné invarianty**:
- `elementConfig.elements` môže byť prázdny — chart zobrazí nič
- Hodnota stĺpca môže byť 0.0 (entita zaznamenaná ako neaktívna alebo 0/1 binary=false)

---

## Contract 2: HomeScreen

**Súbor**: `ui/screens/HomeScreen.kt`

**Zmeny parametrov**: Žiadna zmena signatúry composable `HomeScreen(viewModel: HomeViewModel, onEditClick: () -> Unit)`.

**Zmeny layoutu**:
- Karta "Radar" → nahradená `EntityDoubleBarChart(viewModel.vectorEntities.value, viewModel.elementConfig)`
- Karta "Tip dňa" → odstránená
- Metriky: `"Denný ADHD index"`, `"Spokojnosť"`, `"Vyplnené"` v jednej `Row` so 3 `Column(weight(1f))`
- Text `"Splnené"` → `"Vyplnené"`

---

## Contract 3: VectorScreen

**Súbor**: `ui/screens/VectorScreen.kt`

**Zmeny parametrov**: Žiadna zmena signatúry `VectorScreen(viewModel: VectorViewModel, date: String?)`.

**Zmeny layoutu**:
- Titulok: `"Radar – $date"` → `"Denný detail – $date"` (resp. `"Denný detail – detail"` ak date == null)
- `RadarChart(...)` → `EntityDoubleBarChart(viewModel.entities.value, viewModel.elementConfig)`
- Textový zoznam entít pod chartom zostáva (zostáva `RADAR_AXES.forEach { ... }` blok) — môže byť neskôr vyčistený

---

## Contract 4: TrackerScreen

**Súbor**: `ui/screens/TrackerScreen.kt`

**Zmeny parametrov**: Žiadna zmena signatúry.

**Zmeny layoutu**:
- Card farba pozadia pre každý element: `if (element.impact == 1) Color(0x1A4CAF50) else Color(0x1AF44336)` namiesto `MaterialTheme.colorScheme.surface`
- Po poslednom `Spacer` v scrollovacom obsahu: nové `Button("Uložiť deň")` s rovnakou logikou ako horné
- Horné tlačidlo nezmenené

**ElementUiState rozšírenie**:
```kotlin
data class ElementUiState(
    val key: String,
    val label: String,
    val hasScale: Boolean,
    val impact: Int    // NOVÉ
)
```

---

## Contract 5: TrendScreen

**Súbor**: `ui/screens/TrendScreen.kt`

**Zmeny layoutu**:
- Textový zoznam dní (`series.forEach { row -> Text(...) }`) → každý riadok obalený v `Card` s farebným pozadím
  - `row.indexValue >= 50.0` → `containerColor = Color(0x1A4CAF50)` (bledozelená)
  - `row.indexValue < 50.0` → `containerColor = Color(0x1AF44336)` (bledočervená)
- Zoradenie: série musia byť od najnovšieho po najstarší (index 0 = najnovší deň)

---

## Contract 6: HomeViewModel a VectorViewModel

**Nová property (read-only)**:

```kotlin
// HomeViewModel.kt
val elementConfig: ElementConfig get() = repository.elementConfig

// VectorViewModel.kt
val elementConfig: ElementConfig get() = repository.elementConfig
```

**Invariant**: `repository.elementConfig` je vždy non-null (inicializovaný pri vytvorení TrackerRepository).
