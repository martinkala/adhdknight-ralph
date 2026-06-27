# Implementation Plan: Dual Vector Split (Positive/Negative ADHD Sub-Indices)

**Branch**: `004-dual-vector-split` | **Date**: 2026-06-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-dual-vector-split/spec.md`

**Závislosť**: Feature 003 (`003-radar-visual-distinction`) musí byť implementovaná pred alebo súčasne — tento plán stavia na `RadarElementData`, `ElementClassification` a farebných osách z 003.

## Summary

Rozšírenie ADHD trackera o duálny pohľad: pozitívny sub-index (sleep, physical_activity, nutrition_protein, mindfulness — maximalizovať) a negatívny sub-index (stress_work, stress_personal, alcohol, caffeine — minimalizovať). Zmeny zahŕňajú: novú doménovú logiku výpočtu sub-indexov (+ unit testy), Room migráciu v1→v2 (nullable stĺpce v `index_daily`), dual-bar chart na Trend obrazovke, farebné indikátory na Home obrazovke a dva polygóny v Radar charte.

## Technical Context

**Language/Version**: Kotlin 1.9 / JVM 17

**Primary Dependencies**: Jetpack Compose BOM 2024.06.00, Material 3, Room 2.6.1 (s `@AutoMigration`), Kotlinx Coroutines 1.8.1

**Storage**: Room SQLite — migrácia v1→v2 (pridanie 2 nullable stĺpcov do `index_daily`)

**Testing**: JUnit 4 / JVM unit testy (`./gradlew test`); Room migration test (`./gradlew test --tests "*MigrationTest*"`)

**Target Platform**: Android API 26+, Min SDK 26, Target SDK 34

**Project Type**: Android mobile app (MVVM + Repository)

**Performance Goals**: Sub-indexy sa počítajú v rovnakom prechode ako kombinovaný index — žiadna dodatočná latencia

**Constraints**: Offline-first; žiadne nové knižnice; Room `@AutoMigration` vyžaduje `exportSchema = true`

**Scale/Scope**: 8 elementov (4+4), 3 obrazovky, 1 DB migrácia

## Constitution Check

| Princíp | Stav | Poznámka |
|---------|------|----------|
| § I — MVVM + Repository | PASS | Výpočet v `IndexCalculator` (domain), ukladanie v `Repository`, state vo ViewModeloch, UI je pure display |
| § II — Domain logika + unit testy | **GATE** | `computePositiveIndex()` a `computeNegativeIndex()` MUSIA mať unit testy. Blokuje merge. |
| § III — DB schéma + migrácia | PASS | `@AutoMigration(from=1, to=2)` pre 2 nullable stĺpce; `exportSchema = true` povinné |
| § IV — UX | PASS | Duálna metafora znižuje kognitívnu záťaž; Home ostáva 2-obrazovková cesta |
| § VI — Testovanie | **GATE** | Unit testy pre nové domain metódy + migration test sú povinné |
| § VII — Tech stack | PASS | Žiadne nové závislosti; Room AutoMigration je v rámci existujúcej Room 2.6.1 |

**Violations**: Žiadne — pri dodržaní § II gate podmienky.

## Project Structure

### Documentation (this feature)

```text
specs/004-dual-vector-split/
├── plan.md              ← tento súbor
├── research.md          ← Phase 0 výstup
├── data-model.md        ← Phase 1 výstup
├── contracts/
│   └── ui-contracts.md  ← Phase 1 výstup
├── quickstart.md        ← Phase 1 výstup
└── tasks.md             ← Phase 2 výstup (/speckit-tasks)
```

### Source Code Changes

```text
android_app/app/src/main/java/com/example/madhdtracker/
├── data/
│   ├── Entities.kt                          MODIFY — pridať positiveIndex, negativeIndex do IndexDailyEntity
│   ├── Models.kt                            MODIFY — pridať DailySubIndexRow data class
│   ├── Daos.kt                              MODIFY — pridať getLatestDualWithDate() do IndexDao
│   ├── AppDatabase.kt                       MODIFY — version=2, exportSchema=true, @AutoMigration
│   └── TrackerRepository.kt                 MODIFY — rozšíriť computeAndSaveDailyIndex(), pridať getLatestSubIndices(), getLatestDualIndexSeries()
├── domain/
│   └── logic/
│       └── IndexCalculator.kt               MODIFY — pridať computePositiveIndex(), computeNegativeIndex()
│   └── model/
│       └── RadarElementData.kt              NEW (z feature 003) — ElementClassification + RadarElementData
├── ui/
│   ├── HomeViewModel.kt                     MODIFY — pridať positiveIndex, negativeIndex state
│   ├── TrendViewModel.kt                    MODIFY — pridať dualSeries state
│   ├── VectorViewModel.kt                   MODIFY (z feature 003) — expose List<RadarElementData>
│   └── screens/
│       ├── HomeScreen.kt                    MODIFY — pridať dual index indikátory
│       ├── TrendScreen.kt                   MODIFY — nahradiť SimpleBarChart za DualBarChart
│       ├── RadarChart.kt                    MODIFY — pridať dva polygóny
│       └── VectorScreen.kt                  MODIFY (z feature 003) — pass elements do RadarChart

