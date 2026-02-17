# Android (Kotlin/Compose) Instructions

applyTo: "native-android/**/*.kt"

## Architecture

- Prefer pure functions in the domain layer for business rules.
- UI is Jetpack Compose; keep Composables thin and push logic into testable helpers.
- Use coroutines/Flow; avoid `Handler`/callbacks unless required by an API.

## Compose

- Keep layouts responsive (portrait/landscape). Use `LocalConfiguration` or `BoxWithConstraints` when needed.
- Avoid exposing countdown/remaining-time UI. This app is a *random timer* and should not reveal remaining time.

## Services / Notifications / Audio

- Alarm behavior lives in `TimerForegroundService`.
- If changing notifications or audio focus, add/adjust tests and verify behavior in both foreground and background.

## Testing

- Use TDD: add failing tests first, then implement.
- Unit tests: `native-android/app/src/test/**`
- Instrumentation tests: `native-android/app/src/androidTest/**`
- Run locally:
  - `make verify-android` (unit tests + debug build)
  - `make verify-android-instrumentation` (requires emulator/device)
  - `cd native-android && ./gradlew lintDebug` (optional; currently flaky in some environments)
