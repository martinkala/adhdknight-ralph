# Tasks: Range Scale, Day Deletion, Future Date Guard

**Input**: Design documents from `specs/013-range-updates/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/

**Tests**: Included for US1 (Constitution Principle II — value_effective change MUST have tests) and US3 (FR-012 — server tests required).

**Organization**: Tasks grouped by user story. US2 and US3 are independent of US1 and can proceed after Foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Data Model Foundations)

**Purpose**: Extend the data model and DAO layer — these are the minimal shared prerequisites that unblock all user story phases.

**⚠️ CRITICAL**: Complete before any user story work.

- [X] T001 [P] Extend `EntityNode` data class in `android_app/app/src/main/java/com/example/madhdtracker/domain/model/ElementConfig.kt` — add `scaleMin: Int = 1` and `scaleMax: Int = 5` fields (keep existing `scale: List<Int>?` for hasScale detection)
- [X] T002 [P] Add `@Query("DELETE FROM event_day WHERE id = :dayId") suspend fun deleteById(dayId: Long)` to `EventDayDao` interface in `android_app/app/src/main/java/com/example/madhdtracker/data/Daos.kt`

**Checkpoint**: Data model foundation ready — user story phases can start.

---

## Phase 2: Foundational (Config & Repository)

**Purpose**: Parse updated YAML config into `EntityNode` and expose delete via `TrackerRepository`.

- [X] T003 [P] Update YAML parsing in `android_app/app/src/main/java/com/example/madhdtracker/data/EntityConfigLoader.kt` — read `scale_min`/`scale_max` keys into `EntityNode.scaleMin`/`scaleMax`; fall back to `scale.min()` / `scale.max()` if YAML keys absent (depends T001)
- [X] T004 [P] Update sleep node in `android_app/app/src/main/assets/entities.yaml` — add `scale_min: -2` and `scale_max: 2` under the `sleep` key
- [X] T005 [P] Add `suspend fun deleteDay(dayId: Long)` to `TrackerRepository` in `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — body: `db.eventDayDao().deleteById(dayId)` (CASCADE handles EventValueEntity, SatisfactionEntity, IndexDailyEntity) (depends T002)

**Checkpoint**: Config parsed; delete exposed to ViewModel layer.

---

## Phase 3: User Story 1 — Záporné škály (Priority: P1) 🎯 MVP

**Goal**: Sleep (and other scale elements) support negative values; ADHD index stays 0-100.

**Independent Test**: Set sleep scale to -2..2, enter -1, save → verify `value_effective = 0.25` and index in 0-100.

### Tests for US1 (Constitution Principle II — REQUIRED)

- [X] T006 [P] [US1] Add failing unit tests for updated `IndexCalculator.valueEffective` signature in `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorTest.kt` — test cases: `valueEffective(0, -2, -2, 2) = 0.0`; `valueEffective(0, 0, -2, 2) = 0.5`; `valueEffective(0, 2, -2, 2) = 1.0`; backward compat `valueEffective(0, 3, 1, 5) = 0.5`; `valueEffective(0, 5, 1, 5) = 1.0`

### Implementation for US1

