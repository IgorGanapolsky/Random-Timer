# iOS (SwiftUI/Swift Concurrency) Instructions

applyTo: "native-ios/**/*.swift"

## Architecture

- UI is SwiftUI. Business logic lives in `TimerManager` and service classes under `native-ios/RandomTimer/Sources/Services`.
- Prefer `async/await` and `@MainActor` correctness over ad-hoc threading.
- Avoid force unwraps in production code.

## UX Constraints

- This is a *random timer*: do not surface remaining time/countdown UI.
- Keep layouts responsive in landscape. Use `ViewThatFits`, `GeometryReader`, or size classes when needed.

## Notifications / Audio

- Alarm notifications and alarm audio live in `NotificationService`.
- If changing audio session behavior, keep "duck others" behavior for alarms (navigation-app style).

## Testing

- Use TDD: add failing unit tests first, then implement.
- Unit tests: `native-ios/RandomTimerTests/**`
- UI tests: `native-ios/RandomTimerUITests/**`
- Run locally:
  - `cd native-ios && xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer -destination 'platform=iOS Simulator,name=iPhone 16' CODE_SIGNING_ALLOWED=NO`

