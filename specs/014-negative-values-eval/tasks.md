# Tasks: Scale Color Visualization

**Input**: Design documents from `specs/014-negative-values-eval/`

**Prerequisites**: spec.md ✓, checklists/ ✓ (no plan.md — tasks derived from spec + constitution + codebase context)

**Tests**: Included for US3 (spec FR-007, FR-008, FR-009 explicitly require them). No tests for US1/US2 UI color logic (Compose Color not JVM-testable; visual verification via quickstart).

**Tech Stack** (from constitution + codebase): Kotlin, Jetpack Compose / Material 3, MVVM + Repository, Android min SDK 26.

**Organization**: Tasks grouped by user story. US1 and US2 share the ScaleColorMapper foundation. US3 is independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Foundational (ScaleColorMapper)

**Purpose**: Create the shared color-mapping utility that both US1 and US2 depend on. Pure Compose function — no data model changes needed.

**⚠️ CRITICAL**: Both US1 and US2 depend on this. Complete before starting either story.

- [X] T001 Create `android_app/app/src/main/java/com/example/madhdtracker/ui/ScaleColorMapper.kt` — object with `fun scaleCardColor(value: Int, scaleMin: Int, scaleMax: Int, impact: Int, isActive: Boolean): Color`. Logic: if not active → return current pale impact-tint (green `Color(0x1A4CAF50)` for impact=1, red `Color(0x1AF44336)` for impact=-1). If active AND `scaleMin < 0` (negative range): value < 0 → red with `alpha = abs(value).toFloat() / max(abs(scaleMin), scaleMax).toFloat()` clamped 0.1–0.5; value == 0 → `Color.Transparent`; value > 0 → green with same alpha formula. If active AND `scaleMin >= 0` (positive-only): `alpha = ((value - scaleMin).toFloat() / (scaleMax - scaleMin).toFloat()).coerceIn(0.1f, 0.5f)`; if impact > 0 → green; if impact < 0 → red.

**Checkpoint**: ScaleColorMapper created and logic is self-contained — ready for US1 and US2 integration.

---

## Phase 2: User Story 1 — Farebná vizualizácia (záporný range) (Priority: P1) 🎯 MVP

**Goal**: Elements with negative ranges (scaleMin < 0) show dynamic background color + numeric value in TrackerScreen.

**Independent Test**: Set sleep slider to -2 → card is deep red with "-2" visible. Set to 0 → card is transparent/neutral with "0". Set to 2 → card is deep green with "2". Binary elements remain unchanged.

### Implementation for US1

- [X] T002 [US1] Update `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — (a) Replace the static `sectionColor` `when` block with `ScaleColorMapper.scaleCardColor(state.scale.value, element.scaleMin, element.scaleMax, element.impact, state.binary.value && element.hasScale)` for all elements. For elements with `element.scaleMin < 0` this correctly renders dynamic negative-range colors; for others it falls back to the inactive pale tint. (b) Inside the card `Column`, after the Switch row, add `Text(text = state.scale.value.toString(), style = MaterialTheme.typography.bodyMedium)` visible when `state.binary.value && element.hasScale`. (depends T001)

**Checkpoint**: US1 complete — sleep slider shows dynamic red/white/green background + numeric label. Positive-only range elements may not yet show correct active coloring (handled in US2).

---

## Phase 3: User Story 2 — Farebná vizualizácia (kladný range) (Priority: P2)

**Goal**: Elements with positive-only ranges (scaleMin >= 0) show dynamic saturation color + numeric value, consistent with US1 pattern.

**Independent Test**: Set physical_activity (impact=1, 1..5) to 5 → deep green + "5". Set to 1 → pale green + "1". Set stress_work (impact=-1, 1..5) to 5 → deep red + "5". Binary elements unchanged.

### Implementation for US2

- [X] T003 [US2] Verify and adjust `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — after T002, the `ScaleColorMapper.scaleCardColor()` call already handles positive-only ranges via the `scaleMin >= 0` branch. Manually verify with physical_activity and stress_work elements: run app and confirm (a) active high value shows saturated correct color, (b) active low value shows pale correct color, (c) number is visible. If ScaleColorMapper alpha bounds need adjustment for 1-5 range (minimum alpha at value=1 may look too faint), tune the `0.1f` lower bound in `ScaleColorMapper.kt`. (depends T002)

**Checkpoint**: US2 complete — all scale elements (both negative and positive ranges) show dynamic colors + numbers. Full color palette functional.

---

## Phase 4: User Story 3 — Testy a ASRS dokumentácia (Priority: P3)

**Goal**: Unit tests cover IndexCalculator edge cases with negative ranges. ASRS compatibility is documented.

**Independent Test**: Run `./gradlew :app:test` — all new tests in `NegativeRangeIndexTest.kt` pass. ASRS compatibility doc exists in `specs/014-negative-values-eval/asrs-compatibility.md`.

### Tests for US3 (FR-007, FR-008 — REQUIRED by spec)

