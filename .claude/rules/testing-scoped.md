---
paths:
  - "**/*Test*"
  - "**/*test*"
  - "**/*Spec*"
  - "**/*spec*"
  - "native-android/app/src/test/**"
  - "native-android/app/src/androidTest/**"
  - "native-ios/RandomTimerTests/**"
---

# Test File Rules

- Follow TDD: failing test first, then implementation.
- No mocking unless testing external boundaries (network, disk, system APIs).
- Test names describe behavior, not implementation: `shouldShowAlarmWhenTimerExpires` not `testTimerFunction`.
- One assertion concept per test. Multiple asserts OK if they verify the same behavior.
- Clean up test state. No test-to-test dependencies.
- Use test-runner agent for execution. Never claim tests pass without running them.
