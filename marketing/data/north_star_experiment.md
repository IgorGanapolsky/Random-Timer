# North Star Experiment

- Generated: 2026-03-09T20:05:42+00:00
- Status: proposed
- Primary Focus: activation

## Experiment
- Slug: activation-default-range-0-30
- Target Metric: open_to_completed_rate
- Hypothesis: Starting every user at 0s to 30s reduces setup friction and increases first completion rate.
- Owner: product

## Measurement Plan
- Metric: open_to_completed_rate
- Baseline: 0.023
- Target: 0.25
- Gap: 0.227
- Window Days: 30

## Recommended Next Action
Ship the default 0s to 30s timer range and verify first-session completion improves.

## Implementation Checklist
- Keep launch defaults at 0s to 30s on both platforms.
- Keep setup-screen previews visible for countdown and drill voice cues.
- Verify first-session setup and start flow with smoke evidence on iOS and Android.

## Proof Commands
- `python3 -m pytest -q scripts/tests/`
- `cd native-android && ./gradlew testDebugUnitTest`
- `cd native-ios && xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer -destination 'platform=iOS Simulator,id=<SIMULATOR_ID>' -skip-testing:RandomTimerUITests -quiet CODE_SIGNING_ALLOWED=NO`

## Warnings
- none
