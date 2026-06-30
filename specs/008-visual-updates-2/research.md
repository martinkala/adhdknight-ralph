# Research: Visual Updates 2

**Feature**: 008-visual-updates-2
**Date**: 2026-06-29

---

## Decision 1: Double Bar Chart — knižnica vs. vlastný Compose layout

**Decision**: Vlastný Compose `Canvas` + `Row/Column` layout bez externej knižnice

**Rationale**: Constitution §VII zakazuje nové závilosti (dependencies). Existujúci `DualBarChart` v TrendScreen.kt už dokazuje, že `Canvas`-based prístup je použiteľný a stačí na horizontálne/vertikálne stĺpce s labelmi.

**Alternatives considered**:
- `MPAndroidChart` — externe, zakázané constitution
- Vico chart library — externe, zakázané constitution
- Vlastný Canvas — zvolené ✅

**Implementation note**: Nový súbor `screens/EntityBarChart.kt` s composable `EntityDoubleBarChart(entities, elementConfig, modifier)`. Hodnoty normalizované voči maximálnej efektívnej hodnote v sete. Horizontálny layout: ľavá strana (záporné, červené) + pravá strana (pozitívne, zelené). Vertikálne stĺpce v každej strane zoradené podľa veľkosti hodnoty.

---

## Decision 2: Prístup k elementConfig v HomeScreen a VectorScreen

**Decision**: Vystaviť `elementConfig: ElementConfig` ako property na `HomeViewModel` a `VectorViewModel` (delegát na `repository.elementConfig`)

**Rationale**: `repository.elementConfig` je už `public val` (feature 007). Exposing it through the ViewModel je clean MVVM — screen dostane celý kontext cez ViewModel bez priameho prístupu na Repository.

**Alternatives considered**:
- Pasovanie `elementConfig` cez `remember {}` v MainActivity priamo do composable — obchádza ViewModel layer
- Nový ViewModel pre chart — overkill pre jednoduchú read-only property

**Implementation note**:
```kotlin
// HomeViewModel.kt
val elementConfig: ElementConfig get() = repository.elementConfig
// VectorViewModel.kt  
val elementConfig: ElementConfig get() = repository.elementConfig
```

---

## Decision 3: TrendScreen zoradenie (FR-003)

**Decision**: Odstrániť `.reversed()` z `TrendViewModel.refresh()` pre `series` a `dualSeries`

**Rationale**: `getLatestDailySeries(n)` a `getLatestDualIndexSeries(n)` používajú `ORDER BY date DESC` (alebo ekvivalent) podľa konvencie "Latest" prefix v repozitári. `.reversed()` teda mení DESC → ASC (= najstarší navrchu), čo je opak toho čo chceme. Ak je DB query ASC, stačí nereverzovať a priradiť priamo.

**Verification task**: Pri implementácii T003 skontrolovať `DailyIndexDao` query sort order a upraviť podľa toho (buď odobrať `.reversed()` alebo nechať bez zmeny ak query je už ASC).

---

## Decision 4: ElementUiState rozšírenie o impact (FR-006)

**Decision**: Pridať `impact: Int` pole do `ElementUiState` data class

**Rationale**: TrackerScreen potrebuje farbu pozadia per-sekcia. Farba závisí od `impact` z EntityConfig. Najčistejší spôsob je preniesť ju cez existujúci `ElementUiState` (ktorý je už build-time objekt zostavený z `elementConfig`).

**Implementation note**: `buildElementList()` v `TrackerViewModel` pridá `impact = el.impact` pri konštrukcii `ElementUiState`. TrackerScreen číta `element.impact` a odvodí farbu.

---

## Decision 5: Farby pre pastelové pozadie

**Decision**: Material3-kompatibilné pastelové farby s nízkym alpha

| Použitie | Farba | Hex |
|----------|-------|-----|
| Pozitívne pozadie (+1) | bledozelená | `Color(0x1A4CAF50)` (alpha 10%) |
| Negatívne pozadie (-1) | bledočervená | `Color(0x1AF44336)` (alpha 10%) |
| Trend ≥ 50 (dobrý deň) | bledozelená | `Color(0x1A4CAF50)` |
| Trend < 50 (zlý deň) | bledočervená | `Color(0x1AF44336)` |

**Rationale**: Alpha 10% (0x1A) je dostatočne viditeľné bez toho aby zasahovalo do čitateľnosti textu na svetlej aj tmavej téme. Material3 `containerColor` na kartách bude pozmenená pre dotknuté karty.

---

## Decision 6: Druhé tlačidlo Uložiť (FR-005)

**Decision**: Extrahovať save logiku do `val onSave: () -> Unit = { ... }` lambda v rámci composable, a reusovať ju pre obidve tlačidlá

**Rationale**: Identická logika, dve miesta. Lambda extrakcia je štandardný Compose pattern — zabraňuje duplikácii bez zavádzania novej abstrakcie.

---

## Decision 7: HomeScreen kompaktné metriky (FR-007)

**Decision**: Nahradiť 2-riadkové zobrazenie (ADHD index samostatne, potom Spokojnosť + Splnené) jednou `Row` so 3 `Column` blokmi s `weight(1f)` rozdelením

**Rationale**: Šetrí 1 celý riadok. Všetky 3 hodnoty majú rovnaký typ zobrazenia (label + hodnota), takže symetrický layout je prirodzený.

---

## Constraints from Constitution

- §VII: **No new dependencies** — všetky grafy sú Compose-native
- §VIII: **MVVM pattern** — elementConfig sa prenáša cez ViewModel
- §XI: **Offline-first** — žiadna sieťová komunikácia, iba lokálne dáta
- §Testy: Vizuálne zmeny nevyžadujú nové unit testy (čisto UI vrstva). Existujúce testy nesmú regresovať.
