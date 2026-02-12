# Random Tactical Timer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: iOS](https://img.shields.io/badge/iOS-18%2B-blue?logo=apple)](native-ios/)
[![Platform: Android](https://img.shields.io/badge/Android-8%2B-green?logo=android)](native-android/)
[![CI](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci.yml)

A timer that goes off at a **random** time within your chosen range. You set min/max — the app picks when. You never know exactly when it will ring.

**Perfect for** workout intervals, reaction drills, team activities, meditation, and anywhere predictable timing defeats the purpose.

<!-- Store badges — uncomment when live
[![Download on the App Store](https://img.shields.io/badge/App_Store-0D96F6?logo=app-store&logoColor=white)](https://apps.apple.com/app/random-tactical-timer/id...)
[![Get it on Google Play](https://img.shields.io/badge/Google_Play-414141?logo=google-play&logoColor=white)](https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer)
-->

---

## Demo

<p align="center">
  <img src="screenshots/android-demo.gif" width="300" alt="Random Tactical Timer Demo — Android" />
</p>

## Screenshots

<p align="center">
  <img src="screenshots/ios-setup.png" width="260" alt="iOS — Timer Setup" />
  &nbsp;&nbsp;
  <img src="screenshots/ios-active.png" width="260" alt="iOS — Timer Active" />
  &nbsp;&nbsp;
  <img src="screenshots/android-setup.png" width="260" alt="Android — Timer Setup" />
</p>

## Features

- **Random Timer Range** — set min/max time (e.g. 1–5 minutes), the app picks a random duration
- **Hidden Mode** — conceals the countdown so you can't anticipate the alarm
- **Loop Mode** — automatically restarts with a new random duration when the timer finishes
- **Lock Screen Display** — iOS Live Activity + Android notification with pause/resume/stop controls
- **Alarm Sounds** — choose Intense or Gentle, with adjustable volume and vibration
- **Premium UI** — glassmorphism dark theme with Material Design 3 Expressive (Android) and SwiftUI (iOS)
- **Background Operation** — reliable notifications even when the app isn't in the foreground
- **Pause, Resume, Reset** — full timer controls on both platforms

## Platforms

| Platform | Technology | Min Version |
|----------|------------|-------------|
| iOS | Swift 6 + SwiftUI | iOS 18+ |
| Android | Kotlin 2.1 + Jetpack Compose (M3) | Android 8+ (API 26) |

## Project Structure

```
native-ios/
├── RandomTimer/
│   └── Sources/
│       ├── App/           # SwiftUI App entry
│       ├── Services/      # TimerManager, Storage, Notifications
│       └── UI/
│           ├── Components/  # CircularTimer, GlassCard, Buttons
│           ├── Screens/     # TimerSetup, ActiveTimer
│           └── Theme/       # Colors
├── RandomTimerWidget/     # Live Activity for Lock Screen
└── SharedModels/          # Shared types

native-android/
└── app/src/main/
    ├── java/.../randomtimer/
    │   ├── domain/        # Models, UseCases, Repository
    │   ├── data/          # DataStore implementation
    │   ├── ui/            # Compose screens & components
    │   ├── service/       # Foreground service
    │   └── di/            # Hilt modules
    └── res/               # Drawables, sounds, themes
```

## Build & Run

### iOS

```bash
cd native-ios
open RandomTimer.xcodeproj
# Build and run from Xcode (Cmd+R)
```

Or via command line:
```bash
xcodebuild -scheme RandomTimer -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

### Android

```bash
cd native-android
./gradlew assembleDebug
./gradlew installDebug
```

## Testing

### Unit Tests

```bash
# Android
cd native-android && ./gradlew test

# iOS
xcodebuild test -scheme RandomTimer -destination 'platform=iOS Simulator,name=iPhone 17 Pro'
```

### E2E Tests (Maestro)

```bash
maestro test .maestro/smoke-test.yaml
```

## Architecture

### iOS
- **MVVM** with `@Observable` TimerManager
- **Live Activities** for Lock Screen / Dynamic Island
- **UserDefaults** for persistence
- **AVAudioPlayer** for alarm sounds

### Android
- **Clean Architecture** with MVVM
- **Hilt** for dependency injection
- **DataStore** for persistence
- **Foreground Service** for reliable countdown
- **MediaPlayer** for alarm sounds
- **Material Design 3 Expressive** with spring-based animations and haptic feedback

## Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0F0A1A` | Deep purple-black |
| Accent | `#8B5CF6` | Purple primary |
| Timer Active | `#10B981` | Emerald — running |
| Timer Complete | `#8B5CF6` | Purple — done |
| Glass | `rgba(255,255,255,0.10)` | Card backgrounds |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Privacy

Random Tactical Timer collects **no personal data**. See [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

## License

[MIT](LICENSE) — Igor Ganapolsky
