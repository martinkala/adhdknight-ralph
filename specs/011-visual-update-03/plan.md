# Implementation Plan: Visual Update 03

**Branch**: `011-visual-update-03` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-visual-update-03/spec.md`

## Summary

8 vizuálnych a UX vylepšení aplikácie ADHD Tracker. Primárne: oprava kritickej chyby kde Home zobrazuje dáta predchádzajúceho dňa (HomeViewModel používa `getLatestXxx()` bez dátumovej filtrácie) + auto-save v Trackeri (eliminuje stratu dát). Sekundárne: vylepšenia dual bar chartu (groupovanie po kategóriách, váha v bare), koláčový graf na VectorScreen, swipe navigácia. Terciárne: Info obrazovka, Home ikona, user entity bug fix.

## Technical Context

**Language/Version**: Kotlin (JVM target 17)

**Primary Dependencies**:
- Jetpack Compose BOM 2024.06.00 (Material3, UI, Navigation Compose)
- Room 2.6.1 + KSP (perzistencia)
- Kotlinx Coroutines 1.8.1
- WorkManager 2.9.0 (notifikácie)
- ViewModel Compose 2.8.2
- `androidx.compose.material:material-icons-core` — **NOVÁ závislosť** (z BOM, prvostranná, §VII justifikácia: textový placeholder "H" nie je štandardné UX; knižnica je z oficiálneho Compose BOM bez externej závislosti)

**Storage**: Room + SQLite (on-device), offline-first

**Testing**: JUnit4 (JVM unit), Room in-memory (integration)

**Target Platform**: Android 8.0+ (API 26+), target SDK 34

**Performance Goals**: 60fps UI; auto-save ≤ 100ms per write (debounce slider 500ms)

**Constraints**: Offline-capable (§I); žiadny nový externý vendor (§VII); MVVM + Repository layer (§I)

**Scale/Scope**: Single user, 9–15 entít, denné záznamy

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Princíp | Status | Poznámka |
|---------|--------|---------|
| §I MVVM/Repository | ✅ PASS | Všetky nové metódy prechádzajú cez `TrackerRepository` → DAO. UI vola len ViewModel. |
| §II Index formula | ✅ PASS | Formula sa nemení. Auto-save volá existujúci `saveDay()` + `computeAndSaveDailyIndex()`. |
| §III DB schéma | ✅ PASS | Žiadna nová entita ani stĺpec. Nové metódy sú len nové DAO queries na existujúcich tabuľkách. |
| §IV UX | ✅ PASS | Auto-save = "minimálne kliknutia". Placeholder na Home = "prázdny stav s CTA". |
| §V Notifikácie | ✅ PASS | Notifikačná logika nie je dotknutá. |
| §VI Testovanie | ✅ PASS | Žiadna nová doménová logika nevyžaduje unit testy. UI-layer zmeny netriggerujú §VI. |
| §VII Závislosti | ⚠️ JUSTIFIED | `material-icons-core`: prvostranná Google/Compose BOM knižnica. Zdôvodnenie: UX štandard (§IV), žiadna externá závislosť, riziková hodnota nulová. |

**Constitution Check: PASS** — žiadna porušená brána.

## Project Structure

### Documentation (this feature)

```text
specs/011-visual-update-03/
├── plan.md           # Tento súbor
├── research.md       # Technické rozhodnutia (Phase 0)
├── data-model.md     # Entity a vzťahy (Phase 1)
├── quickstart.md     # Validačné scenáre (Phase 1)
├── spec.md           # Feature spec
├── tasks.md          # Task list
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
android_app/
├── app/
│   ├── build.gradle.kts                         # + material-icons-core (T018)
│   └── src/main/java/com/example/madhdtracker/
│       ├── data/
│       │   ├── TrackerRepository.kt              # + date-scoped queries, getAllEventDates()
│       │   ├── AppDatabase.kt                    # (bežná zmena ak treba nové DAO metódy)
│       │   └── [existujúce DAO súbory]
│       ├── domain/
│       │   ├── logic/IndexCalculator.kt           # (bez zmeny)
│       │   └── model/ElementConfig.kt             # (bez zmeny)
│       ├── ui/
│       │   ├── HomeViewModel.kt                   # + displayedDate, loadForDate(), loadPrev/Next
│       │   ├── TrackerViewModel.kt                # + saveCurrent(), + user entity merge
│       │   ├── screens/
│       │   │   ├── HomeScreen.kt                  # + PlaceholderBarChart, swipe, title update
│       │   │   ├── TrackerScreen.kt               # auto-save, remove save button
│       │   │   ├── EntityBarChart.kt              # BarRow, category pairing, weight text, PieChart
│       │   │   ├── VectorScreen.kt                # + PieChart composable
│       │   │   └── InfoScreen.kt                  # NOVÝ SÚBOR
│       │   └── navigation/
│       │       └── AppNavGraph.kt                 # + INFO route
│       └── MainActivity.kt                        # + INFO BottomNav, Home icon
```

**Structure Decision**: Android single-module app; nové súbory sa pridávajú do existujúcej štruktúry. Žiadna zmena modularizácie ani build systému (okrem jednej závislosti).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `material-icons-core` (§VII new dependency) | `Icons.Filled.Home` pre štandardné UX navigácie (US7) | Text "H" nie je UX-štandard; Canvas kresba ikony domu by bola oveľa zložitejšia bez benefitu |