- [X] T007 [US1] Update `IndexCalculator.valueEffective` in `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt` — change signature to `valueEffective(valueBinary: Int, valueScale: Int?, scaleMin: Int = 1, scaleMax: Int = 5): Double`; change body to `valueScale?.let { (it - scaleMin) / (scaleMax - scaleMin).toDouble() } ?: valueBinary.toDouble()` (depends T006)
- [X] T008 [US1] Update `ElementUiState` in `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — add `scaleMin: Int = 1, scaleMax: Int = 5` fields; update `buildElementList` to set them from `EntityNode.scaleMin`/`scaleMax`; update `formStates` init to use `mutableStateOf((el.scaleMin + el.scaleMax) / 2)` as default scale value (depends T001)
- [X] T009 [US1] Update `saveCurrent` and `saveDay` in `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — change binary threshold from hardcoded `>= 3` to `>= (element.scaleMin + element.scaleMax) / 2`; pass `element.scaleMin, element.scaleMax` to `IndexCalculator.valueEffective` calls; for `satisfactionEffective` keep default `scaleMin=1, scaleMax=5` (overall_feeling is 1-5, Constitution IV) (depends T007, T008)
- [X] T010 [US1] Update Slider in `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — change `valueRange = 1f..5f` to `element.scaleMin.toFloat()..element.scaleMax.toFloat()`; change `steps = 3` to `element.scaleMax - element.scaleMin - 1`; change `coerceIn(1, 5)` to `coerceIn(element.scaleMin, element.scaleMax)` (depends T008)

**Checkpoint**: US1 complete — sleep slider shows -2..2, value_effective computed correctly, unit tests pass.

---

## Phase 4: User Story 2 — Zmazanie dňa (Priority: P2)

**Goal**: User can delete a day from TrackerScreen with a confirmation dialog; Room CASCADE handles dependent records.

**Independent Test**: Open a day with values → tap "Zmazať deň" → confirm → calendar shows day as empty.

### Implementation for US2

- [X] T011 [US2] Add `deleteDay(date: String, onDeleted: () -> Unit)` to `TrackerViewModel` in `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — launches coroutine: finds day by date via `repository.getByDate(date)`, calls `repository.deleteDay(day.id)`, then dispatches `onDeleted()` on Main (depends T005)
- [X] T012 [US2] Update `TrackerScreen` in `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — add `onDayDeleted: () -> Unit = {}` parameter; add `showDeleteDialog = remember { mutableStateOf(false) }`; add "Zmazať deň" `OutlinedButton` (red/error color); add `AlertDialog` with title "Zmazať deň?", message "Všetky záznamy pre $date budú vymazané.", confirm button "Zmazať" (calls `viewModel.deleteDay(date) { onDayDeleted() }`), dismiss button "Zrušiť" (depends T011)
- [X] T013 [US2] Update `AppNavGraph.kt` at `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt` — add `onDayDeleted = { navController.popBackStack() }` to `TrackerScreen` composable call (depends T012)

**Checkpoint**: US2 complete — delete dialog shows, day removed after confirmation, navigation returns to previous screen.

---

## Phase 5: User Story 3 — Zákaz budúcich dátumov (Priority: P3)

**Goal**: DatePicker blocks future dates; ViewModel rejects them; server returns 422; automated tests pass.

**Independent Test**: Tap tomorrow in DatePicker → grayed out; POST /api/v1/compute/daily with tomorrow → HTTP 422.

### Implementation for US3

- [X] T014 [US3] Add `SelectableDates` to DatePicker in `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — use `rememberDatePickerState(selectableDates = object : SelectableDates { override fun isSelectableDate(utcTimeMillis: Long): Boolean = utcTimeMillis <= System.currentTimeMillis() })` to grey out future dates in picker
- [X] T015 [US3] Add future-date guard to `onDateSelected` in `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — add `val dateError = mutableStateOf<String?>(null)`; at start of `onDateSelected` check `if (date.isAfter(LocalDate.now())) { dateError.value = "Nemožno zadať budúci dátum"; return }`; clear `dateError` on valid date
- [X] T016 [P] [US3] Add `@field_validator("date") @classmethod def date_not_in_future(cls, v: str) -> str` to `ComputeDailyRequest` and `DayInput` classes in `server/app/schemas/compute.py` — body: `from datetime import date as dt; if dt.fromisoformat(v) > dt.today(): raise ValueError("Date cannot be in the future"); return v`; import `field_validator` from pydantic
- [X] T017 [P] [US3] Add same `date_not_in_future` field validator to `DaySyncItem` class in `server/app/schemas/sync.py` — same implementation as T016
- [X] T018 [P] [US3] Add same `date_not_in_future` field validator to `MigrationDayItem` class in `server/app/schemas/migrate.py` — same implementation as T016
- [X] T019 [US3] Write pytest tests in `server/tests/api/test_future_date.py` — use `httpx.AsyncClient` with `ASGITransport(app=app)`; test: today → 200 on `POST /api/v1/compute/daily` with minimal valid body; tomorrow → 422; year 2099-01-01 → 422; yesterday → 200; also test `POST /api/v1/sync/batch` with future date → 422 (depends T016, T017)

**Checkpoint**: US3 complete — future dates blocked in picker, ViewModel, and server; pytest tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T020 Display `viewModel.dateError` as `Snackbar` or red `Text` in `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrackerScreen.kt` — show when `dateError.value != null`, auto-clear after user dismisses or selects valid date
- [X] T021 [P] Run quickstart.md validation scenarios SC-001 through SC-007 — confirm all scenarios pass end-to-end (requires physical device / emulator)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T001 and T002 can run in parallel
- **Foundational (Phase 2)**: Depends on Phase 1 — T003 depends T001; T005 depends T002; T004 independent
- **US1 (Phase 3)**: Depends on Phase 2 (T003, T004 must complete) — T006, T008 can start in parallel; T007 after T006; T009 after T007+T008; T010 after T008
- **US2 (Phase 4)**: Depends on Phase 2 (T005 must complete) — independent of US1, can start after Phase 2
- **US3 (Phase 5)**: Depends on Phase 1 only (no dependency on US1 or US2) — T014/T015 independent; T016/T017/T018 in parallel; T019 after T016+T017
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 1+2; no dependency on US2 or US3
- **US2 (P2)**: Depends on Phase 1+2 (T002, T005 only); no dependency on US1 or US3
- **US3 (P3)**: Android side depends only on Phase 1; Server side is fully independent

### Key Sequential Chains

```
T001 → T003 → T008 → T009 → T010   (US1 chain)
T001 → T008 → T009                  (US1 ViewModel chain)
T006 → T007 → T009                  (US1 test-first chain)
T002 → T005 → T011 → T012 → T013   (US2 chain)
T016, T017, T018 → T019             (US3 server chain)
```

---

## Parallel Opportunities

### Phase 1 (both in parallel)
```
Task: "T001 — Extend EntityNode with scaleMin/scaleMax"
Task: "T002 — Add deleteById to EventDayDao"
```

### Phase 2 (all in parallel after Phase 1)
```
Task: "T003 — Update EntityConfigLoader"
Task: "T004 — Update entities.yaml"
Task: "T005 — Add deleteDay to TrackerRepository"
```

### Phase 5 US3 server validators (all in parallel)
```
Task: "T016 — field_validator in compute.py"
Task: "T017 — field_validator in sync.py"
Task: "T018 — field_validator in migrate.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: T001, T002
2. Complete Phase 2: T003, T004, T005
3. Complete Phase 3: T006 → T007 → T008 → T009 → T010
4. **STOP and VALIDATE**: Sleep slider shows -2..2; value_effective correct; unit tests pass
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1+2 → foundation ready
2. US1 (Phase 3) → Negative scales in UI + domain logic ← MVP
3. US2 (Phase 4) → Delete day UI
4. US3 (Phase 5) → Future date blocking + server tests
5. Polish (Phase 6) → Error messages, validation run

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- T006 MUST be written BEFORE T007 (TDD — tests fail first, then implement)
- T019 MUST be written AFTER T016+T017 (tests verify the implementation)
- `overall_feeling` always uses scaleMin=1, scaleMax=5 — this is Constitution Principle IV and MUST NOT change
- Room CASCADE on EventDayEntity covers EventValueEntity, SatisfactionEntity, IndexDailyEntity — no manual cleanup needed in T005/T011
- Server schemas already use `field_validator` in auth.py — follow the same pattern for consistency
