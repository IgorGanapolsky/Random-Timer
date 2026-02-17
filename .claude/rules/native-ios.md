---
paths:
  - "native-ios/**/*.swift"
  - "native-ios/**/*.xc*"
  - "native-ios/**/*.plist"
---

# iOS Platform Rules

- Swift-first. Minimum deployment target: iOS 17.
- SwiftUI for new screens. UIKit only when SwiftUI can't do it.
- Use `@Observable` (Observation framework) for new state. No ObservableObject in new code.
- Structured concurrency (async/await, TaskGroup) for async. No raw GCD in new code.
- TimelineView with `minimumInterval: 1.0/60.0` for animations (prevents 120Hz waste on ProMotion).
- Test with XCTest in `native-ios/RandomTimerTests/`.
- Pod issues: `cd native-ios && pod deintegrate && pod install`.
