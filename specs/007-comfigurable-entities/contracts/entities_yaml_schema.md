# Contract: entities.yaml Schema

**File**: `android_app/app/src/main/assets/entities.yaml`  
**Parser**: SnakeYAML 2.2 (`org.yaml:snakeyaml:2.2`)

---

## Schema

```yaml
categories:
  <category_key>:
    label: String          # povinné, neprázdny
    clickable: Boolean     # povinné
    weight: Double         # povinné, > 0

elements:
  <element_key>:
    weight: Double         # povinné, > 0
    impact: Int            # povinné, +1 alebo -1
    parent: String|null    # voliteľné; ak null → root entita
    description: String    # voliteľné
    active: Boolean        # povinné, default true
    scale: List<Int>|null  # voliteľné; ak null → binárna entita
```

---

## Príklad (aktuálnych 9 entít + kategórie)

```yaml
categories:
  sleep:
    label: "Spánok"
    clickable: true
    weight: 15.0

  physical_activity:
    label: "Fyzická aktivita"
    clickable: true
    weight: 11.0

  lifestyle:
    label: "Životný štýl"
    clickable: false
    weight: 42.0

  head:
    label: "Mentálne aktivity"
    clickable: false
    weight: 11.0

  food:
    label: "Strava"
    clickable: false
    weight: 8.0

elements:
  overall_feeling:
    weight: 13.0
    impact: 1
    parent: null
    description: "Celkový pocit za deň"
    active: true

  sleep:
    weight: 15.0
    impact: 1
    parent: sleep
    description: "Kvalitný spánok"
    active: true

  physical_activity:
    weight: 11.0
    impact: 1
    parent: physical_activity
    description: "Fyzická aktivita"
    active: true
    scale: [1, 2, 3, 4, 5]

  stress_work:
    weight: 13.0
    impact: -1
    parent: lifestyle
    description: "Pracovný stres"
    active: true
    scale: [1, 2, 3, 4, 5]

  stress_personal:
    weight: 13.0
    impact: -1
    parent: lifestyle
    description: "Osobný stres"
    active: true
    scale: [1, 2, 3, 4, 5]

  caffeine:
    weight: 6.0
    impact: -1
    parent: lifestyle
    description: "Kofeín"
    active: true
    scale: [1, 2, 3, 4, 5]

  alcohol:
    weight: 10.0
    impact: -1
    parent: lifestyle
    description: "Alkohol"
    active: true
    scale: [1, 2, 3, 4, 5]

  nutrition_protein:
    weight: 8.0
    impact: 1
    parent: food
    description: "Príjem bielkovín"
    active: true

  mindfulness:
    weight: 11.0
    impact: 1
    parent: head
    description: "Mindfulness / meditácia"
    active: true
```

---

## Fallback pravidlá

| Situácia | Správanie |
|----------|-----------|
| Súbor neexistuje | Log `"entities.yaml not found, using defaults"` → DefaultWeights |
| Neplatný YAML | Log `"entities.yaml parse error: <msg>"` → DefaultWeights |
| Neznámy `parent` kľúč | Element ignorovaný, log `"unknown parent: <key>"` |
| `weight <= 0` | Element ignorovaný, log `"invalid weight for: <key>"` |
| `impact` nie je ±1 | Element ignorovaný, log `"invalid impact for: <key>"` |
| `scale` má menej ako 2 hodnoty | `scale` nastavené na `null` (binárna) |
| Chýba `active` | Default `true` |
| Prázdna sekcia `categories` | Fallback na defaults |
| Prázdna sekcia `elements` | Fallback na defaults |

---

## Rozšíriteľnosť

Nové atribúty môžu byť pridané bez zmeny parsera (SnakeYAML mapuje do `Map<String, Any?>`). Neznáme polia sú ignorované — backward compatible.
