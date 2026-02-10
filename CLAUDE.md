# Random Timer

React Native/Expo timer app. Package: `com.iganapolsky.randomtimer`. Expo SDK 54, RN 0.81.4 (New Architecture).

## Commands

```bash
npm start                    # Expo dev client (cache clear)
npm run android / ios        # Build and run
npm run quality              # Full check: compile + lint + format + test
npm test                     # Jest tests
npm run prebuild:clean       # Regenerate native projects
adb reverse tcp:8081 tcp:8081  # Fix Android Metro connection
maestro test .maestro/       # E2E smoke tests
```

## Path Aliases

`@navigation`, `@shared/*`, `@features/*`, `@assets` — configured in `tsconfig.json` + `babel.config.js`.

## Non-Obvious Rules

- **Act, Don't Instruct**: NEVER tell user to run commands. Execute everything autonomously.
- **Restricted imports**: Use `SafeAreaView` from `react-native-safe-area-context` (never `react-native`). Use `@shared/utils/storage` (never import MMKV directly).
- **Theme system**: Never hardcode colors/spacing. Use `src/shared/theme/`.
- **Redux persistence**: Uses MMKV (not AsyncStorage). New slices go in `src/shared/redux/slices/`, add to `rootReducer` and `persistConfig.whitelist`.
- **Named exports only**: No default exports.
- **Branch**: `develop` is the main working branch. Use conventional commits.

## Gotchas

- **Android SocketTimeoutException**: Run `adb reverse tcp:8081 tcp:8081`. Check `network_security_config.xml` exists.
- **iOS Pod failures**: `cd ios && pod deintegrate && pod install`
- **Cache issues**: `npx expo start --clear && rm -rf node_modules/.cache`

## Debug Timer States

```typescript
navigation.navigate('Timer', {
  config: timerConfig,
  debug: { debugTimeRemaining: 5, debugState: 'warning', debugSkipToAlarm: true },
});
```

## TDD Protocol (MANDATORY)

For ALL code changes:
1. Write failing test FIRST
2. Run test — confirm it fails
3. Write minimal code to pass
4. Run test — confirm it passes
5. Refactor if needed

NEVER write production code without a failing test. No exceptions.

## Testing

Jest + React Native Testing Library. PostToolUse hook auto-runs related tests on file edits. Never claim success without running tests.

## Animation/Timing Parity Rule (added 2026-02-09)

When comparing animations across platforms (iOS/Android):
1. **COMPUTE the actual full cycle time** for each platform in a table BEFORE proposing any fix
2. Account for repeat modes: Android `RepeatMode.Reverse` means duration × 2 for full cycle
3. Account for repeat modes: iOS `autoreverses: true` means duration × 2 for full cycle
4. iOS cosine/sinusoidal `period` parameter = full cycle time (NOT half-cycle)
5. **NEVER speculate about "perceptual differences" or frame rates** — if numbers don't match, the numbers are the bug
6. **Compare ALL visual elements** between platforms before editing (don't miss tracking dots, glows, etc.)
7. Present the timing comparison table to the user BEFORE making any edits
