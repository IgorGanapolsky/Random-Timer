# 🔐 SecurePass - Next Gen Password Manager

[![Build Status](https://github.com/IgorGanapolsky/SuperPassword/workflows/SuperPassword%20CI%2FCD/badge.svg)](https://github.com/IgorGanapolsky/SuperPassword/actions)
[![Coverage](https://codecov.io/gh/IgorGanapolsky/SuperPassword/branch/develop/graph/badge.svg)](https://codecov.io/gh/IgorGanapolsky/SuperPassword)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Known Vulnerabilities](https://snyk.io/test/github/IgorGanapolsky/SuperPassword/badge.svg)](https://snyk.io/test/github/IgorGanapolsky/SuperPassword)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A professional password generator built with React Native CLI, featuring Material Design and ready for deployment to Google Play Store and Apple App Store.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📁 Project Structure](#-project-structure)
- [🏗️ Development Workflow](#️-development-workflow)
  - [Architecture Overview](#️-architecture-overview)
  - [Multi-Agent System](#-multi-agent-system)
  - [Branch Strategy](#-branch-strategy)
  - [Development Process](#️-development-process)
  - [GitButler CLI & MCP Integration](#-gitbutler-cli--mcp-integration)
- [🏭 Building for Production](#-building-for-production)
- [📱 App Store Configuration](#-app-store-configuration)
- [🔥 Firebase Setup](#-firebase-setup)
- [📊 AdMob Integration](#-admob-integration)
- [🌍 Environment Variables](#-environment-variables)
- [⚙️ CI/CD & Autonomous Ops](#️-cicd--autonomous-ops)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [💬 Support](#-support)

---

## Features

### Core Features (Free)

- ✨ Clean Material Design interface with gradient background
- 🔐 Password generation with customizable length (8-50 characters)
- ⚙️ Toggle options for uppercase, lowercase, numbers, special characters
- 💪 Real-time password strength meter with color coding
- 📋 One-tap copy to clipboard with success animation
- 📜 Password history (last 10 generated passwords) with timestamps
- 🌓 Dark mode toggle with system preference detection
- 📳 Haptic feedback for interactions

### Premium Features ($2.99 one-time purchase)

- 📜 Unlimited password history
- ☁️ Cloud sync across devices
- 🎯 Custom character sets and exclusion rules
- 📦 Bulk password generation (up to 100 at once)
- 📊 Export passwords to CSV
- 🔒 Advanced security settings
- 🚫 No advertisements

## Tech Stack

- React Native CLI
- TypeScript
- React Navigation
- React Native Paper (Material Design)
- @react-native-async-storage/async-storage for local data
- React Native Keychain for secure storage
- Firebase (ready for integration)
- Google AdMob (ready for integration)

## Getting Started

1. **Prerequisites**

   - Node.js 18+
   - Yarn
   - React Native CLI (`npm install -g react-native-cli`)
   - Android Studio (for Android development)
   - Xcode (for iOS development, macOS only)
   - CocoaPods (`sudo gem install cocoapods`)

2. **Install Dependencies**

   ```bash
   # Install JavaScript dependencies
   yarn install

   # Install iOS dependencies
   cd ios && pod install && cd ..
   ```

3. **Start Development Server**

   ```bash
   # Start Metro bundler
   yarn start

   # In a new terminal, run for iOS
   yarn ios

   # Or for Android
   yarn android
   ```

4. **Troubleshooting**
   - If you encounter issues with iOS builds, try:
     ```bash
     cd ios
     pod deintegrate
     pod install
     cd ..
     ```
   - For Android, ensure you have the correct Android SDK versions installed in Android Studio

```bash
npx expo run:android
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # App screens
├── navigation/     # Navigation setup
├── services/       # Services (storage, Firebase, etc.)
├── utils/          # Utility functions
├── hooks/          # Custom React hooks
├── types/          # TypeScript type definitions
├── constants/      # App constants and theme
└── store/          # State management
```

## Building for Production

### Using EAS Build

1. Install EAS CLI:

```bash
npm install -g eas-cli
```

2. Configure EAS:

```bash
eas build:configure
```

3. Build for iOS:

```bash
eas build --platform ios --profile production
```

4. Build for Android:

```bash
eas build --platform android --profile production
```

5. Submit to stores (after first credential setup):

```bash
eas submit --platform ios --profile production
.eas submit --platform android --profile production
```

## App Store Configuration

### Google Play Store

- Package name: `com.securepass.generator`
- Target SDK: 34
- Min SDK: 24 (Android 7.0+)

### Apple App Store

- Bundle ID: `com.securepass.generator`
- Deployment target: iOS 15.1+

## Firebase Setup (Required for production)

1. Create a Firebase project at https://console.firebase.google.com
2. Add iOS and Android apps with the package/bundle IDs
3. Download `google-services.json` (Android) and `GoogleService-Info.plist` (iOS)
4. Place configuration files in the project root
5. Configure Firebase services:
   - Authentication
   - Firestore
   - Remote Config
   - Analytics
   - Crashlytics

## AdMob Setup (Required for monetization)

1. Create AdMob account at https://admob.google.com
2. Create ad units:
   - Banner ad for main screen
   - Interstitial ad for password generations
   - Rewarded video for premium trial
3. Add AdMob App IDs to app configuration
4. Test with test ad unit IDs during development

## Environment Variables

Copy `.env.example` to `.env` and set values. Key settings:

- APP_NAME, APP_SLUG, APP_SCHEME, EXPO_OWNER
- IOS_BUNDLE_ID, ANDROID_PACKAGE
- EAS_PROJECT_ID
- ADMOB_APP_ID_IOS, ADMOB_APP_ID_ANDROID
- SENTRY_DSN

## Development Workflow

This project uses **GitButler virtual branches** with **specialized Claude AI agents** for parallel development. Each agent works in isolation with dedicated worktrees and virtual branches.

### 🏗️ Architecture Overview

![GitButler Architecture](docs/diagrams/gitbutler-architecture.svg)

Our development architecture consists of three layers:

- **GitButler Virtual Branches**: Isolated development streams
- **Physical Worktrees**: Dedicated workspaces per agent
- **Claude AI Agents**: Specialized development roles

### 🤖 Multi-Agent System

![Agent Architecture](docs/diagrams/agent-architecture.svg)

We employ five specialized Claude AI agents:

#### 🔐 **Security Agent**

- **Worktree**: `/worktrees/security`
- **Branch**: `security/*`
- **Focus**: Biometric authentication, encryption, security policies
- **Current Work**: TouchID/FaceID implementation (#179)

#### 🧪 **Testing Agent**

- **Worktree**: `/worktrees/testing`
- **Branch**: `test/*`
- **Focus**: Test coverage, QA automation, performance benchmarks
- **Current Work**: Comprehensive test coverage (#180)

#### 🤖 **Android Agent**

- **Worktree**: `/worktrees/platform/android`
- **Branch**: `platform/android`
- **Focus**: Android-specific features, Play Store compliance
- **Current Work**: Native Android features (#181)

#### 🍎 **iOS Agent**

- **Worktree**: `/worktrees/platform/ios`
- **Branch**: `platform/ios`
- **Focus**: iOS-specific features, App Store compliance
- **Current Work**: Native iOS features (#182)

#### 🐛 **Bugfix Agent**

- **Worktree**: `/worktrees/bugfix`
- **Branch**: `bugfix/*`
- **Focus**: Bug fixes, performance optimization, refactoring
- **Current Work**: Native performance improvements (#183)

### 🔄 Branch Strategy

![Branch Strategy](docs/diagrams/branch-strategy.svg)

We follow a **GitFlow-inspired** strategy enhanced with **GitButler virtual branches**:

#### Protected Branches

- **`main`**: Production releases (protected)
- **`develop`**: Integration branch (protected)

#### Working Branches

- **`feat/*`**: New features → merge to `develop`
- **`fix/*`**: Bug fixes → merge to `develop`
- **`hotfix/*`**: Critical fixes → merge to `main` and `develop`
- **`release/*`**: Release preparation → merge to `main` and `develop`

#### GitButler Integration

- **Virtual Branches**: Each agent works on isolated virtual branches
- **Auto-Merge**: Conflicts resolved with "ours" strategy
- **PR Automation**: Virtual branches automatically create PRs
- **Squash Merge**: Clean history with atomic commits

### 🛠️ Development Process

1. **Task Assignment** → Specialized agent selected
2. **Virtual Branch** → GitButler creates isolated branch
3. **Development** → Agent implements in dedicated worktree
4. **Auto PR** → GitButler creates pull request
5. **Review & Merge** → Human review + automated merge

### 📋 Branch Protection Rules

- **PR Reviews Required**: All changes to `main`/`develop`
- **Status Checks**: CI must pass before merge
- **Linear History**: Enforced for clean git history
- **Auto-Delete**: Head branches removed after merge

### 💬 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

**Example**:

```
feat(auth): implement biometric authentication

- Add FaceID/TouchID support
- Add fallback to PIN
- Add user preference toggle

Closes #123
```

### 🔧 GitButler CLI & MCP Integration

This project integrates **GitButler CLI** with **Model Context Protocol (MCP)** for seamless AI-powered development.

#### GitButler CLI Setup

```bash
# Install GitButler CLI
brew install gitbutler-cli

# Initialize in project
gitbutler init

# Configure AI agents
gitbutler config set ai.provider claude
gitbutler config set ai.model claude-3-5-sonnet
```

#### MCP Server Configuration

The project includes MCP server integration for Claude Code:

```json
// .cursor/config.json
{
  "mcp": {
    "servers": {
      "gitbutler": {
        "command": "gitbutler",
        "args": ["mcp", "server"],
        "env": {
          "GITBUTLER_PROJECT_PATH": "."
        }
      }
    }
  }
}
```

#### Agent Worktree Management

```bash
# Create agent worktrees
./setup-cursor-agents.sh

# List active agents
gitbutler agents list

# Switch agent context
gitbutler agent switch security

# Sync virtual branches
gitbutler sync --all
```

#### CLI Advantages Over UI

- **Automation**: Script complex workflows
- **Integration**: Works with any editor (Cursor, VS Code, etc.)
- **Performance**: Faster than GUI operations
- **CI/CD**: Integrate with automated pipelines
- **Flexibility**: Custom hooks and automation rules

#### MCP Benefits

- **Real-time Context**: Claude sees current branch state
- **Smart Suggestions**: Context-aware code recommendations
- **Conflict Resolution**: AI-assisted merge conflict resolution
- **Code Review**: Automated PR analysis and feedback

#### Available Commands

```bash
# Branch management
gitbutler branch create feat/new-feature
gitbutler branch list --agent security
gitbutler branch merge feat/auth-improvements

# Agent operations
gitbutler agent assign security feat/biometric-auth
gitbutler agent status --all
gitbutler agent sync security

# Automation
gitbutler hooks enable auto-pr
gitbutler hooks enable conflict-resolution
gitbutler workflow run security-audit
```

## CI/CD & Autonomous Ops

- Local hourly autofix: LaunchAgent runs `scripts/autofix-local.sh` to format/lint, commit, and push.
- Cloud hourly autofix: `.github/workflows/autofix.yml` runs Prettier + ESLint and auto-commits.
- CI checks: `.github/workflows/ci.yml` runs tsc, expo-doctor, lint, and prettier on PRs.
- OTA updates (optional): use EAS Update to ship JS-only fixes to channels.

### Sentry (crash and error reporting)

1. Create a Sentry project (React Native) and get DSN.
2. Set env:

```bash
echo "SENTRY_DSN=your_sentry_dsn" >> .env
```

3. For CI/EAS builds, set secrets:

   - GitHub Actions: `SENTRY_AUTH_TOKEN` (org:project release:write)
   - EAS Secrets: `SENTRY_AUTH_TOKEN`

4. Build a release with EAS so source maps upload and crashes link to code:

```bash
eas build --platform ios --profile production
eas build --platform android --profile production
```

### Firebase (Auth, Analytics, Crashlytics, Firestore, Remote Config)

1. Download platform configs from Firebase Console and place at project root:
   - iOS: `GoogleService-Info.plist` (path referenced in `app.config.ts`)
   - Android: `google-services.json` (path referenced in `app.config.ts`)
2. Dev client (required for local dev with native SDKs):
   - iOS: `eas build --profile development --platform ios && eas build:run --platform ios`
   - Android: `eas build --profile development --platform android && eas build:run --platform android`
3. Start server: `npx expo start --dev-client`
4. Verify Crashlytics: trigger `FirebaseService.logError(new Error('test'), { screen: 'Home' })` and check Firebase console.

### Release flow (fully scripted)

```bash
# 1) Set env vars in .env or CI secrets (bundle IDs, EAS_PROJECT_ID, AdMob, Sentry)
# 2) Build
EAS_NO_VCS=1 eas build --platform ios --profile production
EAS_NO_VCS=1 eas build --platform android --profile production
# 3) Submit
EAS_NO_VCS=1 eas submit --platform ios --profile production
EAS_NO_VCS=1 eas submit --platform android --profile production
```

Notes:

- Manage credentials via EAS on first run; subsequent runs use stored credentials.
- For multiple apps, keep a repo per app; parameterize via `app.config.ts` + `.env`.

## Testing

Run tests:

```bash
npm test
```

Run TypeScript type checking:

```bash
npx tsc --noEmit
```

## 🤝 Contributing

We welcome contributions! This project uses a **multi-agent GitButler workflow** with specialized development roles.

### Getting Started

1. **Fork & Clone**

   ```bash
   git clone https://github.com/yourusername/SuperPassword.git
   cd SuperPassword
   ```

2. **Setup Development Environment**

   ```bash
   npm install
   ./setup-cursor-agents.sh
   ```

3. **Choose Your Agent Role**
   - 🔐 **Security**: Authentication, encryption, security policies
   - 🧪 **Testing**: Test coverage, QA automation, benchmarks
   - 🤖 **Android**: Android-specific features, Play Store
   - 🍎 **iOS**: iOS-specific features, App Store
   - 🐛 **Bugfix**: Bug fixes, performance, refactoring

### Agent-Specific Guidelines

#### 🔐 Security Agent

- **Worktree**: `/worktrees/security`
- **Branch Prefix**: `security/`
- **Focus Areas**:
  - Biometric authentication (TouchID/FaceID)
  - Encryption algorithms and key management
  - Security policy implementation
  - Vulnerability assessments
- **Required Reviews**: Security team + 1 other agent
- **Testing**: Security-focused unit tests required

#### 🧪 Testing Agent

- **Worktree**: `/worktrees/testing`
- **Branch Prefix**: `test/`
- **Focus Areas**:
  - Unit test coverage (target: >90%)
  - Integration test suites
  - Performance benchmarking
  - E2E test automation
- **Required Reviews**: 1 feature agent + maintainer
- **Testing**: Meta-testing for test infrastructure

#### 🤖 Android Agent

- **Worktree**: `/worktrees/platform/android`
- **Branch Prefix**: `platform/android`
- **Focus Areas**:
  - Android-specific native features
  - Play Store compliance
  - Android UI/UX patterns
  - Performance optimization
- **Required Reviews**: iOS agent (cross-platform consistency)
- **Testing**: Android device testing required

#### 🍎 iOS Agent

- **Worktree**: `/worktrees/platform/ios`
- **Branch Prefix**: `platform/ios`
- **Focus Areas**:
  - iOS-specific native features
  - App Store compliance
  - iOS UI/UX patterns
  - Performance optimization
- **Required Reviews**: Android agent (cross-platform consistency)
- **Testing**: iOS device testing required

#### 🐛 Bugfix Agent

- **Worktree**: `/worktrees/bugfix`
- **Branch Prefix**: `bugfix/`
- **Focus Areas**:
  - Bug reproduction and fixes
  - Performance improvements
  - Code refactoring
  - Technical debt reduction
- **Required Reviews**: Original feature author + 1 other
- **Testing**: Regression tests required

### Development Process

1. **Issue Assignment**

   - Issues are labeled by agent type
   - Self-assign or request assignment
   - Check agent-specific project boards

2. **Branch Creation**

   ```bash
   # Switch to agent worktree
   cd /worktrees/[agent-name]

   # Create feature branch
   gitbutler branch create [prefix]/[feature-name]
   ```

3. **Development**

   - Follow agent-specific coding standards
   - Write tests for your changes
   - Update documentation as needed

4. **Pull Request**
   - Use agent-specific PR template
   - Include relevant screenshots/demos
   - Tag appropriate reviewers
   - Ensure CI passes

### Code Standards

- **TypeScript**: Strict mode enabled
- **ESLint**: Follow project configuration
- **Prettier**: Auto-formatting on save
- **Commit Messages**: Follow conventional commits
- **Testing**: Minimum 80% coverage for new code

### Review Process

- **Agent Reviews**: Each agent reviews their domain expertise
- **Cross-Agent Reviews**: Platform agents review each other
- **Security Reviews**: Required for authentication/encryption changes
- **Final Approval**: Maintainer approval required for merge

### Documentation

- Update relevant documentation in `/docs`
- Add inline code comments for complex logic
- Update README if adding new features
- Include architecture decision records (ADRs) for major changes

### Questions?

Reach out in the appropriate channel:

- **General**: GitHub Discussions
- **Security**: Private security channel
- **Bugs**: GitHub Issues with `bug` label
- **Features**: GitHub Issues with `enhancement` label

### 📚 Additional Documentation

For more detailed information, see our documentation files:

- **[GitButler Claude Workflow](docs/GITBUTLER_CLAUDE_WORKFLOW.md)** - Detailed workflow setup and agent coordination
- **[Branch Strategy](docs/BRANCH_STRATEGY.md)** - Complete branching model and merge processes
- **[Architecture Diagrams](docs/diagrams/)** - Visual representations of our development architecture

## License

MIT

## Support

For support, email support@securepass.app
