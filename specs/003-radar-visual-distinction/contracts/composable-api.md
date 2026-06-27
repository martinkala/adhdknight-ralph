# UI Contract: RadarChart Composable

## Current signature (to be replaced)

```kotlin
@Composable
fun RadarChart(
    values: List<Double>,
    labels: List<String>,
    modifier: Modifier = Modifier
)
```

## New signature

```kotlin
@Composable
fun RadarChart(
    elements: List<RadarElementData>,
    modifier: Modifier = Modifier
)
```

## Invariants

- `elements.size >= 3` — chart requires at least 3 axes; caller must not pass fewer
- `elements[i].value` ∈ [0.0, 1.0] — coerced internally, but caller should normalize
- Order of `elements` determines axis order (clockwise from top)
- `elements` must be in `RADAR_AXES` order (defined in `RadarChart.kt`)

## Visual contract

| Classification | Axis spoke color | Data dot color | Stroke width |
|---|---|---|---|
| POSITIVE | `#81C784` (light green) | `#81C784` | 3.5f |
| NEGATIVE | `#E57373` (light red) | `#E57373` | 2.0f |
| NEUTRAL | `#1A4A80` (existing blue) | `#1A4A80` | 3.0f |

- Fill polygon: `#3A6EA5` at 35% alpha (unchanged)
- Legend: rendered below the Canvas, always visible, 2 rows max

## VectorViewModel contract

Exposes: `elements: State<List<RadarElementData>>`

- Empty list when no data loaded yet
- Populated via `refresh()` which calls `repository.getLatestVectorElementData()`
- Classification is NOT computed in ViewModel — provided by Repository
