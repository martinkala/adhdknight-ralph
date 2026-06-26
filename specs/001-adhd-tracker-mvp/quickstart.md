# Quickstart: ADHD Tracker MVP Baseline

## Prerequisites

- Android Studio with JDK 17
- Local Android SDK configured

## Setup

1. Open `android_app/` in Android Studio.
2. Sync Gradle and build the project.
3. Run the app on an emulator or device (Android 26+).

## Validation Scenarios

### Daily Tracking And Index

1. Open the app and navigate to the daily tracker.
2. Enter values for all activities and save.
3. Verify the daily index appears immediately.

### Activity Detail Info

1. From the daily tracker list, tap an activity (e.g., sleep or caffeine).
2. Verify a read-only page appears with the activity name and formatted
   description.

### Trends And Vector View

1. Log at least 7 days of data.
2. Open the weekly trend view and confirm a summary is displayed.
3. Open the vector view and confirm a multi-dimensional snapshot is visible.

### Gentle Reminders

1. Leave a day unfilled past the reminder time.
2. Confirm at most one reminder is shown and none are delivered in the quiet
   window.
3. Disable reminders and confirm none are delivered.

## Validation Notes

- Quickstart steps documented; full validation not run in this environment.
