# Data Model: Visual Updates 2

**Feature**: 008-visual-updates-2
**Date**: 2026-06-29

---

## Nové dátové štruktúry (UI-vrstva only)

Žiadna zmena databázy, Room entít ani Repository. Všetky zmeny sú v UI/Compose vrstve.

---

### BarEntry (nová data class)

Reprezentuje jeden stĺpec v `EntityDoubleBarChart`.

```
BarEntry {
  key: String          // kľúč entity (napr. "caffeine")
  label: String        // zobrazovaný text: "Potraviny / Kofeín" alebo iba "Celková spokojnosť"
  value: Double        // normalizovaná hodnota 0.0–1.0
  impact: Int          // +1 alebo -1 (z ElementConfig)
}
```

**Derivácia**: zostavená z `Map<String, EventValueEntity>` + `ElementConfig` v composable.

**Validácia**:
- `value` je `valueEffective` cez `radarValue()` helper, orezaná na [0.0, 1.0]
- Root entity (parent == null a key != "overall_feeling") sa zobrazujú bez parent prefixu
- `overall_feeling` sa vynecháva z barchart (zobrazená samostatne ako Spokojnosť)

---

### ElementUiState (rozšírenie existujúcej)

Existujúca data class v `TrackerViewModel.kt` sa rozšíri o jedno pole:

```
ElementUiState {
  key: String        // (existujúce)
  label: String      // (existujúce)  
  hasScale: Boolean  // (existujúce)
  impact: Int        // NOVÉ — +1 alebo -1 z EntityConfig
}
```

**Derivácia**: `buildElementList()` v TrackerViewModel.companion čerpá `impact` z `elementConfig.elements[key]?.impact ?: 1`.

---

### TrendRow (konceptuálny model — existujúca DailyIndexRow)

Existujúca `DailyIndexRow` sa nemení. Farebné pozadie v TrendScreen sa odvodzuje priamo v Compose composable:

```
rowBackground = if (row.indexValue >= 50.0) Color(0x1A4CAF50) else Color(0x1AF44336)
```

---

## Vzťahy

```
ElementConfig.elements[key]
  └── impact: Int ──────────────────────→ ElementUiState.impact (TrackerScreen colors)
  └── parent: String? ──────────────────→ BarEntry.label prefix (EntityBarChart)
  └── description: String ──────────────→ BarEntry.label suffix

Map<String, EventValueEntity>[key]
  └── valueEffective: Double ───────────→ BarEntry.value (EntityBarChart)

DailyIndexRow.indexValue
  └── >= 50 ? green : red ─────────────→ TrendScreen Card background
```

---

## Ovplyvnené súbory (UI vrstva)

| Súbor | Typ zmeny |
|-------|-----------|
| `ui/TrackerViewModel.kt` | `ElementUiState` + `impact` field; `buildElementList()` update |
| `ui/screens/EntityBarChart.kt` | NOVÝ — `EntityDoubleBarChart` composable + `BarEntry` |
| `ui/screens/HomeScreen.kt` | Nahradiť RadarChart; kompaktné metriky; odstrániť Tip dňa |
| `ui/screens/VectorScreen.kt` | Nahradiť RadarChart; premenovať titulok |
| `ui/screens/TrackerScreen.kt` | Impact farby per sekcia; 2. tlačidlo Uložiť |
| `ui/screens/TrendScreen.kt` | Zoradenie; farebné pozadie riadkov |
| `ui/HomeViewModel.kt` | Pridať `elementConfig` property |
| `ui/VectorViewModel.kt` | Pridať `elementConfig` property |
