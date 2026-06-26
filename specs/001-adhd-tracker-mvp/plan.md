# Implementation Plan: ADHD Tracker MVP Baseline

**Branch**: `001-adhd-tracker-mvp` | **Date**: 2026-06-26 | **Spec**: `specs/001-adhd-tracker-mvp/spec.md`

**Input**: Feature specification from `specs/001-adhd-tracker-mvp/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Deliver an offline-first Android app that lets users log daily ADHD-related
activities, view a daily index, open read-only activity details with formatted
descriptions, review weekly trends and a vector view, and receive gentle
reminders under strict UX limits.

## Technical Context

**Language/Version**: Kotlin (JVM target 17)

**Primary Dependencies**: Jetpack Compose (Material 3), Room, WorkManager,
Kotlin Coroutines, Navigation Compose

**Storage**: Room (local SQLite)

**Testing**: JUnit (unit), AndroidX Test (instrumentation), Room in-memory DB
for integration tests

**Target Platform**: Android 26+

**Project Type**: Mobile app (single Android app)

**Performance Goals**: Daily tracker and activity detail screens render in under
1 second on mid-range devices; daily index visible immediately after save.

**Constraints**: Offline-first; Compose-only UI; MVVM + Repository; WorkManager
for background notifications; no DI framework in MVP.

**Scale/Scope**: Single-user local app; ~9 tracked elements; weekly summaries.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- MVVM + Repository separation enforced (PASS)
- Offline-first operation required (PASS)
- Kotlin + Compose only for UI (PASS)
- Room for persistence, WorkManager for background (PASS)
- Domain logic changes require tests (PASS)
- Notification rules and quiet window enforced (PASS)
- Data model schema preserved (PASS)
- MVP scope respected; Post-MVP features excluded (PASS)
- No DI framework in MVP (PASS)

## Project Structure

### Documentation (this feature)

```text
specs/001-adhd-tracker-mvp/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
android_app/
├── app/
│   └── src/
│       ├── main/
│       │   ├── java/
│       │   └── res/
│       ├── test/
│       └── androidTest/
├── build.gradle.kts
├── settings.gradle.kts
└── gradle/
```

**Structure Decision**: Single Android app under `android_app/` with MVVM
feature modules and Room persistence. No backend or API components.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository pattern | Required by constitution | Direct DAO access violates Principle I |
