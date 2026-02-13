# GitHub Copilot Instructions for Random Timer

This repo is a **native** app:

- Android: Kotlin + Jetpack Compose + Hilt in `native-android/`
- iOS: SwiftUI + Swift Concurrency in `native-ios/`

The app is a **random timer**: do not expose remaining time / countdown UI (only show the configured range).

## Non-Negotiables

### TDD + Test Gates

- Use TDD: write/adjust **failing tests first**, then implement.
- Target **100% coverage** for new/changed business logic. If something can’t be covered (e.g., OS audio focus quirks), document the gap and add a follow-up task in `TASKS.md`.
- Never claim something is fixed without running the relevant tests locally.
- Default gate: run `make verify` before marking work done.
- If UI/notifications/audio are touched:
  - Add/adjust Android instrumentation tests (`native-android/app/src/androidTest/**`)
  - Add/adjust iOS UI tests (`native-ios/RandomTimerUITests/**`)
  - Add/adjust Maestro flows under `.maestro/`

### Task Loop (Layered)

Maintain `TASKS.md` as the source of truth. Work in layers:

1. Make `make verify` green (build + unit tests)
2. Fix store/compliance blockers (Play/App Store) if present
3. Implement product enhancements
4. Refactor only after 1-3 are stable

Loop until `TASKS.md` has no remaining actionable items:

1. Pick the top unchecked task in `TASKS.md`
2. Write the failing test(s)
3. Implement the minimum to pass
4. Run `make verify` (and UI/instrumentation where applicable)
5. Update `TASKS.md` with what changed and which tests prove it

If blocked, write the blocker and evidence into `TASKS.md` instead of guessing.

## Android Guidance (Kotlin/Compose)

- Prefer pure, testable functions for business rules.
- Keep Composables thin; push logic into helpers.
- Use coroutines/Flow; avoid `Handler` and ad-hoc threading.
- Alarm behavior is owned by `native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt`.

## iOS Guidance (SwiftUI/Swift Concurrency)

- UI is SwiftUI; timer logic is in `native-ios/RandomTimer/Sources/Services/TimerManager.swift`.
- Notifications + alarm audio are in `native-ios/RandomTimer/Sources/Services/NotificationService.swift`.
- Prefer `async/await` and `@MainActor` correctness; avoid force unwraps in production.

## Safety

- Never commit secrets, API keys, keystores, or private credentials.
- Avoid adding new permissions unless the feature truly requires it.
