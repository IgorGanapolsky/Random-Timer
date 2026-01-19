# ⏲️ Random Timer

[![Build Status](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A React Native application featuring a Random Timer that triggers events at configurable, random intervals. Built with React Native CLI for deployment to Android and iOS platforms.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📁 Project Structure](#-project-structure)
- [⚙️ GitHub Actions](#️-github-actions)
- [🔮 Future Enhancements](#-future-enhancements)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [💬 Support](#-support)

---

## ✨ Features

### Core Features

- ⏲️ **Random Timer**: Triggers events at configurable, random intervals
- ⚙️ **Customizable Intervals**: Set minimum and maximum time ranges for random triggering
- 🎯 **Event Notifications**: Get notified when the random timer triggers
- 📱 **Cross-Platform**: Works on both Android and iOS devices
- 🎨 **Material Design**: Clean, modern user interface
- 💾 **Persistent Settings**: Your timer preferences are saved between sessions

## 🛠️ Tech Stack

- **React Native CLI** - Native mobile app framework
- **TypeScript** - Type-safe JavaScript
- **React Navigation** - Navigation library for React Native
- **React Native Paper** - Material Design components
- **AsyncStorage** - Local data persistence
- **React Native Haptic Feedback** - Tactile feedback for interactions

## 🚀 Getting Started

Follow these steps to get the Random Timer app running on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Yarn** package manager (`npm install -g yarn`)
- **React Native CLI** (`npm install -g react-native-cli`)
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)
- **CocoaPods** (for iOS dependencies: `sudo gem install cocoapods`)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/IgorGanapolsky/Random-Timer.git
   cd Random-Timer
   ```

2. **Install Dependencies**

   ```bash
   # Install JavaScript dependencies
   yarn install

   # Install iOS dependencies (macOS only)
   cd ios && pod install && cd ..
   ```

### Running the App

#### Start Metro Bundler

```bash
yarn start
```

#### Run on Android

In a new terminal window:

```bash
yarn android
```

Make sure you have an Android emulator running or a physical device connected via USB with debugging enabled.

#### Run on iOS (macOS only)

In a new terminal window:

```bash
yarn ios
```

This will launch the iOS simulator. For physical devices, you'll need to configure code signing in Xcode.

### Troubleshooting

#### iOS Build Issues

If you encounter issues with iOS builds:

```bash
cd ios
pod deintegrate
pod install
cd ..
```

#### Android Build Issues

- Ensure you have the correct Android SDK versions installed in Android Studio
- Check that the `ANDROID_HOME` environment variable is set correctly
- Try cleaning the build: `cd android && ./gradlew clean && cd ..`

#### Metro Bundler Issues

If the bundler cache is causing problems:

```bash
yarn start --reset-cache
```

## 📁 Project Structure

```
Random-Timer/
├── src/
│   ├── components/     # Reusable UI components
│   ├── screens/        # App screens (Timer, Settings, etc.)
│   ├── navigation/     # Navigation configuration
│   ├── services/       # Services (storage, notifications, etc.)
│   ├── utils/          # Utility functions
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript type definitions
│   ├── constants/      # App constants and theme
│   └── contexts/       # React context providers
├── android/            # Android native code
├── ios/                # iOS native code
├── __tests__/          # Test files
└── App.tsx             # App entry point
```

## ⚙️ GitHub Actions

This repository uses GitHub Actions for automated CI/CD workflows.

### Continuous Integration

The CI/CD pipeline runs automatically on every push to `main` and `develop` branches, as well as on pull requests.

#### Validation Workflow

- **Linting**: Checks code style and quality with ESLint
- **Type Checking**: Validates TypeScript types with `tsc`
- **Testing**: Runs the test suite with Jest
- **Coverage**: Uploads test coverage to Codecov

#### Security Checks

- **CodeQL Analysis**: Scans for security vulnerabilities
- **Dependency Review**: Checks for vulnerable dependencies
- **Snyk Scanning**: Additional vulnerability scanning (when configured)

### Android APK Builds

When code is merged into the `develop` branch, GitHub Actions automatically:

1. **Builds the Android APK** using Gradle
2. **Runs all tests** to ensure quality
3. **Uploads the APK** as a build artifact

You can download the built APK from the [Actions tab](https://github.com/IgorGanapolsky/Random-Timer/actions) after a successful build.

#### Build Configuration

- **Target SDK**: 34 (Android 14)
- **Minimum SDK**: 24 (Android 7.0)
- **Architectures**: x86_64, armeabi-v7a, arm64-v8a

### Workflow Files

- `.github/workflows/ci-cd.yml` - Main CI/CD pipeline
- `.github/workflows/eas-build.yml` - EAS build configuration (optional)

### Manual Builds

You can also trigger builds manually from the GitHub Actions tab using the "workflow_dispatch" event.

## 🧪 Testing

### Running Tests

Run the test suite:

```bash
yarn test
```

Run tests with coverage:

```bash
yarn test:coverage
```

Run TypeScript type checking:

```bash
yarn typecheck
```

### Linting and Formatting

Check code style with ESLint:

```bash
yarn lint
```

Auto-fix linting issues:

```bash
yarn lint:fix
```

Format code with Prettier:

```bash
yarn fmt:fix
```

Run all checks:

```bash
yarn validate
```

## 🔮 Future Enhancements

We have exciting plans to expand the Random Timer app with additional features and improvements:

### Planned Features

- **🔐 Code Signing**: Implement proper code signing for production releases to both app stores
- **⏰ Multiple Timers**: Support for running multiple independent random timers simultaneously
- **🎨 UI/UX Improvements**: 
  - Enhanced visual feedback when timers trigger
  - Customizable themes and color schemes
  - Timer history and statistics
  - Visual timer progress indicators
- **🔔 Advanced Notifications**: 
  - Customizable notification sounds
  - Rich notifications with actions
  - Notification categories and priorities
- **📊 Analytics & Insights**: 
  - Track timer usage patterns
  - Statistics dashboard
  - Export timer data
- **⚙️ Advanced Configuration**:
  - Timer presets for common use cases
  - Import/export timer configurations
  - Timer groups and categories
- **🌐 Cloud Sync**: Synchronize timer settings across multiple devices
- **🎯 Event Actions**: Trigger specific actions when timers expire
- **♿ Accessibility**: Enhanced support for screen readers and accessibility features

### Contributing Ideas

Have an idea for a new feature? We welcome suggestions! Please:

1. Check the [issues page](https://github.com/IgorGanapolsky/Random-Timer/issues) for existing feature requests
2. Open a new issue with the `enhancement` label
3. Describe your idea and its potential use cases
4. Join the discussion with other community members

## 🤝 Contributing

We welcome contributions to the Random Timer project!

### How to Contribute

1. **Fork the Repository**

   ```bash
   git clone https://github.com/yourusername/Random-Timer.git
   cd Random-Timer
   ```

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**

   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

4. **Test Your Changes**

   ```bash
   yarn test
   yarn lint
   yarn typecheck
   ```

5. **Commit Your Changes**

   Follow conventional commit format:

   ```bash
   git commit -m "feat: add new timer feature"
   ```

   Commit types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

6. **Push and Create a Pull Request**

   ```bash
   git push origin feature/your-feature-name
   ```

   Then open a pull request on GitHub.

### Code Standards

- **TypeScript**: Use strict typing
- **ESLint**: Follow project linting rules
- **Prettier**: Code is auto-formatted
- **Testing**: Maintain or improve test coverage
- **Documentation**: Update README and inline comments

### Questions?

- **General Questions**: Use GitHub Discussions
- **Bug Reports**: Open an issue with the `bug` label
- **Feature Requests**: Open an issue with the `enhancement` label

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

For support and questions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/IgorGanapolsky/Random-Timer/issues)
- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/IgorGanapolsky/Random-Timer/discussions)

---

Made with ❤️ by the Random Timer team
