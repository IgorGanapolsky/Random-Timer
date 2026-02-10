---
paths:
  - "native-android/**/*.kt"
  - "native-android/**/*.xml"
  - "native-android/**/*.gradle*"
---

# Android Platform Rules

- Kotlin-first. Target API 34+.
- Use Jetpack Compose for all new UI. No XML layouts for new screens.
- Hilt for DI. Annotate modules in `di/`.
- ViewModel + StateFlow for state management. No LiveData in new code.
- Coroutines for async. Never block the main thread.
- Test with `native-android/app/src/test/` (unit) and `native-android/app/src/androidTest/` (instrumented).
- `adb reverse tcp:8081 tcp:8081` for Metro connection issues.
- Gradle builds: `./gradlew assembleDebug` from `native-android/`.
