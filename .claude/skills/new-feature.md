# Skill: New Feature

Scaffold a feature module following project architecture. Uses progressive disclosure — only loads the phase you're in.

## Trigger

User invokes `/new-feature` or asks to create/add a new feature.

## Phase 1: Requirements (load this first)

Ask the user:
- **Feature name** (e.g., "notifications", "history", "presets")
- **Platform**: Android, iOS, or both?
- **Needs navigation?** (yes/no)
- **Needs persistent state?** (yes/no)

Stop here. Do NOT load Phase 2 until requirements are confirmed.

## Phase 2: Scaffold (load after Phase 1 confirmed)

### Android (`native-android/`)
```bash
mkdir -p native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/{featureName}
mkdir -p native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/{featureName}
```

Create screen composable, ViewModel, and add to Navigation.kt.

### iOS (`native-ios/`)
```bash
mkdir -p native-ios/RandomTimer/Sources/UI/{FeatureName}
```

Create SwiftUI View, ViewModel using @Observable, and add to navigation.

Stop here. Do NOT load Phase 3 until scaffold compiles.

## Phase 3: Integration (load after Phase 2 compiles)

- Wire navigation entry points
- Add DI bindings (Hilt for Android, direct init for iOS)
- Add persistent state if needed (DataStore for Android, UserDefaults/SwiftData for iOS)
- Write initial test (TDD: failing test first)

## Phase 4: Verify (load after Phase 3)

- Run tests on both platforms
- Verify navigation flow works
- Confirm state persistence survives app restart

## Success Criteria

- Feature compiles on target platform(s)
- Navigation works end-to-end
- At least one test per platform
- No hardcoded strings (use strings.xml / Localizable)
