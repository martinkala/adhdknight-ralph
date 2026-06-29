# Data Model: Configurable Entities

**Feature**: 007-comfigurable-entities  
**Date**: 2026-06-29

---

## Domain Entities

### Category (YAML config — systémovo definovaná, nemenná)

Definuje top-level zoskupenie entít. Definovaná výlučne v `entities.yaml`, nie editovateľná používateľom.

| Pole | Typ | Povinné | Popis |
|------|-----|---------|-------|
| `key` | String | ✓ | Unikátny identifikátor (napr. `physical_activity`) |
| `label` | String | ✓ | Zobrazovaný názov |
| `clickable` | Boolean | ✓ | Či je kategória sama o sebe sledovateľná entita |
| `weight` | Double | ✓ | Celkový budget kategórie v indexe (suma príspevkov jej sub-entít) |

**Validácia**: `weight > 0`, `key` unikátny v rámci celého configu

---

### Element (YAML config — systémové entity)

Sledovateľná entita zaradená pod kategóriu. Definovaná v `entities.yaml`.

| Pole | Typ | Povinné | Popis |
|------|-----|---------|-------|
| `key` | String | ✓ | Unikátny identifikátor (napr. `sleep`, `pushups`) |
| `weight` | Double | ✓ | Relatívna váha v rámci rodičovskej kategórie |
| `impact` | Int | ✓ | `+1` (pozitívny) alebo `-1` (negatívny) — riadi inverziu pri výpočte |
| `parent` | String? | ○ | Key rodičovskej kategórie; `null` pre root entity (iba `overall_feeling`) |
| `description` | String | ○ | Opis pre UI |
| `active` | Boolean | ✓ | Defaultný stav aktívnosti (môže byť prepísaný user overridom) |
| `scale` | List\<Int\>? | ○ | Hodnoty škály napr. `[1,2,3,4,5]`; `null` = binárna entita (checkbox) |

**Validácia**: `weight > 0`, `impact` ∈ {+1, -1}, `scale` hodnoty unikátne a vzostupné, `parent` musí existovať v categories alebo byť null

---

### UserElementOverride (Room DB — user-level override)

Používateľom nastavený stav aktívnosti pre systémové entity.

| Pole | Typ | Popis |
|------|-----|-------|
| `elementKey` | String (PK) | Odkazuje na `Element.key` |
| `isActive` | Boolean | User override; ak záznam neexistuje, použije sa `Element.active` |

**Room Entity**: `user_element_override`

---

### UserElement (Room DB — user-defined entity) [US4 / P3]

Vlastná entita definovaná používateľom. Ukladá sa do DB, nie do YAML.

| Pole | Typ | Povinné | Popis |
|------|-----|---------|-------|
| `id` | Long (PK) | ✓ | Auto-generate |
| `key` | String | ✓ | Unikátny identifikátor; nesmie kolidovať so systémovými kľúčmi |
| `weight` | Double | ✓ | Váha v rámci rodičovskej kategórie |
| `impact` | Int | ✓ | +1 alebo -1 |
| `parentCategory` | String | ✓ | Key existujúcej top-level Category |
| `description` | String? | ○ | Voliteľný opis |
| `scale` | String? | ○ | JSON-encoded list napr. `"[1,2,3,4,5]"` |
| `isActive` | Boolean | ✓ | Default true |

**Room Entity**: `user_element`

---

### ElementConfig (in-memory — parsed result)

Výsledok načítania `entities.yaml` pri štarte aplikácie.

```kotlin
data class ElementConfig(
    val categories: Map<String, Category>,  // key → Category
    val elements: Map<String, Element>,     // key → Element (systémové)
    val userElements: List<UserElement>     // z DB (pridávané v runtime)
)
```

---

## Hierarchia a vzťahy

```
ElementConfig
├── Category: sleep (weight: 15.0, clickable: true)
│   └── Element: sleep (weight: 15.0, impact: +1)
├── Category: physical_activity (weight: 11.0, clickable: true)
│   ├── Element: physical_activity (weight: 11.0, impact: +1) ← leaf (MVP)
│   └── [budúce sub-entity: pushups, running, ...]
├── Category: lifestyle (weight: 42.0, clickable: false)
│   ├── Element: stress_work (weight: 13.0, impact: -1)
│   ├── Element: stress_personal (weight: 13.0, impact: -1)
│   ├── Element: caffeine (weight: 6.0, impact: -1)
│   └── Element: alcohol (weight: 10.0, impact: -1)
├── Category: head (weight: 11.0, clickable: false)
│   └── Element: mindfulness (weight: 11.0, impact: +1)
├── Category: food (weight: 8.0, clickable: false)
│   └── Element: nutrition_protein (weight: 8.0, impact: +1)
└── Root (no parent)
    └── Element: overall_feeling (weight: 13.0, impact: +1) ← špeciálna
```

---

## Index Calculation s FR-006

Pre každú kategóriu:

```
group_avg = Σ(active_element.weight × effective_value) / Σ(active_element.weight)
category_contribution = group_avg × category.weight

// overall_feeling je root — prispieva priamo, nie cez kategóriu
```

Celkový index:
```
numerator = Σ(category_contribution) + overall_feeling_contribution
denominator = Σ(active_category.weight) + overall_feeling.weight
index = (numerator / denominator) × 100
```

---

## Migrácia z AppConfig.weights

| Fáza | Stav |
|------|------|
| Tento PR | `EntityConfig` pridaný, `TrackerRepository` dostáva oba (AppConfig + EntityConfig); váhy sa berú z EntityConfig |
| Budúci PR | `AppConfig.weights` sekcia deprecated, `DefaultWeights.kt` odvodený z EntityConfig |
