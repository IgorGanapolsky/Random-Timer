# Device E2E tests (local)

Run on a **connected Android device** and **booted iOS Simulator** with Maestro installed.

## One-time macOS bootstrap

```bash
./scripts/device-tests/bootstrap-macos.sh
```

## Prerequisites

- Android: `brew install openjdk@21` (Gradle 9.4 + `jlink`) — or use bootstrap script
- iOS: Xcode + Simulator; Maestro CLI; **idb-companion** (`brew install facebook/fb/idb-companion`)
- Maestro: `brew install openjdk` (JVM for Maestro; macOS `/usr/bin/java` is a stub)

## Commands

```bash
# Android device + Maestro flows + ADB shell tests
./scripts/device-tests/run-all.sh

# Android Maestro only (skip APK build)
./scripts/device-tests/run-all.sh --maestro-only

# iOS Simulator — XCUITest E2E (recommended locally)
./scripts/device-tests/run-ios-simulator.sh
# or explicitly:
./scripts/device-tests/run-ios-xctest.sh

# iOS Maestro flows (CI parity; may need Maestro+iOS 26 pairing)
./scripts/device-tests/run-ios-simulator.sh --maestro --smoke-only

# Both platforms
./scripts/device-tests/run-e2e.sh
```

## Flows

- **Android Maestro:** `.maestro/smoke-test.yaml`, `ci-smoke-test.yaml`, persistence, alarm, activation, pro-lock regressions (see `run-all.sh`).
- **iOS Maestro:** `.maestro/ios-smoke-test.yaml` and paywall/pro regressions (see `run-ios-simulator.sh`).

## Local Gradle note

`native-android/gradle/gradle-daemon-jvm.properties` pins JetBrains Runtime 21; foojay cannot download it on **macOS arm64**. Device-test scripts temporarily move that file aside and use Homebrew **openjdk@21** for builds.
