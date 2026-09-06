# Random Tactical Timer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci.yml)
[![Claude Review](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/claude-review.yml/badge.svg?branch=develop)](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/claude-review.yml)
[![GitHub Copilot Review](https://img.shields.io/badge/GitHub%20Copilot-Review%20Enabled-181717)](docs/pr-review-bots.md)
[![Sentry Seer](https://img.shields.io/badge/Sentry-Seer%20Review-362D59)](docs/pr-review-bots.md)
[![Cursor BugBot](https://img.shields.io/badge/Cursor-BugBot%20Policy-000000)](BUGBOT.md)
[![SonarQube Cloud](https://img.shields.io/badge/SonarQube%20Cloud-Quality%20Gate-4E9BCD)](docs/pr-review-bots.md)
[![iOS](https://img.shields.io/badge/iOS-SwiftUI-blue?logo=apple)](native-ios/)
[![Android](https://img.shields.io/badge/Android-Compose-3DDC84?logo=android)](native-android/)

**Train reaction, not rhythm.** Random interval timer for **MMA, BJJ, boxing, muay thai, kickboxing, HIIT, CrossFit, sparring, tabata, pad work, and tactical drills**. Native **iOS + Android** app: the buzzer fires at a **random** moment inside your range so you cannot anticipate it.

*Store-facing line:* **TRAIN FOR CHAOS. NOT RHYTHM.** — same headline as [App Store description](native-ios/fastlane/metadata/en-US/description.txt) and [Play Store full description](native-android/fastlane/metadata/android/en-US/full_description.txt) (en-US).

| Store | One-liner (en-US) |
|--------|-------------------|
| **App Store** subtitle | [Random HIIT & combat training](native-ios/fastlane/metadata/en-US/subtitle.txt) |
| **Play** short description | [Random tactical timer: MMA, BJJ, boxing, muay thai & HIIT. AI coach voices.](native-android/fastlane/metadata/android/en-US/short_description.txt) |

---

## Screenshots = store assets

Images below are **not** a second set of mocks — they are the **same files** shipped in Fastlane metadata (en-US).

**iPhone** (`native-ios/fastlane/screenshots/en-US/`)

<p align="center">
  <img src="native-ios/fastlane/screenshots/en-US/1_setup.png" width="190" alt="Setup: timer range and start" />
  <img src="native-ios/fastlane/screenshots/en-US/2_active.png" width="190" alt="Active random interval" />
  <img src="native-ios/fastlane/screenshots/en-US/3_alarm.png" width="190" alt="Alarm / cue" />
  <img src="native-ios/fastlane/screenshots/en-US/4_running.png" width="190" alt="Running state" />
</p>

**Android phone** (`native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/`)

<p align="center">
  <img src="native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/1_setup.png" width="190" alt="Setup" />
  <img src="native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/2_active.png" width="190" alt="Active timer" />
  <img src="native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/3_voice.png" width="190" alt="Voice callouts (Pro)" />
  <img src="native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/4_loop.png" width="190" alt="Loop mode" />
</p>

*iPad / additional iOS sizes: same folder (`5_ipad_*` … `7_ipad_*`).*

---

## Diagrams

### Training loop

```mermaid
flowchart LR
  A[Set min/max range] --> B[Start]
  B --> C[Drill / train]
  C --> D[Random cue]
  D --> E{Loop?}
  E -->|Yes| C
  E -->|No| F[Stop / dismiss]
```

### Repository layout

```mermaid
flowchart TB
  subgraph apps [Native apps]
    iOS[iOS — SwiftUI / Live Activities / StoreKit]
    AND[Android — Compose / FGS / Play Billing]
  end
  subgraph meta [Store & screenshots]
    FM[iOS Fastlane metadata + screenshots]
    AM[Android Fastlane metadata + images]
  end
  subgraph auto [Automation]
    PY[scripts/ — Python tooling]
    GA[.github/workflows — CI & release]
  end
  iOS --> FM
  AND --> AM
  apps --> GA
  PY --> GA
```

---

## Tech summary

| Layer | Stack |
|--------|--------|
| **iOS** | Swift 6, SwiftUI, Live Activities, AVFoundation alerts, StoreKit, PostHog |
| **Android** | Kotlin, Jetpack Compose, Hilt, foreground service, Play Billing, PostHog, Firebase crash/analytics |
| **Repo** | Python automation in [`scripts/`](scripts/), workflows in [`.github/workflows/`](.github/workflows/), Fastlane under each `native-*` tree |

## Build & verify

Entry point: **[`Makefile`](Makefile)**.

```bash
make verify
```

Details: iOS `native-ios/` (`xcodebuild`), Android `native-android/` (`./gradlew …`). See Makefile targets for simulators, Maestro, and platform-specific checks.

---

## Docs index

| Doc | Purpose |
|-----|---------|
| [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md) | **Start here** — unified developer journey + capabilities |
| [`docs/developer_capabilities.json`](docs/developer_capabilities.json) | Machine-readable capability catalog (Pages mirror under `marketing/site/`) |
| [`docs/REPO_PROFILE.md`](docs/REPO_PROFILE.md) | **GitHub About** text, topics, links — keep in sync with this README |
| [`docs/pr-review-bots.md`](docs/pr-review-bots.md) | PR review / bot matrix |
| [`docs/north-star-baseline.md`](docs/north-star-baseline.md) | Dated WQTU snapshot (verify live metrics in PostHog) |
| [`CLAUDE.md`](CLAUDE.md) | Operator rules, budgets, release flow |
| [`AGENTS.md`](AGENTS.md) | Agent / AI instructions |
| [`PRIVACY_POLICY.md`](PRIVACY_POLICY.md) | Privacy (linked from store metadata) |

## Repository layout (2026)

| Path | Role |
|------|------|
| [`marketing/site/`](marketing/site/) | **GitHub Pages** deploy root (`daily-growth-publishing` workflow) |
| [`marketing/product-pages/`](marketing/product-pages/) | Product landing HTML + AMP + `llms.txt` (kept out of repo root) |
| [`config/`](config/) | Tooling config (e.g. Sonar properties) |
| [`scripts/shell/`](scripts/shell/) | Bash entrypoints; Python automation stays in [`scripts/`](scripts/) (see [`scripts/README.md`](scripts/README.md)) |

## License

[MIT](LICENSE) — Igor Ganapolsky
