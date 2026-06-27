# Implementation Plan: Radar Chart Visual Distinction (Positive/Negative)

**Branch**: `003-radar-visual-distinction` | **Date**: 2026-06-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-radar-visual-distinction/spec.md`

## Summary

Add per-element color and stroke-width distinction to the existing radar chart on the Advanced vektor screen. Positive elements (sleep, physical_activity, nutrition_protein, mindfulness) render with a light green axis and thicker data dot; negative elements (stress_work, stress_personal, alcohol, caffeine) render with a light red axis and thinner data dot. Classification is static for MVP, sourced from the existing `DefaultWeights.negativeKeys` constant. No DB changes, no new entities, no migration.

## Technical Context

**Language/Version**: Kotlin 1.9 / JVM 17

**Primary Dependencies**: Jetpack Compose BOM 2024.06.00, Material 3, Room 2.6.1, Compose Canvas (built-in)

**Storage**: Room (no schema changes for this feature)

**Testing**: JUnit 4 / JVM unit tests (`./gradlew test`)

**Target Platform**: Android API 26+ (Min SDK 26, Target SDK 34)

**Project Type**: Android mobile app (MVVM + Repository)

**Performance Goals**: No perceptible rendering regression — chart draw time unchanged (all Canvas operations)

**Constraints**: Offline-capable; no new dependencies; no DB migration

**Scale/Scope**: 8 radar axes, 3 classification states

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| § I — MVVM + Repository | PASS | Classification logic in Repository; ViewModel exposes `List<RadarElementData>`; Composable is pure display |
| § II — Domain logic unit tested | PASS | `getLatestVectorElementData()` has simple classification logic; unit test added |
| § III — DB schema unchanged | PASS | No new entities, no migration |
| § IV — UX low-friction | PASS | Visual distinction reduces cognitive load; no new interactions required |
| § VI — Tests required | PASS | Unit test for classification mapping added |
| § VII — Tech stack | PASS | No new dependencies; uses existing Canvas API |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-radar-visual-distinction/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── composable-api.md
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code Changes

```text
android_app/app/src/main/java/com/example/madhdtracker/
├── domain/
│   └── model/
│       └── RadarElementData.kt              NEW — ElementClassification enum + RadarElementData data class
├── data/
│   └── TrackerRepository.kt                 MODIFY — add getLatestVectorElementData()
├── ui/
│   ├── VectorViewModel.kt                   MODIFY — expose List<RadarElementData> instead of Map<String, EventValueEntity>
│   └── screens/
│       ├── RadarChart.kt                    MODIFY — per-element axis color + stroke width + legend
│       └── VectorScreen.kt                  MODIFY — pass elements to RadarChart; update value list rendering

android_app/app/src/test/java/com/example/madhdtracker/
└── domain/
    └── model/
        └── RadarElementDataTest.kt          NEW — unit test for classification correctness
```

## Implementation Steps

### Step 1 — New domain type `RadarElementData`

Create `domain/model/RadarElementData.kt`:
- `enum class ElementClassification { POSITIVE, NEGATIVE, NEUTRAL }`
- `data class RadarElementData(key, label, value: Double, classification: ElementClassification)`

No dependencies on other layers.

### Step 2 — Repository: `getLatestVectorElementData()`

In `TrackerRepository.kt` add:
```
suspend fun getLatestVectorElementData(): List<RadarElementData>
```
Logic:
1. Call existing `getLatestVectorEntities()` → `Map<String, EventValueEntity>`
2. For each entry in `RADAR_AXES` order:
   - `value = radarValue(entities[key])`  (reuse existing `radarValue()` from RadarChart.kt — move to domain layer or duplicate inline)
   - `classification = if (key in DefaultWeights.negativeKeys) NEGATIVE else POSITIVE`
   - If entities map is empty → all NEUTRAL
3. Return `List<RadarElementData>`

**Note**: `RADAR_AXES` and `radarValue()` are currently in `RadarChart.kt` (UI layer). Move `RADAR_AXES` constant to a shared location (e.g., `domain/model/RadarElements.kt`) so Repository can reference it without importing UI. `radarValue()` logic is a pure function — move to domain layer too.

### Step 3 — VectorViewModel update

Replace:
```kotlin
val entities = mutableStateOf<Map<String, EventValueEntity>>(emptyMap())
```
With:
```kotlin
val elements = mutableStateOf<List<RadarElementData>>(emptyList())
```

`refresh()` calls `repository.getLatestVectorElementData()`.

Update `VectorViewModelFactory` if needed (no signature change).

### Step 4 — `RadarChart.kt` composable update

New signature: `fun RadarChart(elements: List<RadarElementData>, modifier: Modifier = Modifier)`

Per-axis rendering changes:
- **Axis spokes**: draw each spoke with `classificationColor(element.classification)` and `classificationStrokeWidth(element.classification)`
- **Data dots**: draw each dot with classification color
- **Data polygon fill**: unchanged (single translucent fill)
- **Data polygon stroke**: draw per-axis or keep as single path in neutral color (implementation choice: per-axis is cleaner; single-path neutral is simpler — use neutral)

Color helper (inside file):
```kotlin
fun classificationColor(c: ElementClassification): Color = when (c) {
    POSITIVE -> Color(0xFF81C784)
    NEGATIVE -> Color(0xFFE57373)
    NEUTRAL  -> Color(0xFF1A4A80)
}
fun classificationStrokeWidth(c: ElementClassification): Float = when (c) {
    POSITIVE -> 3.5f
    NEGATIVE -> 2.0f
    NEUTRAL  -> 3.0f
}
```

**Legend**: Add below Canvas a `Row` or two `Text` items showing colored line indicators with labels "Pozitívny vplyv" and "Negatívny vplyv". Use `Canvas` small horizontal line icon or `Box` with background color.

### Step 5 — `VectorScreen.kt` update

Replace:
```kotlin
RadarChart(
    values = RADAR_AXES.map { (key, _) -> radarValue(entities[key]) },
    labels = RADAR_AXES.map { it.second },
    ...
)
```
With:
```kotlin
RadarChart(
    elements = viewModel.elements.value,
    ...
)
```

Update the element list below chart: since `VectorViewModel.entities` is removed, derive display values from `viewModel.elements.value`.

### Step 6 — Unit test

`RadarElementDataTest.kt`:
- Verify all 4 negative keys classify as NEGATIVE
- Verify all 4 positive keys classify as POSITIVE
- Verify empty entities → all NEUTRAL

## Complexity Tracking

No constitution violations — no complexity tracking needed.
