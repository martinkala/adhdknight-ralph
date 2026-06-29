# Contract: app_config.json Schema

**Feature**: 005-app-config-layer | **Date**: 2026-06-28

Vývojár edituje `android_app/app/src/main/assets/app_config.json` pred buildovaním. Súbor musí byť platný JSON. Chýbajúce alebo neplatné polia sú ticho nahradené zabudovanými fallback hodnotami (pozri `data-model.md` — validačné pravidlá).

---

## Kompletná schéma so všetkými defaults

```json
{
  "weights": {
    "overall_feeling":    13.0,
    "sleep":              15.0,
    "physical_activity":  11.0,
    "stress_work":        13.0,
    "stress_personal":    13.0,
    "nutrition_protein":   8.0,
    "caffeine":            6.0,
    "alcohol":            10.0,
    "mindfulness":        11.0
  },
  "element_classification": {
    "negative_keys": ["stress_work", "stress_personal", "alcohol", "caffeine"]
  },
  "adaptation": {
    "alpha":                  0.2,
    "clamp_min_factor":       0.5,
    "clamp_max_factor":       2.0,
    "correlation_threshold":  0.1,
    "min_history_days":       15,
    "min_series_size":         5
  },
  "asrs": {
    "delta_threshold":           10.0,
    "consecutive_measurements":   2,
    "recalibration_alpha":        0.3
  },
  "notification": {
    "quiet_start_hour":    22,
    "quiet_start_minute":   0,
    "quiet_end_hour":       8,
    "quiet_end_minute":     0,
    "stress_threshold_scale": 4,
    "neglected_area_days":  3,
    "stress_recovery_days": 3
  }
}
```

---

## Popis polí

### `weights` (object)

Váhy 9 elementov. Suma musí byť ≈ 100 (tolerancia ±5 %). Ak suma mimo rozsahu, hodnoty sa normalizujú automaticky.

| Kľúč | Typ | Rozsah | Default |
|------|-----|--------|---------|
| `overall_feeling` | number | > 0 | 13.0 |
| `sleep` | number | > 0 | 15.0 |
| `physical_activity` | number | > 0 | 11.0 |
| `stress_work` | number | > 0 | 13.0 |
| `stress_personal` | number | > 0 | 13.0 |
| `nutrition_protein` | number | > 0 | 8.0 |
| `caffeine` | number | > 0 | 6.0 |
| `alcohol` | number | > 0 | 10.0 |
| `mindfulness` | number | > 0 | 11.0 |

### `element_classification` (object)

| Kľúč | Typ | Popis | Default |
|------|-----|-------|---------|
| `negative_keys` | string[] | Elementy kde vyššia hodnota = horšie (invertujú sa vo výpočte) | `["stress_work","stress_personal","alcohol","caffeine"]` |

Neznáme kľúče v `negative_keys` sú ignorované. `positive_keys` sa neuvádza — odvodí sa ako `weights.keys - negative_keys`.

### `adaptation` (object)

| Kľúč | Typ | Rozsah | Default | Popis |
|------|-----|--------|---------|-------|
| `alpha` | number | (0, 1] | 0.2 | Koeficient učenia váh |
| `clamp_min_factor` | number | > 0 | 0.5 | Min váha = factor × default_weight |
| `clamp_max_factor` | number | > clamp_min_factor | 2.0 | Max váha = factor × default_weight |
| `correlation_threshold` | number | > 0 | 0.1 | Min \|korelácia\| pre zmenu váhy |
| `min_history_days` | integer | ≥ 1 | 15 | Min počet záznamov v histórii |
| `min_series_size` | integer | ≥ 1 | 5 | Min počet hodnôt pre Pearsonov koeficient |

### `asrs` (object)

| Kľúč | Typ | Rozsah | Default | Popis |
|------|-----|--------|---------|-------|
| `delta_threshold` | number | > 0 | 10.0 | Max rozdiel \|ASRS - index_avg\| bez re-kalibrácie |
| `consecutive_measurements` | integer | ≥ 1 | 2 | Počet meraní nad prahom pre trigger |
| `recalibration_alpha` | number | (0, 1] | 0.3 | Zvýšený alpha počas re-kalibrácie |

### `notification` (object)

| Kľúč | Typ | Rozsah | Default | Popis |
|------|-----|--------|---------|-------|
| `quiet_start_hour` | integer | 0-23 | 22 | Začiatok tichého intervalu (hodina) |
| `quiet_start_minute` | integer | 0-59 | 0 | Začiatok tichého intervalu (minúta) |
| `quiet_end_hour` | integer | 0-23 | 8 | Koniec tichého intervalu (hodina) |
| `quiet_end_minute` | integer | 0-59 | 0 | Koniec tichého intervalu (minúta) |
| `stress_threshold_scale` | integer | 1-5 | 4 | Min scale hodnota pre "vysoký stres" |
| `neglected_area_days` | integer | ≥ 1 | 3 | Počet dní bez aktivity = "zanedbané" |
| `stress_recovery_days` | integer | ≥ 1 | 3 | Počet po sebe idúcich dní stres+no-mindfulness |

---

## Pravidlá backward kompatibility

- Neznáme JSON kľúče na ľubovoľnej úrovni sú ignorované (future-proofing pri downgrade APK)
- Konfigurácia bez niektorých sekcií je platná — chýbajúca sekcia → celá sekcia z defaults
- Zmeny tohto schémy sú backward-compatible pokiaľ sa existujúce kľúče nemenia

---

## Príklady použitia

### Zvýšiť váhu spánku a znížiť alpha

```json
{
  "weights": {
    "sleep": 20.0,
    "overall_feeling": 13.0,
    "physical_activity": 11.0,
    "stress_work": 11.0,
    "stress_personal": 11.0,
    "nutrition_protein": 8.0,
    "caffeine": 6.0,
    "alcohol": 9.0,
    "mindfulness": 11.0
  },
  "adaptation": {
    "alpha": 0.1
  }
}
```

*Poznámka: Ostatné polia sa doplnia z defaults. Suma váh = 100 → žiadna normalizácia.*

### Presunúť caffeine do pozitívnych elementov

```json
{
  "element_classification": {
    "negative_keys": ["stress_work", "stress_personal", "alcohol"]
  }
}
```
