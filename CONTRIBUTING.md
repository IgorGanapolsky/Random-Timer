# Contributing to Random Tactical Timer

Thanks for your interest in contributing! Here's how to get started.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch from `develop`
4. Make your changes
5. Submit a pull request targeting `develop`

## Development Setup

### Android
```bash
cd native-android
./gradlew assembleDebug
./gradlew test
```

### iOS
```bash
cd native-ios
open RandomTimer.xcodeproj
# Build with Cmd+R in Xcode
```

## Guidelines

- **Branch from `develop`**, not `main`
- Keep branches short-lived (`feature/*`, `fix/*`), and merge back to `develop` quickly
- For production promotion, cut `release/vX.Y.Z` from `develop` and open PR to `main`
- Use conventional commit messages (`feat:`, `fix:`, `docs:`, etc.)
- Write tests for new features
- Keep PRs focused on a single change
- All CI checks must pass before merge

## Reporting Issues

- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for bugs
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) for ideas
- Check existing issues before creating a new one

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful and constructive.
