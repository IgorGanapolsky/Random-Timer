# Tasks

This file is the task source-of-truth for iterative agent work.

## Rules

- Each task must have acceptance criteria and tests.
- Use TDD (write failing tests first).
- Do not mark a task done until `make verify` is green (and UI/instrumentation tests are updated where relevant).

## Backlog (Next)

- [ ] **Range Slider: Drag Min Pushes Max (>= 30s gap)**
  - Acceptance:
    - Dragging min beyond `max - 30s` pushes max forward to keep a 30s minimum gap (until max hits 300s).
    - Dragging max below `min + 30s` pulls min back to keep a 30s minimum gap (until min hits 0s).
    - Works on **Android + iOS**.
  - Tests:
    - Android unit tests for range adjustment helper.
    - iOS unit tests for range adjustment helper.
    - Maestro flow updated/added to exercise range updates.

- [ ] **Bluetooth Headset Button Stops Alarm**
  - Acceptance:
    - When alarm is ringing, pressing a Bluetooth headset media button stops the alarm (sound + vibration).
    - Works on **Android + iOS**.
  - Tests:
    - Android unit tests for media-button handling logic.
    - iOS unit tests for NotificationService media session wiring (as feasible).

- [ ] **Tap Timer Circle = Stop (When Alarm Has Gone Off)**
  - Acceptance:
    - When status is `ALARM` or `COMPLETE`, tapping the timer circle has the same effect as the Stop button.
    - Works on **Android + iOS**.
  - Tests:
    - Android instrumentation test or Maestro flow verifying tap stops.
    - iOS UI test or Maestro flow verifying tap stops.

- [ ] **Android: Duck Other Audio Instead of Pausing**
  - Acceptance:
    - Alarm audio requests transient focus with ducking (navigation-app style).
    - Other audio should duck rather than stop when possible.
  - Tests:
    - Unit test for focus-request configuration helper (API-level behavior guarded).

- [ ] **Landscape Layout Fix**
  - Acceptance:
    - Action buttons are visible and tappable in landscape on both platforms.
  - Tests:
    - Maestro flow(s) that run in landscape (or equivalent platform UI tests).

- [ ] **Alarm Notification Stop Action**
  - Acceptance:
    - When alarm is ringing, notification action is labeled **Stop** (not Dismiss).
    - Action stops alarm and returns the user to the app home/setup screen (or device home where appropriate).
    - Works on **Android + iOS**.
  - Tests:
    - Android instrumentation test for notification action intent handling (as feasible).
    - iOS unit/UI test for action wiring (as feasible).

