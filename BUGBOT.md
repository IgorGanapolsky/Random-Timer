# BUGBOT.md

Cursor BugBot should review this repository with a bug-first mindset.

## Priorities

1. Find correctness bugs, regressions, and release risks before style issues.
2. Prioritize store, billing, timer, alarm, audio, CI, and secret-handling changes.
3. Flag any change that could break App Store / Play Store delivery, internal distribution, or tester access.
4. Flag security-sensitive workflow patterns, especially untrusted PR execution, token exposure, and unsafe shell usage.

## High-Risk Areas

- `native-android/` timer execution, foreground service, billing, and release automation
- `native-ios/` timer logic, audio session handling, notifications, and App Store delivery
- `.github/workflows/` release, CI, and branch-protection logic
- `scripts/` store ops, metadata sync, and release verification

## Review Rules

- Prefer findings with file and line references.
- Do not spend review budget on pure style unless it creates user-facing risk, CI breakage, or security exposure.
- Call out missing tests when business logic, release logic, or runtime behavior changes.
- Treat false-success CI paths as high severity.
- Treat broken store-readiness claims as high severity.

## What Good Feedback Looks Like

- Specific, reproducible, and tied to code behavior
- Focused on bugs, regressions, security, or operational failures
- Minimal speculation; prefer evidence from the diff
