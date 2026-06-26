# Feature Specification: ADHD Tracker MVP Baseline

**Feature Branch**: `adhd-tracker-mvp`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "update spec add new feature activity detail which will display current activiti non editable info page. page will be invocable when clicking on activity and display page with activity name (spanok, alkohol, kava/caj ..) and short descirption of activity. Come up with solution where to store such a description. It shuld be simple text with markup capabilities to format . For hardcoded values this wil be defined inside system"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily Tracking And Index (Priority: P1)

As a user, I want to log my daily ADHD-related elements with minimal friction and
see a single daily index so I can understand how my day impacts my ADHD state.

**Why this priority**: This is the core value of the product and the minimum
viable outcome.

**Independent Test**: User can complete a daily log and immediately see a
computed daily index for that day.

**Acceptance Scenarios**:

1. **Given** a new day with no entries, **When** I open the tracker and submit
   values for all elements, **Then** the system saves the entries and displays a
   daily index for that day.
2. **Given** I reopen the app later that same day, **When** I view today, **Then**
   I see my previously saved entries and the same daily index.

---

### User Story 2 - Activity Detail Info (Priority: P2)

As a user, I want to open a read-only activity detail page from any activity
so I can understand what that activity means and how it affects my tracking.

**Why this priority**: Clear, low-friction guidance reduces confusion and keeps
daily tracking consistent.

**Independent Test**: User can tap an activity and see a non-editable page with
the activity name and a short formatted description.

**Acceptance Scenarios**:

1. **Given** the daily tracker list is visible, **When** I tap an activity,
   **Then** I see a detail page showing the activity name and description.
2. **Given** I am on the activity detail page, **When** I view the content,
   **Then** I cannot edit the description or activity name.

---

### User Story 3 - Trends And Vector View (Priority: P3)

As a user, I want to see my recent trend and a multi-dimensional view so I can
notice patterns across days.

**Why this priority**: Users need feedback beyond a single day to recognize
patterns and stay motivated.

**Independent Test**: With at least 7 days of data, user can view a weekly trend
and a vector view that reflects those days.

**Acceptance Scenarios**:

1. **Given** at least 7 days of logged data, **When** I open the trends screen,
   **Then** I see a weekly trend summary derived from those days.
2. **Given** multiple elements logged across days, **When** I open the vector
   view, **Then** I see a multi-dimensional snapshot reflecting the element
   values for the selected period.

---

### User Story 4 - Gentle Reminders (Priority: P4)

As a user, I want gentle reminders when I miss logging or neglect an area so I
can keep consistent habits without feeling overwhelmed.

**Why this priority**: Reminders drive adherence while respecting ADHD-friendly
UX constraints.

**Independent Test**: User receives at most one reminder per day under the
defined conditions and can disable reminders completely.

**Acceptance Scenarios**:

1. **Given** I have not completed today by the reminder time, **When** the day
   reaches the reminder threshold, **Then** I receive a single reminder.
2. **Given** I have disabled reminders, **When** a trigger condition occurs,
   **Then** no reminder is delivered.

---

### Edge Cases

- What happens when a user logs some elements but not all required ones?
- How does the system handle days with no entries when computing trends?
- What happens if reminders would trigger during the quiet window?
- What happens if an activity description is missing?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow users to record daily values for each
  defined element.
- **FR-002**: The system MUST require "overall feeling" to be recorded on a
  1-5 scale each day.
- **FR-003**: The system MUST compute a daily index on a 0-100 scale based on
  the recorded elements.
- **FR-004**: The system MUST support an optional detailed 1-5 scale for
  elements that defaults to the midpoint when not provided.
- **FR-005**: The system MUST provide a weekly trend view derived from daily
  data.
- **FR-006**: The system MUST allow users to open a read-only activity detail
  page from any activity entry.
- **FR-007**: The activity detail page MUST display the activity name and a
  short description.
- **FR-008**: Activity descriptions MUST support basic text formatting via
  markup.
- **FR-009**: Activity descriptions MUST be stored as built-in, non-editable
  content within the app.
- **FR-010**: The system MUST provide a multi-dimensional vector view derived
  from recorded element values.
- **FR-011**: The system MUST adapt element weights no more than once per week
  after a minimum of 15 days of data.
- **FR-012**: The system MUST allow users to enable or disable reminders.
- **FR-013**: The system MUST ensure no more than one reminder is sent per day.
- **FR-014**: The system MUST avoid sending reminders inside the quiet window
  and must not send reminders retroactively.
- **FR-015**: The system MUST allow users to export their data in a common
  format.
- **FR-016**: The system MUST allow a sync toggle that does not change behavior
  when sync is not configured.

### Key Entities *(include if feature involves data)*

- **Day Log**: A single day of user inputs across all tracked elements.
- **Element Entry**: The recorded value for an element on a specific day.
- **Activity Description**: A built-in formatted text entry that explains an
  activity.
- **Daily Index**: The computed 0-100 score for a single day.
- **Weekly Summary**: A derived view of daily indices across a week.
- **Weights Profile**: The current weights used to compute the index.
- **Reminder Log**: A record of reminders sent to enforce daily limits.
- **ASRS Check-in**: A periodic self-assessment score used for recalibration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of users can complete a daily log in under 2 minutes.
- **SC-002**: Daily index is available immediately after a log is submitted for
  99% of sessions.
- **SC-003**: Weekly trend view is available for 100% of users with 7 or more
  logged days.
- **SC-004**: Reminder delivery respects the one-per-day rule in 100% of cases.
- **SC-005**: At least 95% of users can open and read an activity description
  within 5 seconds from the daily tracker screen.

## Assumptions

- The product targets a single user on a single device with local data storage.
- The app is usable without network connectivity.
- Users can opt out of reminders without losing other functionality.
- Data export is intended for user-controlled backups or personal analysis.
- Advanced integrations (tasks, calendar, wearables) are out of scope for MVP.
- Activity descriptions are maintained as built-in app content and are not
  user-editable.
