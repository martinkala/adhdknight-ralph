# Data Model: Visual Update 03

**Date**: 2026-06-30 | **Feature**: 011-visual-update-03

---

## Existujúce entity (bez zmeny DB schémy)

Táto feature nemení žiadnu Room DB entitu ani schémy. Všetky potrebné dáta sú dostupné v existujúcich tabuľkách.

| Room entita | Relevantné polia | Použitie v tejto feature |
|-------------|-----------------|--------------------------|
| `EventDayEntity` | `id`, `date` (ISO string) | Filter pre date-scoped queries (US1, US5) |
| `EventValueEntity` | `eventDayId`, `elementKey`, `valueBinary`, `valueScale`, `valueEffective` | Zdroj dát pre BarChart, PieChart, auto-save (US2, US3, US4) |
| `IndexDailyEntity` | `eventDayId`, `indexValue`, `positiveIndex`, `negativeIndex` | Date-scoped index pre Home (US1, US5) |
| `SatisfactionEntity` | `eventDayId`, `valueScale` | Date-scoped spokojnosť pre Home (US1, US5) |
| `WeightEntity` | `elementKey`, `weightDefault`, `weightPersonal` | Váhy pre Info obrazovku (US6) a weight text v bare (US3) |
| `UserElementEntity` | `key`, `weight`, `impact`, `parentCategory`, `description`, `scale`, `isActive` | User-defined entity pre Tracker merge (US8) |

---

## Nové in-memory modely (UI layer)

### `BarRow` (zobrazenie v EntityDoubleBarChart)

Nový data class v `EntityBarChart.kt` — žiadna DB perzistencia.

```
BarRow(
  negEntry: BarEntry?,      // null = žiadna negatívna entita pre tento riadok
  posEntry: BarEntry?       // null = žiadna pozitívna entita pre tento riadok
)
```

**Vzťah na existujúce**: `BarEntry` je rozšírený o `categoryKey: String?` a `weight: Double` (z `Element.weight`).

### `PlaceholderBarChart` (in-memory kompozičné dáta)

Konštanty definované priamo v composable funkci — žiadna trieda ani DB:
- Ľavé bary: frakcie `[0.30f, 0.60f, 0.45f]`
- Pravé bary: frakcie `[0.50f, 0.35f, 0.65f]`
- Farba: `Color(0xFFD0D0D0)` (svetlosivá)

---

## Nové Repository metódy (bez DB schémy zmien)

Nasledujúce metódy budú pridané do `TrackerRepository.kt`. Sú len nové query metódy na existujúcich tabuľkách — žiadna DB migrácia nie je potrebná.

| Metóda | DAO dotaz | Použitie |
|--------|----------|---------|
| `getIndexForDate(date: String): Double?` | `eventDayDao.getByDate(date)` → `indexDao.getByDayId(dayId)` | US1, US5 |
| `getSatisfactionForDate(date: String): Int?` | `eventDayDao.getByDate(date)` → `satisfactionDao.getByDayId(dayId)` | US1, US5 |
| `getSubIndicesForDate(date: String): Pair<Double?, Double?>` | z `IndexDailyEntity` cez `eventDayId` | US1, US5 |
| `getCompletionCountsForDate(date: String): Pair<Int, Int>?` | count `EventValueEntity` pre daný deň | US1, US5 |
| `getAllEventDates(): List<String>` | `eventDayDao.getAllDates()` ORDER BY date DESC | US5 |

---

## Zmeny schémy

**Žiadne.** `DB_VERSION` zostáva nezmenená. Žiadna migrácia nie je potrebná.

---

## ElementConfig vzťahy (in-memory, z YAML)

```
ElementConfig
├── categories: Map<String, Category>
│   ├── Category(key, label, clickable, weight)  ← category.weight pre výpočet indexu
│   └── ...
└── elements: Map<String, Element>
    ├── Element(key, weight, impact, parent?, description, active, scale?)
    │   ↑ parent: String? → referencuje categories[parent].key
    └── ...
```

**Kategórie a ich prvky** (z YAML, bez zmeny):
- Root elements (`parent == null`): napr. `sleep`, `physical_activity`, `overall_feeling`, `mindfulness`
- Categorized elements (`parent != null`): napr. `stress_work`, `stress_personal` → parent: `stress`; `nutrition_protein` → parent: `nutrition`

**Groupovanie pre BarRow** (US3): Entity sa zoskupia podľa `element.parent`. Každá kategória produkuje zoznam riadkov kde neg[i] a pos[i] z tej istej kategórie sú spárované. Nekategorizované entity sú standalone riadky.
