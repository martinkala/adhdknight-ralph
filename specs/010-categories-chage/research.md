# Research: Unified Entity Tree (010-categories-chage)

**Date**: 2026-06-30 | **Plan**: [plan.md](plan.md)

Tento dokument obsahuje všetky technické rozhodnutia (D1–D5) potrebné pre implementáciu. Všetky pôvodné NEEDS CLARIFICATION boli vyriešené analýzou existujúceho kódu.

---

## D1: Naming collision — `sleep` kategória vs `sleep` element

**Problém**: V aktuálnom YAML existuje `categories.sleep` (display "Spánok") a súčasne `elements.sleep` (display "Kvalitný spánok", `parent: sleep`). V jednotnom `nodes:` namespace by YAML duplikoval kľúč `sleep`.

**Rozhodnutie**: Kľúč `sleep` sa zachová pre skupinu/parent node. Element `sleep` (child) sa **odstráni** — jeho atribúty (`impact: 1`, `active: true`) sa presunú do rodičovského uzla `sleep`. Rovnaké riešenie pre `physical_activity`.

- `nodes.sleep` → `label: "Spánok"`, `weight: 15.0`, `impact: 1`, `active: true`, `clickable: true`
- `nodes.physical_activity` → `label: "Fyzická aktivita"`, `weight: 11.0`, `impact: 1`, `active: true`, `scale: [1,2,3,4,5]`, `clickable: true`

**Dôsledok**: `WeightEntity` a `EventValueEntity` používajú kľúče `sleep`, `physical_activity` — tieto sa v DB **nemenia**. Existujúce záznamy ostávajú platné.

**Alternatíva odmietnutá**: Premenovanie childov na `sleep_quality`, `physical_activity_activity` — zbytočne rozbíja existujúce `EventValueEntity` záznamy v DB.

---

## D2: YAML sekcia — `nodes:` nahrádza `categories:` + `elements:`

**Rozhodnutie**: Nová sekcia v `entities.yaml` sa volá `nodes:`. Stará dvojitá štruktúra (`categories:` + `elements:`) je odstránená.

**`EntityConfigLoader` fallback**: Ak YAML obsahuje len `categories:` a `elements:` (stará verzia), loader vráti `buildFallback()`. Toto je akceptovateľné pretože assets sa aktualizujú spolu s APK.

**Nový YAML formát**:
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
    
  lifestyle:
    label: "Životný štýl"
    weight: 42.0
    # impact je null → non-trackable group
    
  stress_work:
    label: "Pracovný stres"
    weight: 13.0
    impact: -1
    parent: lifestyle
    active: true
    scale: [1, 2, 3, 4, 5]
```

---

## D3: Kotlin dátový model — `EntityNode` + `EntityConfig`

**Rozhodnutie**: `Category` a `Element` sa zlúčia do `EntityNode`. `ElementConfig` sa prepíše ako `EntityConfig`.

```kotlin
data class EntityNode(
    val key: String,
    val weight: Double,
    val impact: Int?,          // null → non-trackable group
    val parent: String?,
    val label: String,         // display name (was Category.label; for tracked nodes = description)
    val active: Boolean,
    val scale: List<Int>?,
    val clickable: Boolean     // default false
)

data class EntityConfig(
    val nodes: Map<String, EntityNode>
) {
    val negativeKeys: Set<String>
        get() = nodes.values.filter { it.impact == -1 && it.active }.map { it.key }.toSet()
    val positiveKeys: Set<String>
        get() = nodes.values.filter { it.impact == 1 && it.active }.map { it.key }.toSet()
    val trackableNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact != null && it.value.active }
    val groupNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact == null }
}
```

**Backward compat pre `IndexCalculator`**:
- `elementConfig.categories[catKey]` → `entityConfig.nodes[catKey]` (group nodes fungujú ako staré categories)
- `elementConfig.elements.values` → `entityConfig.trackableNodes.values`
- `elementConfig.negativeKeys` → `entityConfig.negativeKeys` (computed property, rovnaká logika)

**Súbor**: `ElementConfig.kt` sa **prepíše** — existujúci súbor zostáva (mení sa obsah). Názov súboru sa nezmení kvôli zachovaniu git histórie.

---

## D4: `IndexCalculator.computeDailyIndexGrouped` — logika po zmene

**Aktuálna logika** (zachovaná sémantika):
1. Root elements (`parent == null`) → priame príspevky
2. Category groups → `group_weighted_avg × categoryNode.weight`

**Nová logika** (mierne rozšírená pre trackable parents):

```
For each active trackable node:
  if node.parent == null:
    # Root node — two sub-cases:
    activeChildren = trackableNodes.filter { it.parent == node.key && it.key in activeKeys }
    if activeChildren.isNotEmpty():
      # Children take priority — compute group avg × node.weight
      groupAvg = weighted_avg(activeChildren)
      totalContribution += groupAvg * node.weight
      totalWeight += node.weight
    else:
      # Node itself is directly tracked
      v = valueMap[node.key] ?: skip
      effective = if (node.impact < 0) 1.0 - v.valueEffective else v.valueEffective
      totalContribution += node.weight * effective
      totalWeight += node.weight
  else:
    # Child node — handled by parent's group calculation above
    skip (already counted)
    
For each group node (impact == null) that has active children:
  groupAvg = weighted_avg(activeChildren)
  totalContribution += groupAvg * groupNode.weight
  totalWeight += groupNode.weight
```

**Kľúčový invariant**: Uzol (`sleep`) ktorý má `impact` ale **nemá aktívnych potomkov** → prispieva priamo (binárne). Uzol (`sleep`) ktorý má `impact` A **má aktívnych potomkov** → potomkovia preberajú jeho váhu (group avg).

---

## D5: `userId` v `UserElementEntity` — Room AutoMigration 3→4

**Rozhodnutie**: Pridať `val userId: String? = null` do `UserElementEntity`.

**Room AutoMigration**: Room 2.6.1 (používaný v projekte) podporuje automatickú migráciu pre pridanie nullable stĺpca. Stačí `AutoMigration(from = 3, to = 4)` v `@Database`.

**SQL ekvivalent** (Room generuje automaticky):
```sql
ALTER TABLE user_element ADD COLUMN userId TEXT DEFAULT NULL;
```

**Žiadna špeciálna `@RenameColumn` alebo `AutoMigrationSpec`** nie je potrebná — štandardná nullable column addition.

---

## Súhrn rozhodnutí

| ID | Rozhodnutie | Alternatíva odmietnutá |
|----|-------------|----------------------|
| D1 | `sleep`/`physical_activity` mergeované do root trackable node | Premenovanie child elementov |
| D2 | YAML sekcia `nodes:` | Zachovanie dual `categories:`+`elements:` |
| D3 | `EntityNode` + `EntityConfig` v `ElementConfig.kt` | Nový súbor, alebo zachovanie oboch tried |
| D4 | Trackable parent node: ak má deti → group avg; bez detí → priame | Vždy group avg (nedefinované ak nie sú deti) |
| D5 | AutoMigration 3→4, nullable `userId` | Manual migration, alebo `@ColumnInfo(defaultValue)` |
