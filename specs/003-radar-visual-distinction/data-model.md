# Data Model: Radar Chart Visual Distinction

## New Domain Types

### `ElementClassification` (enum)

**Location**: `android_app/app/src/main/java/com/example/madhdtracker/domain/model/RadarElementData.kt`

```
ElementClassification
├── POSITIVE   — element's higher value improves ADHD index (e.g. sleep, physical_activity)
├── NEGATIVE   — element's higher value worsens ADHD index (e.g. stress_work, alcohol)
└── NEUTRAL    — insufficient data or correlation near zero (|corr| < 0.1)
```

Classification source (MVP): `DefaultWeights.negativeKeys` → NEGATIVE; all other radar elements → POSITIVE.

### `RadarElementData` (data class)

**Location**: same file as `ElementClassification`

| Field | Type | Description |
|---|---|---|
| `key` | `String` | Element key, e.g. `"sleep"` |
| `label` | `String` | Display label, e.g. `"Spánok"` |
| `value` | `Double` | Radar value in range [0.0, 1.0] |
| `classification` | `ElementClassification` | Positive/Negative/Neutral for coloring |

---

## Modified Components

### `TrackerRepository`

**New method**: `getLatestVectorElementData(): List<RadarElementData>`

- Loads latest day's `EventValueEntity` map (existing `getLatestVectorEntities()`)
- Classifies each element in `RADAR_AXES` using `DefaultWeights.negativeKeys`
- Returns ordered `List<RadarElementData>` in `RADAR_AXES` order

### `VectorViewModel`

**Modified state**: replace `entities: MutableState<Map<String, EventValueEntity>>` with `elements: MutableState<List<RadarElementData>>`

- `refresh()` calls `repository.getLatestVectorElementData()`
- ViewModel has no classification logic — classification is repository concern

### `RadarChart` (Composable)

**Modified signature**: replace `values: List<Double>, labels: List<String>` with `elements: List<RadarElementData>`

- Color and stroke width per element derived from `ElementClassification`
- Axis spoke color = classification color
- Data dot color = classification color
- Filled polygon = translucent neutral (unchanged from current)
- Legend row added below chart: green thick line = "Pozitívny vplyv", red thin line = "Negatívny vplyv"

### `VectorScreen`

**Modified**: pass `viewModel.elements.value` to `RadarChart` instead of separate `values` and `labels` lists

---

## No DB / Entity Changes

No new Room entities. No migration. `DefaultWeights.negativeKeys` is an in-memory constant.

---

## Classification Mapping (MVP static)

| Element key | Classification |
|---|---|
| sleep | POSITIVE |
| physical_activity | POSITIVE |
| nutrition_protein | POSITIVE |
| mindfulness | POSITIVE |
| caffeine | NEGATIVE |
| alcohol | NEGATIVE |
| stress_personal | NEGATIVE |
| stress_work | NEGATIVE |
