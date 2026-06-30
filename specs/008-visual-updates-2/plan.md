# Implementation Plan: Visual Updates 2

**Branch**: `008-visual-updates-2` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-visual-updates-2/spec.md`

## Summary

Sedem vizuálnych vylepšení Android ADHD Tracker app: nahradenie radar grafu novým `EntityDoubleBarChart` (HomeScreen + VectorScreen), zoradenie TrendScreen zostupne s farebnými riadkami, druhé tlačidlo Uložiť deň v TrackerScreen, pastelové farby sekcií podľa impactu, kompaktné metriky na HomeScreen, odstránenie "Tip dňa" a premenovanie VectorScreen titulku. Všetky zmeny sú čisto v UI/Compose vrstve — žiadna zmena databázy ani Repository.

## Technical Context

**Language/Version**: Kotlin 1.9 / JVM 17

**Primary Dependencies**: Jetpack Compose (Material3), AndroidX ViewModel — žiadne nové závislosti

**Storage**: Room DB v3 — nezmenená

**Testing**: JUnit4 + androidTest — UI zmeny nevyžadujú nové unit testy; existujúce testy nesmú regresovať

**Target Platform**: Android min SDK 26, target SDK 34

**Project Type**: Mobile app (Android)

**Performance Goals**: 60fps scroll — Compose-native layout bez externých grafov

**Constraints**: No new dependencies (§VII constitution); MVVM pattern (§VIII); offline-first (§XI)

**Scale/Scope**: 7 UI obrazoviek, 8 súborov dotknutých, ~300 riadkov kódu

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princíp | Status | Poznámka |
|---------|--------|----------|
| §VII No new dependencies | ✅ PASS | EntityBarChart je Compose-native Canvas/Row |
| §VIII MVVM pattern | ✅ PASS | elementConfig exponovaný cez ViewModel |
| §XI Offline-first | ✅ PASS | Žiadna sieťová komunikácia |
| §Testy unit coverage | ✅ PASS | Čisto UI vrstva, doménová logika nezmenená |

**Post-design re-check**: ✅ PASS — design artifacts neporušujú žiadny constitution princíp.

## Project Structure

### Documentation (this feature)

```text
specs/008-visual-updates-2/
├── plan.md              # Tento súbor
├── spec.md              # Špecifikácia
├── research.md          # Výskum a rozhodnutia
├── data-model.md        # Dátový model a zmeny štruktúr
├── quickstart.md        # Validačné scenáre
├── contracts/
│   └── ui-contracts.md  # UI composable kontrakty
├── checklists/
│   └── requirements.md  # Kontrolný zoznam kvality
└── tasks.md             # (generované /speckit-tasks)
```

### Source Code (repository root)

```text
android_app/app/src/main/java/com/example/madhdtracker/
├── ui/
│   ├── HomeViewModel.kt          # pridať elementConfig property
│   ├── VectorViewModel.kt        # pridať elementConfig property
│   ├── TrackerViewModel.kt       # ElementUiState + impact field; buildElementList update
│   └── screens/
│       ├── EntityBarChart.kt     # NOVÝ súbor — EntityDoubleBarChart + BarEntry
│       ├── HomeScreen.kt         # nahradiť RadarChart; kompaktné metriky; odstrániť Tip dňa
│       ├── VectorScreen.kt       # nahradiť RadarChart; premenovať titulok
│       ├── TrackerScreen.kt      # impact farby; 2. tlačidlo Uložiť
│       └── TrendScreen.kt        # zoradenie; farebné riadky
```

**Structure Decision**: Jednoduchý single-project Android, Option 3 z template. Nový súbor `EntityBarChart.kt` je lokalizovaný do `screens/` package — zodpovedá vzoru ostatných chart súborov (`RadarChart.kt`).

## Phase 0: Research

**Status**: ✅ COMPLETE — viď [research.md](research.md)

Kľúčové rozhodnutia:
1. Compose-native `Canvas` + `Row` pre EntityDoubleBarChart — žiadna externá knižnica
2. `elementConfig` exponovaný ako property na HomeViewModel a VectorViewModel
3. TrendScreen sort: overiť a upraviť `.reversed()` v TrendViewModel podľa DB query order
4. `ElementUiState.impact: Int` nové pole pre TrackerScreen farebné sekcie
5. Pastelové farby: `Color(0x1A4CAF50)` zelená, `Color(0x1AF44336)` červená (alpha 10%)

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

Artefakty:
- [data-model.md](data-model.md) — BarEntry, ElementUiState rozšírenie, ovplyvnené súbory
- [contracts/ui-contracts.md](contracts/ui-contracts.md) — Composable kontrakty pre všetky dotknuté obrazovky
- [quickstart.md](quickstart.md) — 6 validačných scenárov + regresné overenie

## Implementation Order (pre tasks.md)

| Priorita | US | Popis | Závislosti |
|----------|----|-------|------------|
| P1 | US1 | EntityDoubleBarChart (HomeScreen + VectorScreen) | Žiadne |
| P1 | US2 | TrendScreen sort + farebné riadky | Žiadne |
| P2 | US4 | TrackerScreen: ElementUiState.impact + farby sekcií | Žiadne |
| P2 | US3 | TrackerScreen: 2. tlačidlo Uložiť | Žiadne |
| P2 | US5 | HomeScreen: kompaktné metriky + premenovanie | Žiadne |
| P3 | US6 | Odstrániť Tip dňa z HomeScreen | Žiadne |
| P3 | US7 | VectorScreen: premenovať titulok | Závisí na US1 (ten súbor) |

Všetky user stories sú vzájomne nezávislé (rôzne súbory). US7 je v tom istom súbore ako US1 — implementovať v jednom prechode.
