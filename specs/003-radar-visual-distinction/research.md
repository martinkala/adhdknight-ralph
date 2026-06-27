# Research: Radar Chart Visual Distinction

## Classification Strategy

**Decision**: Static classification via `DefaultWeights.negativeKeys` for MVP.

**Rationale**: The codebase already has `DefaultWeights.negativeKeys = setOf("stress_work", "stress_personal", "alcohol", "caffeine")`. These are semantically correct — higher value = worse ADHD state, so they are always negatively correlated with `overall_feeling`. Dynamic Pearson-based classification requires ≥15 days of data and a new repository query. For MVP, static classification delivers the feature immediately and is semantically identical to what dynamic would produce for the majority of users.

**Alternatives considered**:
- **Dynamic (Pearson)**: `IndexCalculator.adaptWeights()` already computes correlations, but they are not persisted. Computing them on every VectorScreen open requires reading 15+ days of history — adds latency and complexity with no user-visible difference for typical usage. Post-MVP candidate.
- **Hardcoded per-spec**: Identical to static via `negativeKeys` but duplicates the constant. Rejected — use existing authoritative source.

**Architecture hook for future dynamic**: `RadarElementData.classification` field is populated by Repository, not ViewModel, so the data flow is upgrade-safe (swap static → dynamic in Repository without touching UI layer).

---

## Color Values

**Decision**: Material-style light green / light red from Android's Color system.

| Classification | Fill/Stroke Color | Hex | Stroke Width |
|---|---|---|---|
| POSITIVE | Light green | `#81C784` (Material Green 300) | 3.5f dp |
| NEGATIVE | Light red | `#E57373` (Material Red 300) | 2.0f dp |
| NEUTRAL | Default blue (existing) | `#1A4A80` | 3.0f dp |

**Rationale**: Material 300-level colors are "light" as requested (not saturated primary), readable on white/light background, sufficient contrast ratio (≥3:1 on white). Stroke width difference (3.5f vs 2.0f) provides FR-009 accessibility cue without being distracting.

---

## Canvas Drawing Strategy

**Decision**: Per-axis colored segments — draw axis spoke + data dot per element individually; retain single filled polygon for the data shape fill.

**Rationale**: Current `RadarChart.kt` draws a single `Path` for all data points. Splitting into per-element paths is necessary for per-element color. Two approaches:
1. **Per-axis spokes colored**: Color the radial axis lines by element type — visually clear, straightforward to implement by looping and drawing each axis with its classification color.
2. **Per-edge polygon segments**: Split polygon edges by classification — complex (mixed-class adjacent segments are ambiguous), not standard in radar charts.

**Chosen**: Color the axis spokes and data dots per element. The filled data polygon stays with a neutral translucent fill. Axis color = classification color. Data dot color = classification color.

---

## No New Entities or DB Migration

Confirmed: feature uses `DefaultWeights.negativeKeys` (in-memory constant). No schema change, no migration needed. Consistent with FR-008 and Constitution § III.

---

## NEUTRAL for `overall_feeling`

`overall_feeling` is the target variable (not in `RADAR_AXES`). It is already excluded from the radar chart (`RADAR_AXES` in `RadarChart.kt` has 8 axes, not 9). No classification needed for it.
