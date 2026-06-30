# Implementation Plan: Unified Entity Tree (010-categories-chage)

**Branch**: `010-categories-chage` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-categories-chage/spec.md`

---

## Summary

Zlúčenie dátových štruktúr `Category` a `Element` do jednej triedy `EntityNode` s jednotným YAML formátom (`nodes:` sekcia). Každý uzol môže byť skupina (bez `impact`), list (s `impact`, priamo sledovateľný) alebo trackable parent (s `impact` aj potomkami). `computeDailyIndexGrouped` ostáva funkčne ekvivalentný. `UserElementEntity` dostáva nullable `userId` pre multi-user readiness (Room AutoMigration 3→4).

---

## Technical Context

**Language/Version**: Kotlin JVM 17

**Primary Dependencies**: Jetpack Compose BOM 2024.06.00, Room 2.6.1, SnakeYAML 2.2, KSP (Room codegen)

**Storage**: Room SQLite — DB version 3 → 4 (AutoMigration, additive only)

**Testing**: JUnit 4 (unit testy IndexCalculator a EntityConfigLoader)

**Target Platform**: Android min SDK 26, target SDK 34

**Project Type**: Mobile app (Android/Kotlin/Compose)

**Performance Goals**: Config načítanie < 200ms; DB AutoMigration bez stratety dát

**Constraints**:
- Offline-first (§I Constitution)
- Numerická ekvivalentnosť výpočtu indexu pre existujúce dáta (SC-002)
- Žiadny DI framework (§VII)
- Room AutoMigration — žiadne deštrukívne zmeny DB

**Scale/Scope**: ~15 systémových uzlov + N user-defined; single-user MVP, multi-user userId placeholder

---

## Constitution Check

| Princíp | Stav | Poznámka |
|---------|------|---------|
| §I — MVVM + Repository | ✅ PASS | Zmeny sú v domain model + loader; MVVM vrstvy zachované |
| §II — Index výpočet NON-NEGOTIABLE | ✅ PASS | `computeDailyIndexGrouped` ostáva ekvivalentné; root/child logika sa nemení, len zdroj dát |
| §III — DB schéma | ✅ PASS | Migrácia 3→4 additive (nullable `userId`); ostatné tabuľky nezmenené |
| §IV — UX / minimálne trenie | ✅ PASS | Tracker UI ostáva identické; zmena je pod kapotou |
| §V — Notifikácie | ✅ PASS | NotificationRules dostáva `entityConfig.trackableKeys` namiesto `elementConfig.elements.keys` |
| §VI — Testy | ⚠️ REQUIRED | `EntityConfigLoader` + `IndexCalculator` MUST mať unit testy pokrývajúce zjednoteený model |
| §VII — Závislosti | ✅ PASS | Žiadna nová závislosť |

**Gate: PASS** — pokračujeme do Phase 0 a Phase 1.

---

## Kľúčové technické rozhodnutia (výstupy Phase 0)

### D1: Naming collision resolution — `sleep` kategória vs `sleep` element

**Problém**: Aktuálny YAML má `categories.sleep` (skupina „Spánok") aj `elements.sleep` (leaf „Kvalitný spánok" s `parent: sleep`). V jednotnom `nodes:` namespace by došlo ku kolízii kľúčov.

**Rozhodnutie**: Kategória `sleep` pohltí atribúty elementu `sleep` — stane sa priamo trackable root node. Rovnako pre `physical_activity`. Ostatné kategórie (`lifestyle`, `head`, `food`, `organisation`) ostávajú skupiny bez `impact` (nie sú priamo trackovateľné).

**Dôsledok**: Z YAML sa odstraňujú `elements.sleep` a `elements.physical_activity`; ich atribúty (`impact`, `description`, `active`, `scale`) sa presúvajú na zodpovedajúce `nodes.sleep` a `nodes.physical_activity`. `WeightEntity` zachová `element_key = "sleep"` bez zmeny.

**Alternatíva odmietnutá**: Premenovanie na `sleep_quality`, `physical_activity_session` — zbytočne mení `element_key` a rozbíja existujúce `EventValueEntity` záznamy.

---

### D2: YAML sekcia — `nodes:` vs zachovanie `categories:` + `elements:`

**Rozhodnutie**: Nová sekcia `nodes:` nahrádza obe sekcie. Starý `EntityConfigLoader` dostane fallback pre prípad, že súbor ešte nebol aktualizovaný.

**Dôsledok**: `entities.yaml` sa prepíše; `EntityConfigLoader.parse()` číta `nodes:` sekciu primárne, fallback na starý formát zachováva spätú kompatibilitu pri prvom spustení po update.

---

### D3: Kotlin dátový model — jedna trieda vs dve

**Rozhodnutie**: `Category` + `Element` sa zlúčia do `EntityNode`. `ElementConfig` sa premenuje na `EntityConfig` (obsahuje `nodes: Map<String, EntityNode>`). Zachovajú sa computed properties `negativeKeys`, `positiveKeys`, `trackableNodes`.

```kotlin
data class EntityNode(
    val key: String,
    val weight: Double,
    val impact: Int?,          // null → non-trackable group node
    val parent: String?,
    val label: String,         // display name (was Category.label; for elements = description)
    val active: Boolean,
    val scale: List<Int>?,
    val clickable: Boolean     // from old Category; default false for elements
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

**Backward compat v IndexCalculator**: `elementConfig.categories[catKey]` → `entityConfig.nodes[catKey]`; `elementConfig.elements.values` → `entityConfig.trackableNodes.values`.

---

### D4: `IndexCalculator.computeDailyIndexGrouped` — logika po zmene

Aktuálna logika:
1. Root elements (`parent == null`) → priamo
2. Category groups → `group_avg × category.weight`

Po zmene:
1. Trackable root nodes (`parent == null && impact != null`) → priamo
2. Trackable child nodes (`parent != null`) → zoskupené podľa `parent`; `group_avg × parentNode.weight`
3. Trackable parent nodes (`parent == null && impact != null` a zároveň má potomkov) — **nový prípad**: ak parent aj potomkovia sú zapnutí, príspevok parent node sa nahrádza váženým priemerom potomkov (potomkovia majú prioritu nad priamou hodnotou parenta).

```
if node.parent == null && node.impact != null:
    children = trackableNodes.filter { it.parent == node.key }
    if children.any { it.key in activeKeys }:
        → use weighted avg of active children × node.weight
    else:
        → use node's own valueEffective × node.weight
```

---

### D5: `userId` v `UserElementEntity` — Room AutoMigration 3→4

**Rozhodnutie**: Pridať `val userId: String? = null` do `UserElementEntity`. Room AutoMigration 3→4 zvládne nullable stĺpec bez špeciálneho `@RenameColumn` — stačí `AutoMigration(from = 3, to = 4)`.

---

## Project Structure

### Documentation (this feature)

```text
specs/010-categories-chage/
├── plan.md              # Tento súbor
├── research.md          # D1–D5 rozhodnutia (výstup Phase 0)
├── data-model.md        # EntityNode, EntityConfig, migrácia 3→4
├── quickstart.md        # Validačné scenáre
└── tasks.md             # Generovaný /speckit-tasks
```

### Source Code — dotknuté súbory

```text
android_app/app/src/main/assets/
└── entities.yaml                             # MODIFIED: nodes: sekcia

android_app/app/src/main/java/com/example/madhdtracker/
├── domain/model/
│   ├── ElementConfig.kt                      # MODIFIED: Category+Element → EntityNode, ElementConfig → EntityConfig
│   └── (ElementConfig.kt ostáva ako súbor, obsah sa mení)
├── data/
│   ├── EntityConfigLoader.kt                 # MODIFIED: parsuje nodes: sekcia
│   ├── Entities.kt                           # MODIFIED: UserElementEntity + userId
│   └── AppDatabase.kt                        # MODIFIED: version 3→4, AutoMigration
├── domain/logic/
│   └── IndexCalculator.kt                    # MODIFIED: computeDailyIndexGrouped nová logika pre trackable parents
├── ui/
│   ├── TrackerViewModel.kt                   # MODIFIED: elementConfig.categories.keys → entityConfig.groupNodes.keys
│   ├── EntityManagementViewModel.kt          # MODIFIED: elements → trackableNodes
│   └── screens/
│       ├── EntityBarChart.kt                 # MODIFIED: elementConfig.categories → entityConfig.nodes
│       ├── EntityManagementScreen.kt         # MODIFIED: kategórie z entityConfig.groupNodes
│       └── InfoScreen.kt                     # MODIFIED: unified iterácia cez entityConfig.nodes
├── data/TrackerRepository.kt                 # MODIFIED: elementConfig → entityConfig refs
├── notifications/NotificationWorker.kt       # MODIFIED: elements.keys → trackableKeys
└── MainActivity.kt                           # MODIFIED: elementConfig.elements.keys → entityConfig.trackableKeys
```

---

## Complexity Tracking

Žiadne constitution violations — žiadny entry potrebný.

---

## Fázový plán

### Phase 0 (Research): D1–D5 ✅ (zahrnuté v tomto dokumente)
Všetky NEEDS CLARIFICATION vyriešené:
- Naming collision: merge do root node
- YAML sekcia: nová `nodes:`
- Kotlin model: `EntityNode` + `EntityConfig`
- IndexCalculator: trackable parent logika
- DB: AutoMigration 3→4

### Phase 1 (Design Artifacts)
- `data-model.md`: EntityNode fields, EntityConfig, DB migration 3→4, UserElementEntity.userId
- `quickstart.md`: validačné scenáre pre SC-001 až SC-006
- AGENTS.md update

### Phase 2 (Tasks)
- `/speckit-tasks` generuje `tasks.md`
