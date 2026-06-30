# Data Model: Unified Entity Tree (010-categories-chage)

**Date**: 2026-06-30 | **Research**: [research.md](research.md)

---

## Kotlin Dátový Model

### `EntityNode` (nahrádza `Category` + `Element`)

**Súbor**: `android_app/app/src/main/java/com/example/madhdtracker/domain/model/ElementConfig.kt`

```kotlin
data class EntityNode(
    val key: String,
    val weight: Double,
    val impact: Int?,       // null = non-trackable group; 1 = positive; -1 = negative
    val parent: String?,    // null = root node
    val label: String,      // display name (was Category.label / Element.description)
    val active: Boolean,
    val scale: List<Int>?,  // null = binary on/off; [1..5] = slider
    val clickable: Boolean  // from old Category; irrelevant for pure leaves
)
```

**Validácia pri loading**:
- `weight > 0.0` — inak uzol sa zahodí
- `impact in {null, -1, 1}` — inak uzol sa zahodí
- `parent` musí existovať v `nodes` mape (ak nie je null) — inak uzol sa zahodí
- Žiadne cyklické referencie (overuje `EntityConfigLoader`)
- `overall_feeling` MUSÍ byť prítomný — inak loader vráti fallback

---

### `EntityConfig` (nahrádza `ElementConfig`)

**Súbor**: `android_app/app/src/main/java/com/example/madhdtracker/domain/model/ElementConfig.kt`

```kotlin
data class EntityConfig(
    val nodes: Map<String, EntityNode>
) {
    val negativeKeys: Set<String>
        get() = nodes.values.filter { it.impact == -1 && it.active }.map { it.key }.toSet()

    val positiveKeys: Set<String>
        get() = nodes.values.filter { it.impact == 1 && it.active }.map { it.key }.toSet()

    // Trackovateľné uzly (majú impact a sú aktívne)
    val trackableNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact != null && it.value.active }

    // Skupiny — non-trackable, slúžia len ako parent pre vážený priemer
    val groupNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact == null }

    // Spätná kompatibilita: kľúče všetkých sledovaných entít
    val trackableKeys: Set<String>
        get() = trackableNodes.keys
}
```

**Typové aliasy (backward compat pre existujúci kód)**:
```kotlin
// Voliteľné — ak je priveľa miest na update, pridať:
typealias ElementConfig = EntityConfig
```
*Poznámka: V tomto projekte je počet použití `elementConfig.*` malý — typealias nie je potrebný, všetky miesta sa aktualizujú priamo.*

---

## YAML Konfigurácia

### Nový formát — `entities.yaml`

**Súbor**: `android_app/app/src/main/assets/entities.yaml`

```yaml
nodes:
  overall_feeling:
    label: "Celkový pocit za deň"
    weight: 13.0
    impact: 1
    active: true
    scale: [1, 2, 3, 4, 5]

  sleep:
    label: "Spánok"
    weight: 15.0
    impact: 1
    active: true
    clickable: true

  physical_activity:
    label: "Fyzická aktivita"
    weight: 11.0
    impact: 1
    active: true
    scale: [1, 2, 3, 4, 5]
    clickable: true

  lifestyle:
    label: "Životný štýl"
    weight: 42.0
    # Žiadny impact → non-trackable group

  stress_work:
    label: "Pracovný stres"
    weight: 13.0
    impact: -1
    parent: lifestyle
    active: true
    scale: [1, 2, 3, 4, 5]

  stress_personal:
    label: "Osobný stres"
    weight: 13.0
    impact: -1
    parent: lifestyle
    active: true
    scale: [1, 2, 3, 4, 5]

  head:
    label: "Mentálne aktivity"
    weight: 11.0
    # Žiadny impact → non-trackable group

  mindfulness:
    label: "Mindfulness / meditácia"
    weight: 11.0
    impact: 1
    parent: head
    active: true

  Adiction:
    label: "Závislosti"
    weight: 15.0
    impact: -1
    parent: head
    active: true
    scale: [1, 2, 3, 4, 5]

  Procrastination:
    label: "Prokrastinácia"
    weight: 10.0
    impact: -1
    parent: head
    active: true
    scale: [1, 2, 3, 4, 5]

  food:
    label: "Strava"
    weight: 8.0
    # Žiadny impact → non-trackable group

  caffeine:
    label: "Kofeín"
    weight: 6.0
    impact: -1
    parent: food
    active: true
    scale: [1, 2, 3, 4, 5]

  alcohol:
    label: "Alkohol"
    weight: 10.0
    impact: -1
    parent: food
    active: true
    scale: [1, 2, 3, 4, 5]

  nutrition_protein:
    label: "Príjem bielkovín"
    weight: 8.0
    impact: 1
    parent: food
    active: true

  vitamins:
    label: "Vitamíny"
    weight: 4.0
    impact: 1
    parent: food
    active: true

  organisation:
    label: "Organizácia úloh"
    weight: 8.0
    # Žiadny impact → non-trackable group

  pomodoro:
    label: "Pomodoro"
    weight: 11.0
    impact: 1
    parent: organisation
    active: true
```