- [X] T004 [P] [US3] Create `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/NegativeRangeIndexTest.kt` — test class using existing test helpers from `IndexCalculatorTest`. Test cases (all use `computeDailyIndexGrouped` or `valueEffective` with actual EntityConfig built from test data):
  - `allElementsAtScaleMin_negativeRange_indexIsZero`: all elements at scaleMin=-2 (valueEffective=0.0 each) → index = 0.0
  - `allElementsAtScaleMax_indexIs100`: all elements at scaleMax (valueEffective=1.0 each, positive impact) → index = 100.0
  - `mixedNegativeAndPositive_indexInValidRange`: mix of -2 and +2 values → index between 0 and 100
  - `negativeImpactElementAtNegativeValue_effectiveIsZero`: stress_work (impact=-1) with scaleMin=-2, value=-2 → `valueEffective(0, -2, -2, 2) = 0.0` (minimum stress = no negative contribution) — semantically correct
  - `negativeImpactElementAtPositiveValue_effectiveIsOne`: stress_work at value=2 → `valueEffective(0, 2, -2, 2) = 1.0` (maximum stress = full negative weight)
  - `overallFeelingAlwaysScale1to5_unchanged`: `valueEffective(0, 3, 1, 5) = 0.5` — constitution Principle IV invariant

- [X] T005 [P] [US3] Add tests to `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorTest.kt` — add at end of class: `computeDailyIndexGrouped_mixedEntityConfig_staysIn0to100`: build EntityConfig with sleep (-2..2) + overall_feeling (1..5) + stress_work (1..5), provide values with sleep=-1 + overall_feeling=3 + stress_work=4 → assert result in 0.0..100.0 and is not null.

### ASRS Documentation for US3 (FR-009 — REQUIRED by spec)

- [X] T006 [US3] Create `specs/014-negative-values-eval/asrs-compatibility.md` — document: (1) How value_effective normalization ensures 0-1 range regardless of scaleMin/scaleMax (formula: `(value - scaleMin) / (scaleMax - scaleMin)`). (2) Scenario: all positive-impact elements at scaleMin (negative value, e.g. sleep=-2) → valueEffective=0.0 → daily index ≈ 0. ASRS score likely elevated (bad ADHD day). This triggers recalibration if `|ASRS - index| > 10` for 2 consecutive days — CORRECT behavior, no compatibility issue. (3) Scenario: all negative-impact elements at their negative scaleMin → valueEffective=0.0 → no negative contribution to index → index inflated. ASRS may diverge. Risk: index looks good but user actually has high-severity negative behaviors at "low" values. (4) Recommended mitigation: Document in AGENTS.md that future features adding negative ranges to negative-impact elements should consider semantic review of the color direction (CHK011 from ux.md checklist).

**Checkpoint**: US3 complete — all new tests pass, ASRS compatibility documented.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T007 [P] Run `./gradlew :app:test` from `android_app/` and confirm all existing tests still pass (no regressions from T004/T005 additions)
- [ ] T008 [P] Run quickstart.md validation scenarios manually on device/emulator — verify sleep -2..2 shows red↔white↔green, physical_activity 1..5 shows pale→sýto zelená, stress_work shows red gradient, number visible for all

---

## Phase 6: ShareSheet Export

**Goal**: Po exporte CSV/JSON sa zobrazí Android ShareSheet — používateľ môže súbor zdieľať cez Gmail, uložiť do Files, atď.

- [X] T009 Create `android_app/app/src/main/res/xml/file_paths.xml` — FileProvider paths config: `<files-path name="exports" path="." />`
- [X] T010 Update `android_app/app/src/main/AndroidManifest.xml` — add `<provider android:name="androidx.core.content.FileProvider" ...>` inside `<application>`
- [X] T011 Update `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/SettingsScreen.kt` — replace Toast after export with `FileProvider.getUriForFile()` + `Intent.ACTION_SEND` ShareSheet for both CSV and JSON buttons

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on T001 (ScaleColorMapper)
- **US2 (Phase 3)**: Depends on T002 (TrackerScreen already has ScaleColorMapper integrated)
- **US3 (Phase 4)**: T004, T005 are independent of US1/US2 (JVM tests, no Compose dependency); T006 is independent of all code
- **Polish (Phase 5)**: T007 after T004+T005; T008 after T002+T003

### User Story Dependencies

```
T001 → T002 [US1] → T003 [US2] → T008 (manual validation)
T004, T005 [US3] → T007 (test suite check)
T006 [US3] — fully independent
```

### Parallel Opportunities

```
# US3 tasks all parallelizable:
Task: "T004 — NegativeRangeIndexTest.kt"
Task: "T005 — IndexCalculatorTest additions"
Task: "T006 — asrs-compatibility.md"

# Polish (after US3 implementation):
Task: "T007 — run test suite"
Task: "T008 — manual device validation" (after T002+T003)
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete T001 (ScaleColorMapper)
2. Complete T002 (TrackerScreen for negative-range elements + number display)
3. **STOP and VALIDATE**: Sleep slider shows red/white/green + number
4. Proceed to US2 if MVP validated

### Incremental Delivery

1. T001 → foundation ready
2. T002 → US1 visual MVP (negative range elements)
3. T003 → US2 extension (positive-only range elements)
4. T004, T005, T006 (parallel) → US3 tests + docs
5. T007, T008 → polish + validation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- ScaleColorMapper must NOT use any Android context or DI — pure Color computation only
- `overall_feeling` always uses scaleMin=1, scaleMax=5 — Constitution Principle IV. ScaleColorMapper will apply its positive-impact palette (pale→sýto zelená) which is correct.
- For binary (no-scale) elements: ScaleColorMapper receives `isActive=false` → returns pale impact tint → unchanged behavior (FR-005)
- T003 may be a no-op if ScaleColorMapper already handles positive-only correctly after T002 — verification task
- T006 ASRS doc is a text artifact, not code — can be written before or after T004/T005
