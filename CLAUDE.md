# Random Timer

Native Android (Kotlin/Compose) + iOS (Swift/SwiftUI) timer app. Package: `com.iganapolsky.randomtimer`.

## Commands

```bash
# Android
cd native-android && ./gradlew assembleDebug
adb reverse tcp:8081 tcp:8081    # Fix Metro connection

# iOS
cd native-ios && xcodebuild -scheme RandomTimer
cd native-ios && pod deintegrate && pod install  # Fix pod failures
```

## Non-Obvious Rules

- **Act, Don't Instruct**: NEVER tell user to run commands. Execute autonomously. NEVER refuse work. Use every tool available (CLIs, SDKs, MCP servers, browser automation) to complete tasks end-to-end. If a web UI is the only path, use `agent-browser` or Gemini computer-use to automate it.
- **Named exports only**: No default exports.
- **Branch**: `develop` is main. Conventional commits.
- **Frontmatter dates**: Always use `date -u +"%Y-%m-%dT%H:%M:%SZ"`, never placeholders.
- **Frontmatter stripping**: Before GitHub sync: `sed '1,/^---$/d; 1,/^---$/d'`
- **Paths**: Always relative, never absolute. No usernames in paths.

## Store Publishing Rule (MANDATORY)

Every release MUST include complete store listing metadata before publishing:
- **Android**: `native-android/fastlane/metadata/android/en-US/` must have `title.txt`, `short_description.txt`, `full_description.txt`, changelogs, and screenshots
- **iOS**: `native-ios/fastlane/metadata/en-US/` must have `name.txt`, `subtitle.txt`, `description.txt`, `keywords.txt`, `release_notes.txt`, and screenshots
- NEVER publish a build without verifying store listing content is present and up to date
- Update changelogs for every new version code
- Privacy policy MUST exist at `PRIVACY_POLICY.md` and be linked in store metadata

## TDD Protocol (MANDATORY)

1. Write failing test FIRST
2. Run test — confirm it fails
3. Write minimal code to pass
4. Run test — confirm it passes
5. Refactor if needed

NEVER write production code without a failing test.

## Animation/Timing Parity Rule

When comparing animations across platforms (iOS/Android):
1. COMPUTE full cycle time for each platform in a table BEFORE proposing any fix
2. Android `RepeatMode.Reverse` = duration x 2. iOS `autoreverses: true` = duration x 2.
3. iOS cosine/sinusoidal `period` = full cycle time (NOT half-cycle)
4. Compare ALL visual elements between platforms before editing
5. Present timing comparison table BEFORE making edits

## PM Filesystem Convention

PRDs live in `.claude/prds/`, epics in `.claude/epics/`. Navigate with `ls`, `cat`, `grep` — no custom scripts needed. All `/pm:*` commands read the filesystem directly.

## PR Management & System Hygiene (Session Directive)

- Role protocol: agent operates as CTO-level autonomous executor; do not hand off manual steps when automation is possible.
- Session start checklist:
  1. Read `CLAUDE.md` + `AGENTS.md`
  2. Query available RAG/memory sources for relevant lessons
  3. Review open PRs and branches
  4. Check CI status
- PR workflow:
  1. Inspect all open PRs and classify merge readiness
  2. Identify orphan branches (no associated PR) and classify merge/delete/stale
  3. Merge all truly ready PRs only after explicit verification
  4. Clean stale branches/files/log artifacts where safe
  5. Verify CI health on `main` and run available dry-run readiness checks
- Evidence standard:
  - Never claim done without verification read-back
  - Include concrete evidence (PR numbers, merge SHAs, branch counts, CI run URLs/statuses)
  - If blocked, report exact blocker (e.g., conflicts, required review, failing/pending checks)
- Honesty + learning:
  - Report failures immediately
  - Record mistakes/lessons in available project memory/RAG surfaces when integrated