---

## DB Schéma — Migrácia 3→4

### `UserElementEntity` — pridanie `userId`

**Súbor**: `android_app/app/src/main/java/com/example/madhdtracker/data/Entities.kt`

```kotlin
@Entity(tableName = "user_element")
data class UserElementEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val key: String,
    val label: String,
    val weight: Double,
    val impact: Int,
    val parent: String?,
    val scale: String?,
    val active: Boolean = true,
    val userId: String? = null    // NOVÝ stĺpec — nullable, default null
)
```

**Room AutoMigration 3→4**:

```kotlin
// AppDatabase.kt
@Database(
    version = 4,   // bolo 3
    autoMigrations = [
        AutoMigration(from = 1, to = 2),
        AutoMigration(from = 2, to = 3),
        AutoMigration(from = 3, to = 4)   // NOVÉ
    ]
)
```

**SQL (generuje Room automaticky)**:
```sql
ALTER TABLE user_element ADD COLUMN userId TEXT DEFAULT NULL;
```

**Ostatné tabuľky**: Nezmenené. `WeightEntity`, `EventValueEntity`, `EventDayEntity`, `IndexDailyEntity` — všetky zostávajú na verzii 3 schémy.

---

## Vzťahy entít

```
EntityNode (YAML/in-memory, nie DB)
  └── key: String (PK)
  ├── parent: String? → FK na iný EntityNode.key
  └── impact: Int? (null = group, 1 = positive, -1 = negative)

UserElementEntity (DB: user_element)
  └── id: Long PK autoGenerate
  ├── key: String (unique pre daného userId)
  ├── parent: String? → logicky odkazuje na EntityNode.key alebo iný UserElementEntity.key
  └── userId: String? (null = single-user MVP; non-null = future multi-user)

WeightEntity (DB: weight) — NEZMENENÉ
  └── elementKey → odkazuje na EntityNode.key alebo UserElementEntity.key

EventValueEntity (DB: event_value) — NEZMENENÉ
  └── elementKey → odkazuje na EntityNode.key alebo UserElementEntity.key
```

---

## Miesta v kóde — Migration Guide

| Starý prístup | Nový prístup |
|---------------|--------------|
| `elementConfig.categories` | `entityConfig.groupNodes` alebo `entityConfig.nodes` |
| `elementConfig.elements` | `entityConfig.trackableNodes` |
| `elementConfig.elements.keys` | `entityConfig.trackableKeys` |
| `elementConfig.negativeKeys` | `entityConfig.negativeKeys` (rovnaké) |
| `elementConfig.positiveKeys` | `entityConfig.positiveKeys` (rovnaké) |
| `elementConfig.categories[key]` | `entityConfig.nodes[key]` |
| `elementConfig.elements[key]` | `entityConfig.nodes[key]` (ak `impact != null`) |
| `Category(key, label, clickable, weight)` | `EntityNode(key, weight, null, null, label, true, null, clickable)` |
| `Element(key, weight, impact, parent, desc, active, scale)` | `EntityNode(key, weight, impact, parent, desc, active, scale, false)` |

**Postihnuté súbory**:
1. `domain/model/ElementConfig.kt` — **REWRITE** (Category + Element + ElementConfig → EntityNode + EntityConfig)
2. `data/EntityConfigLoader.kt` — **REWRITE** (parsuje `nodes:` sekciu)
3. `domain/logic/IndexCalculator.kt` — **MODIFY** (trackable parent logika)
4. `data/TrackerRepository.kt` — **MODIFY** (3 miesta)
5. `ui/TrackerViewModel.kt` — **MODIFY** (2 miesta)
6. `ui/EntityManagementViewModel.kt` — **MODIFY** (1 miesto)
7. `ui/screens/EntityBarChart.kt` — **MODIFY** (2 miesta)
8. `ui/screens/EntityManagementScreen.kt` — **MODIFY** (3 miesta)
9. `ui/screens/InfoScreen.kt` — **MODIFY** (2 miesta)
10. `notifications/NotificationWorker.kt` — **MODIFY** (1 miesto)
11. `MainActivity.kt` — **MODIFY** (1 miesto)
12. `data/Entities.kt` — **MODIFY** (UserElementEntity.userId)
13. `data/AppDatabase.kt` — **MODIFY** (version + AutoMigration)
14. `assets/entities.yaml` — **REWRITE** (nový `nodes:` formát)
