# Device E2E tests (local)

Run on a **connected Android device** and **booted iOS Simulator** with Maestro installed.
Prefer **vphone-cli** (virtual iPhone) or Simulator over the CEO physical handset.

## One-time macOS bootstrap

```bash
./scripts/device-tests/bootstrap-macos.sh
```

## Prerequisites

- Android: `brew install openjdk@21` (Gradle 9.4 + `jlink`) — or use bootstrap script
- iOS: Xcode + Simulator; Maestro CLI; **idb-companion** (`brew install facebook/fb/idb-companion`)
- Maestro: `brew install openjdk` (JVM for Maestro; macOS `/usr/bin/java` is a stub)
- Optional virtual iPhone: [vphone-cli](https://github.com/Lakr233/vphone-cli) (`brew install --cask zqxwce/tap/vphone-cli` after `brew trust zqxwce/tap`)

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

# Optional virtual iPhone lane (fails closed → Simulator if SIP/AMFI blocked)
python3 scripts/vphone_doctor.py --json
./scripts/device-tests/run-ios-vphone.sh --smoke-only

# Both platforms
./scripts/device-tests/run-e2e.sh
```

## vphone-cli lane (optional)

Upstream boots a PV=3 research guest. Host needs Apple Silicon + SIP/AMFI relaxation (CEO Recovery step — agents must not flip SIP without explicit acceptance).

| Doctor status | Meaning | Agent action |
| --- | --- | --- |
| `blocked_sip_amfi` / `blocked_cli_missing` | Not ready | Use Simulator; do not claim vphone E2E |
| `ready_for_vm_create` | Host OK, no VM yet | `vphone-cli vm create rtt-qa -V regular` (prefer `less`/`regular`) |
| `ready_for_launch` | VM exists | Launch + set `VPHONE_MAESTRO_DEVICE`; claim only on Maestro EXIT=0 |

Skill: `.claude/skills/vphone-cli-ios-lane/SKILL.md`.

## Flows

- **Android Maestro:** `.maestro/smoke-test.yaml`, `ci-smoke-test.yaml`, persistence, alarm, activation, pro-lock regressions (see `run-all.sh`).
- **iOS Maestro:** `.maestro/ios-smoke-test.yaml` and paywall/pro regressions (see `run-ios-simulator.sh`).
- **vphone (optional):** same iOS Maestro smoke when doctor + Maestro device binding succeed.

## Local Gradle note

`native-android/gradle/gradle-daemon-jvm.properties` pins JetBrains Runtime 21; foojay cannot download it on **macOS arm64**. Device-test scripts temporarily move that file aside and use Homebrew **openjdk@21** for builds.
