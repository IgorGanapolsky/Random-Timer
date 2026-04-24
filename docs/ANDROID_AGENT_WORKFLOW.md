# Android Agent Workflow

Source context: Android Developers Blog, "Android CLI: Build Android apps 3x faster using any agent", published April 16, 2026.

## High-ROI Defaults

1. Run `python3 scripts/android_agent_doctor.py --json` before Android work to read back local Android CLI, SDK, emulator, `adb`, Gradle wrapper, manifest, and SDK-version state.
2. If Android CLI is installed, run `android update` before relying on its commands.
3. Use `android docs search '<topic>'` before changing Android platform behavior, Play policy-sensitive code, build config, target SDK behavior, foreground services, notifications, background execution, or media playback.
4. Use `android skills` before Navigation, edge-to-edge, AGP, XML-to-Compose, R8, emulator, device, or release-build work.
5. Keep release validation anchored in repo commands: `cd native-android && ./gradlew testDebugUnitTest lint`.

## Why This Helps Random Timer

- Faster reproduction loops: Android CLI can manage SDK/device/run flows directly from terminal agents instead of manual IDE navigation.
- Fewer stale Android assumptions: `android docs` grounds agents in current Android, Firebase, Google Developers, and Kotlin guidance.
- Better migrations: official Android Skills provide task-specific guidance for AGP, R8, edge-to-edge, Navigation, Compose, and related changes.
- Lower release risk: this repo still treats store upload/read-back, CI, and Gradle wrapper verification as the source of truth.

## Safe Usage

Do not make Android CLI a hard CI dependency while it is preview tooling. Prefer optional local acceleration and keep CI based on checked-in scripts, Gradle wrapper commands, and explicit read-back verification.

For this app, never remove foreground service permissions just to satisfy upload tooling. Background/screen-off voice callouts depend on foreground service behavior and must instead be declared correctly in Play Console.
