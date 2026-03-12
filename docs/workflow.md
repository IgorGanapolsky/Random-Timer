# Random Timer Agent Workflow

This file is the canonical proof-of-work contract for autonomous changes in this repository.

## Scope

- Default allowed edit scope: `native-android/`, `native-ios/`, `scripts/`, `.github/workflows/`, `.maestro/`, `docs/`, and `wiki/`.
- Always use an isolated git worktree branch for implementation.
- Keep changes tightly scoped to the requested ticket or regression.

## Forbidden Changes

- Never modify secrets, signing identities, or `.env` values in the primary checkout.
- Never bypass required verification and never claim readiness without read-back evidence.
- Never add duplicate test paths or parallel copies of the same contract outside `scripts/tests`.
- Never leave dead stubs, dormant helpers, or outdated workflow references behind.

## Required Proof

Run the relevant commands for the touched surface area and include the direct output in the PR or status report.

### Python / Workflow Contracts

```bash
python3 -m pytest -q scripts/tests/
```

### Android

```bash
cd native-android
./gradlew testDebugUnitTest
```

### iOS

```bash
cd native-ios
xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer -destination 'platform=iOS Simulator,id=<SIMULATOR_ID>' -skip-testing:RandomTimerUITests -quiet CODE_SIGNING_ALLOWED=NO
```

### Mobile Smoke

- If UI or navigation changes: run `maestro test .maestro/ios-smoke-test.yaml`.
- If Android Maestro is unavailable on the current machine, use `adb` + `uiautomator dump` to prove the app launches, shows the expected screen, and transitions to the expected active state.

### Release / Distribution

- If release automation changes: run `python3 scripts/verify_release.py --help` or the touched verification path directly.
- Workflow changes must parse with Ruby YAML read-back.

## Done Criteria

- The requested behavior is implemented on both iOS and Android when parity is expected.
- `scripts/tests/` remains the single canonical Python contract suite.
- No dead code or dead file paths are introduced.
- Any new workflow emits machine-readable artifacts when the change affects release or growth operations.
- The final report includes exact commands run and the observable evidence from those commands.
