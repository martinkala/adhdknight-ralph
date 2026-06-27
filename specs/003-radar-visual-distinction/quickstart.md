# Quickstart Validation Guide: Radar Chart Visual Distinction

## Prerequisites

- Android Studio (Hedgehog or newer) with an emulator or physical device (API 26+)
- App built and installed: `./gradlew assembleDebug installDebug` from `android_app/`
- At least 1 day of tracker data logged (any values)

---

## Scenario 1 — Visual distinction visible with data (P1 core case)

**Goal**: Positive elements show light green axis, negative elements show light red axis.

1. Open the app → navigate to "Radar – detail" screen (Advanced vektor)
2. Observe the radar chart axes

**Expected**:
- Axes for `sleep`, `physical_activity`, `nutrition_protein`, `mindfulness` → **light green**, thicker stroke
- Axes for `stress_work`, `stress_personal`, `alcohol`, `caffeine` → **light red**, thinner stroke
- Data dots at each axis match the axis color
- Legend below chart shows green thick line labeled "Pozitívny vplyv" and red thin line labeled "Negatívny vplyv"

---

## Scenario 2 — No data / fresh install (edge case FR-008)

**Goal**: Chart remains functional with no classification colors when data is missing.

1. Clear app data (Settings → Apps → MADHD Tracker → Clear Data)
2. Open app → navigate to "Radar – detail"

**Expected**:
- Chart renders without crashing
- All axes shown in neutral color (no green/red)
- OR informational message: "Zbierame dáta pre personalizáciu grafu" (if 0-day state triggers this)

---

## Scenario 3 — Legend visible on small screen (SC-004)

1. Open "Radar – detail" on a small screen emulator (e.g., Pixel 3a, 5.6")
2. Observe without scrolling

**Expected**: Both legend items (green + red) are visible without scrolling.

---

## Scenario 4 — Regression — existing functionality preserved (FR-008)

1. Log a full day (all 8 elements + overall feeling)
2. Open "Radar – detail"

**Expected**:
- Chart still shows correct proportional values for each axis (no value regression)
- Element list below chart still shows values (e.g., "Spánok: 4/5")

---

## Build & run command

```bash
cd android_app
./gradlew assembleDebug installDebug
```

For unit tests covering classification logic:

```bash
./gradlew test
```
