# Random Timer

Native iOS and Android apps that go off at a random time within a user-defined range.

## Demo

<p align="center">
  <img src="screenshots/android-demo.gif" width="300" alt="Random Timer Demo" />
</p>

## Screenshots

<p align="center">
  <img src="screenshots/ios-setup.png" width="280" alt="iOS Setup Screen" />
  <img src="screenshots/android-setup.png" width="280" alt="Android Setup Screen" />
</p>

## Features

- **Random Timer Range**: Set min/max time range (0-5 minutes), timer picks a random duration
- **Alarm Sound**: Choose Intense or Gentle alarm with volume control
- **Vibration**: Optional haptic feedback during alarm
- **Persistent Settings**: Preferences saved between sessions
- **Premium UI**: Glassmorphism design with dark theme

## Platforms

| Platform | Technology | Min Version |
|----------|------------|-------------|
| iOS | Swift 6 + SwiftUI | iOS 18+ |
| Android | Kotlin 2.1 + Jetpack Compose | Android 8+ (API 26) |

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
- **Live Activities** for Lock Screen/Dynamic Island
- **UserDefaults** for persistence
- **AVAudioPlayer** for alarm sounds

### Android
- **Clean Architecture** with MVVM
- **Hilt** for dependency injection
- **DataStore** for persistence
- **Foreground Service** for reliable countdown
- **MediaPlayer** for alarm sounds

## Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0F0A1A` | Deep purple-black |
| Accent | `#8B5CF6` | Purple primary |
| Timer Active | `#10B981` | Emerald - running |
| Timer Complete | `#8B5CF6` | Purple - done |
| Glass | `rgba(255,255,255,0.10)` | Card backgrounds |

## License

MIT
