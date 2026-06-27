# Tasks: ADHD Tracker MVP Baseline

**Input**: Design documents from `/specs/001-adhd-tracker-mvp/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Required for domain logic per constitution (unit + Room integration).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Mobile**: `android_app/app/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Verify Android app builds in `android_app/` and document any setup notes in `specs/001-adhd-tracker-mvp/quickstart.md`
- [X] T002 [P] Define base package structure under `android_app/app/src/main/java/com/adhdtracker/` (ui, data, domain, notifications)
- [X] T003 [P] Add baseline navigation scaffold in `android_app/app/src/main/java/com/adhdtracker/ui/navigation/AppNavGraph.kt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create Room entities and DAOs in `android_app/app/src/main/java/com/adhdtracker/data/db/` per `data-model.md`
- [X] T005 Create Room database setup in `android_app/app/src/main/java/com/adhdtracker/data/db/AppDatabase.kt`
- [X] T006 Implement repository interfaces in `android_app/app/src/main/java/com/adhdtracker/data/repository/` for days, values, weights, indices, notifications
- [X] T007 Implement domain models and mappers in `android_app/app/src/main/java/com/adhdtracker/domain/model/`
- [X] T008 Implement index calculation and weight adaptation logic in `android_app/app/src/main/java/com/adhdtracker/domain/logic/IndexCalculator.kt`
- [X] T009 Implement ASRS recalibration logic in `android_app/app/src/main/java/com/adhdtracker/domain/logic/AsrsRecalibrator.kt`
- [X] T010 Implement notification rule evaluator in `android_app/app/src/main/java/com/adhdtracker/notifications/NotificationRules.kt`
- [X] T011 Create WorkManager worker scaffold in `android_app/app/src/main/java/com/adhdtracker/notifications/NotificationWorker.kt`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Daily Tracking And Index (Priority: P1) 🎯 MVP

**Goal**: Users can log daily activities with low friction and see a daily index

**Independent Test**: User can complete a daily log and immediately see the daily index

### Tests for User Story 1

- [X] T012 [P] [US1] Unit tests for value_effective and daily index in `android_app/app/src/test/java/com/adhdtracker/domain/logic/IndexCalculatorTest.kt`
- [X] T013 [P] [US1] Room integration tests for CRUD and index persistence in `android_app/app/src/androidTest/java/com/adhdtracker/data/db/DatabaseIntegrationTest.kt`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement daily tracker UI in `android_app/app/src/main/java/com/adhdtracker/ui/screens/DailyTrackerScreen.kt`
- [X] T015 [P] [US1] Implement daily tracker ViewModel in `android_app/app/src/main/java/com/adhdtracker/ui/viewmodel/DailyTrackerViewModel.kt`
- [X] T016 [US1] Wire repository operations for day logging in `android_app/app/src/main/java/com/adhdtracker/data/repository/DayLogRepository.kt`
- [X] T017 [US1] Display daily index on home screen in `android_app/app/src/main/java/com/adhdtracker/ui/screens/HomeScreen.kt`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Activity Detail Info (Priority: P2)

**Goal**: Users can open a read-only activity detail page with formatted descriptions

**Independent Test**: Tapping an activity shows a non-editable detail page with title and description

### Implementation for User Story 2

- [X] T018 [P] [US2] Define activity descriptions resource in `android_app/app/src/main/res/raw/activity_descriptions.md`
- [X] T019 [P] [US2] Implement description loader in `android_app/app/src/main/java/com/adhdtracker/data/repository/ActivityDescriptionRepository.kt`
- [X] T020 [P] [US2] Implement activity detail UI in `android_app/app/src/main/java/com/adhdtracker/ui/screens/ActivityDetailScreen.kt`
- [X] T021 [US2] Add navigation from daily tracker items to activity detail in `android_app/app/src/main/java/com/adhdtracker/ui/navigation/AppNavGraph.kt`

**Checkpoint**: User Story 2 should be functional and testable independently

---

## Phase 5: User Story 3 - Trends And Vector View (Priority: P3)

**Goal**: Users can view weekly trends and a multi-dimensional vector view

**Independent Test**: With 7+ days of data, user can see weekly trend and vector snapshot

### Tests for User Story 3

- [X] T022 [P] [US3] Unit tests for weekly aggregation in `android_app/app/src/test/java/com/adhdtracker/domain/logic/WeeklySummaryTest.kt`

### Implementation for User Story 3

- [X] T023 [P] [US3] Implement weekly trend screen in `android_app/app/src/main/java/com/adhdtracker/ui/screens/WeeklyTrendScreen.kt`
- [X] T024 [P] [US3] Implement vector view screen in `android_app/app/src/main/java/com/adhdtracker/ui/screens/VectorViewScreen.kt`
- [X] T025 [US3] Add weekly summary calculation in `android_app/app/src/main/java/com/adhdtracker/domain/logic/WeeklySummaryCalculator.kt`
- [X] T026 [US3] Wire navigation to trends and vector screens in `android_app/app/src/main/java/com/adhdtracker/ui/navigation/AppNavGraph.kt`

**Checkpoint**: User Story 3 should be functional and testable independently

---

## Phase 6: User Story 4 - Gentle Reminders (Priority: P4)

**Goal**: Users receive gentle reminders under strict notification rules

**Independent Test**: At most one reminder per day is delivered and quiet window is respected

### Tests for User Story 4

- [X] T027 [P] [US4] Unit tests for notification rules in `android_app/app/src/test/java/com/adhdtracker/notifications/NotificationRulesTest.kt`

### Implementation for User Story 4

- [X] T028 [P] [US4] Implement reminder settings UI in `android_app/app/src/main/java/com/adhdtracker/ui/screens/NotificationSettingsScreen.kt`
- [X] T029 [US4] Implement notification scheduling and logging in `android_app/app/src/main/java/com/adhdtracker/notifications/NotificationScheduler.kt`
- [X] T030 [US4] Enforce quiet window and daily limit in `android_app/app/src/main/java/com/adhdtracker/notifications/NotificationRules.kt`

**Checkpoint**: User Story 4 should be functional and testable independently

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Update copy and error states in `android_app/app/src/main/java/com/adhdtracker/ui/` for clarity and ADHD-friendly messaging
- [X] T032 [P] Add export flow stub in `android_app/app/src/main/java/com/adhdtracker/ui/screens/SettingsScreen.kt`
- [X] T033 [P] Add sync toggle stub in `android_app/app/src/main/java/com/adhdtracker/ui/screens/SettingsScreen.kt`
- [X] T034 Run quickstart validation and update `specs/001-adhd-tracker-mvp/quickstart.md` with any corrections

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 -> P2 -> P3 -> P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 data model but uses shared repositories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on daily data created in US1
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on notification logging and settings

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before screens
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
Task: "Define activity descriptions resource in android_app/app/src/main/res/raw/activity_descriptions.md"
Task: "Implement description loader in android_app/app/src/main/java/com/adhdtracker/data/repository/ActivityDescriptionRepository.kt"
Task: "Implement activity detail UI in android_app/app/src/main/java/com/adhdtracker/ui/screens/ActivityDetailScreen.kt"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 2 -> Test independently -> Deploy/Demo
4. Add User Story 3 -> Test independently -> Deploy/Demo
5. Add User Story 4 -> Test independently -> Deploy/Demo

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Phase 8: Convergence

- [ ] T035 Fix Gradle toolchain to provide JAVA_COMPILER for CLI builds per plan: configure JDK 17 in `android_app/gradle.properties` or install a full JDK (missing javac) (missing)
