# Research: ADHD Tracker MVP Baseline

## Decisions

### Activity Descriptions Storage

**Decision**: Store activity descriptions as bundled, read-only app resources,
keyed by activity identifier, with markup in a lightweight Markdown subset.

**Rationale**: Descriptions are non-editable, must ship with the app, and should
be available offline. A bundled resource avoids DB migrations and keeps content
immutable at runtime.

**Alternatives considered**:
- Store in Room: rejected due to unnecessary migrations and write paths.
- Remote fetch: rejected due to offline-first requirement.

### Markup Format

**Decision**: Support a minimal Markdown subset (bold, italic, bullet lists,
line breaks) and render locally without network dependencies.

**Rationale**: Provides readable formatting while keeping parsing simple and
avoiding heavy dependencies.

**Alternatives considered**:
- Full HTML: rejected due to complexity and rendering risks.
- Plain text only: rejected because the requirement asks for markup support.

### Notifications Scheduling

**Decision**: Implement notification triggers via WorkManager with local checks
for quiet window and daily rate limit.

**Rationale**: Aligns with constitution requirement for WorkManager and
supports offline scheduling.

**Alternatives considered**:
- AlarmManager: rejected by constitution.
- Foreground services: rejected by constitution and UX constraints.