android_app/app/src/test/java/com/example/madhdtracker/
├── domain/logic/
│   └── IndexCalculatorTest.kt               MODIFY — pridať testy pre nové metódy
└── data/
    └── MigrationTest.kt                     NEW — Room migration v1→v2 test

android_app/app/schemas/                     NEW — Room exportovaná schéma (pre @AutoMigration)
android_app/app/build.gradle.kts             MODIFY — ksp arg pre schemaLocation
```

## Implementation Steps

### Step 1 — `build.gradle.kts` + Room exportSchema

Pridať do `build.gradle.kts`:
```kotlin
ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}
```
Zmeniť `AppDatabase`: `exportSchema = false` → `exportSchema = true`.
Prvý build vygeneruje `app/schemas/.../1.json` — snapshot v1 schémy, nutný pre `@AutoMigration`.

### Step 2 — `IndexDailyEntity` rozšírenie

Pridať do `Entities.kt`:
```kotlin
val positiveIndex: Double? = null
val negativeIndex: Double? = null
```
Nullable s defaultom null → existujúce call sites sa skompilujú bez zmeny.

### Step 3 — `AppDatabase` migrácia v1→v2

```kotlin
@Database(
    version = 2,
    exportSchema = true,
    autoMigrations = [AutoMigration(from = 1, to = 2)]
)
```
Room automaticky vygeneruje `ALTER TABLE index_daily ADD COLUMN positiveIndex REAL` a `ADD COLUMN negativeIndex REAL` (nullable, žiadny DEFAULT).

### Step 4 — `IndexCalculator` — nové metódy (§ II GATE)

Pridať:
```kotlin
fun computePositiveIndex(
    values: List<EventValueEntity>,
    weights: Map<String, WeightEntity>,
    positiveKeys: Set<String>
): Double?

fun computeNegativeIndex(
    values: List<EventValueEntity>,
    weights: Map<String, WeightEntity>,
    negativeKeys: Set<String>
): Double?
```
Obe: `100 × Σ(w_i × e_i for filteredKeys) / Σ(w_i for filteredKeys)`. Negatívny index BEZ inverzie (`e_i` sú raw — vyšší = viac negatívneho správania).

**Unit testy** (pridať do `IndexCalculatorTest.kt`) — povinné pre merge:
- Pozitívny index ignoruje negatívne kľúče
- Negatívny index ignoruje pozitívne kľúče
- Prázdne vstupy / žiadna zhoda → `null`
- Správna vážená hodnota pri zmiešaných vstupoch

### Step 5 — `DailySubIndexRow` + `IndexDao`

`Models.kt`: pridať `data class DailySubIndexRow(val date: String, val positiveIndex: Double?, val negativeIndex: Double?)`.

`Daos.kt` — do `IndexDao` pridať:
```sql
SELECT event_day.date, index_daily.positiveIndex, index_daily.negativeIndex
FROM index_daily INNER JOIN event_day ON index_daily.eventDayId = event_day.id
ORDER BY event_day.date DESC LIMIT :limit
```

### Step 6 — `TrackerRepository` rozšírenie

Rozšíriť `computeAndSaveDailyIndex(dayId)`:
```kotlin
val positiveKeys = DefaultWeights.weights.keys - DefaultWeights.negativeKeys
val positiveIdx = IndexCalculator.computePositiveIndex(values, weights, positiveKeys)
val negativeIdx = IndexCalculator.computeNegativeIndex(values, weights, DefaultWeights.negativeKeys)
db.indexDao().insertDaily(IndexDailyEntity(
    eventDayId = dayId,
    indexValue = indexValue,
    positiveIndex = positiveIdx,
    negativeIndex = negativeIdx
))
```

Pridať nové metódy:
```kotlin
suspend fun getLatestSubIndices(): Pair<Double?, Double?>
suspend fun getLatestDualIndexSeries(limit: Int): List<DailySubIndexRow>
```

### Step 7 — `HomeViewModel` + `HomeScreen`

`HomeViewModel`: pridať `positiveIndex` a `negativeIndex` state, naplniť z `repository.getLatestSubIndices()`.

`HomeScreen`: pridať pod `displaySmall` index číslo `Row` s dvoma farebnými indikátormi — viz [UI contracts](contracts/ui-contracts.md).

### Step 8 — `TrendViewModel` + `DualBarChart`

`TrendViewModel`: pridať `dualSeries: State<List<DailySubIndexRow>>`, volať `repository.getLatestDualIndexSeries(7)`.

`TrendScreen`: nahradiť `SimpleBarChart` za nový `DualBarChart` composable — viz [UI contracts](contracts/ui-contracts.md).

### Step 9 — `RadarChart` — dva polygóny

Rozšíriť composable (po feature 003) o `positivePath` a `negativePath`. Vstupný kontrakt sa nemení (`elements: List<RadarElementData>`). Polygóny sú odvodené z `classification` field — viz [UI contracts](contracts/ui-contracts.md).

### Step 10 — `MigrationTest`

Nový test `MigrationTest.kt`:
- Init DB v1, insert `IndexDailyEntity` so starými poľami
- Spustiť `AutoMigration` na v2
- Assert: stĺpce `positiveIndex` a `negativeIndex` existujú a sú `NULL` pre historický záznam

## Complexity Tracking

Žiadne constitution violations — tracking nie je potrebný.
