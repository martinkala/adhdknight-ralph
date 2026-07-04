# ASRS Compatibility Analysis: Negative Range Elements

## Normalization Formula

All scale values are normalized to [0, 1] before contributing to the daily index:

```
value_effective = (value - scaleMin) / (scaleMax - scaleMin)
```

This ensures the index computation is range-agnostic regardless of whether an element uses 1–5, -2–2, or 0–2.

## Scenario 1: All positive-impact elements at scaleMin (worst day)

**Example**: sleep=-2, physical_activity=0, organisation=-2, mindfulness=1

- All positive-impact elements yield `value_effective ≈ 0.0`
- Daily index approaches **0** (very bad day)
- ASRS score on such a day is typically **elevated** (high ADHD symptom burden)
- Outcome: `|ASRS - index_14d_avg| > 10` → recalibration triggered

**Assessment**: CORRECT behavior. Low index + high ASRS = consistent signal that adaptation is needed.

## Scenario 2: All elements at scaleMax (best day)

**Example**: sleep=2, stress_work=-2 (minimum stress), physical_activity=2

- Positive-impact elements: `value_effective = 1.0`
- Negative-impact elements at scaleMin (-2): `value_effective = 0.0` → no penalty contribution
- Daily index approaches **100**
- ASRS score on such a day is typically **low**

**Assessment**: CORRECT behavior. High index + low ASRS = stable.

## Scenario 3: Negative-impact element with negative range at its scaleMin

**Example**: stress_work with range [-2, 2] at value -2

- `value_effective = 0.0` (minimum stress = no negative contribution)
- Index appears higher than reality if user is genuinely high-stress but the range is inverted

**Risk**: If a negative-impact element (e.g. stress_work) has a negative range AND the user assigns semantic meaning where negative = bad, the color visualization shows red (bad) but the index computation treats it as no penalty (neutral). This creates a **semantic mismatch** between visual feedback and index math.

**Mitigation**: Elements with negative impact AND negative range should either:
1. Use only positive ranges (0–N or 1–N) where higher = more of the negative behavior
2. Or be explicitly documented in `entities.yaml` with a comment explaining the inversion

## Recommendation for Future Features

When adding new elements with negative ranges and negative impact, perform a semantic review:
- Does higher value in the range mean MORE of the negative behavior (use positive range)
- Or does higher value mean LESS of the negative behavior (negative range is correct)

Document the decision in `entities.yaml` alongside `scale_min`/`scale_max`.
