# Store changelog policy

Public **What's New** / release-notes copy on Google Play and the App Store must describe user-visible product changes only. Never publish implementation details that expose test hooks, bypass paths, or security-sensitive behavior.

## Scope (enforced in CI)

| Path | Audience |
|------|----------|
| `native-android/fastlane/metadata/android/en-US/changelogs/*.txt` | Play **What's New** (keyed by `versionCode`) |
| `native-ios/fastlane/metadata/en-US/release_notes.txt` | App Store **What's New** |
| `release-notes/*.md` | Internal release ops (still scanned for high-risk terms) |

`scripts/play_publish.py` reads `changelogs/{versionCode}.txt` at upload time. The filename must match the **uploaded** bundle `versionCode` (from `compute_android_release_version_code.py`), not only the `versionCode` in `build.gradle.kts`.

## Denylist (never in store What's New)

- `backdoor`, `secret`, `debug`, `test-only`, `gesture`, `bypass`, `cheat`

Operational terms like `internal distribution` belong in CI/runbooks, not Play/App Store copy. Do not use `internal` or `hidden` to describe unlock bypasses or tester hooks.

Allowed product phrasing: **stealth countdown** / **hidden countdown** in long-form store descriptions only—not unlock bypasses.

## Write user-safe copy

| Do not publish | Publish instead |
|----------------|-----------------|
| Fixed Upgrade to Pro backdoor gesture | Improved Pro upgrade reliability |
| Production Backdoor: Persistent Pro unlock | Improved Pro access for verified beta testers |
| developer backdoor / hidden hold gesture | developer test mode / internal tester flag |
| internal distribution pipeline | beta and store release reliability |

## Enforcement

```bash
python3 scripts/check_store_changelog_policy.py
python3 -m pytest scripts/tests/test_check_store_changelog_policy.py -q
```

`preflight-release.sh` (Android layer 1) runs the checker before Play uploads.

## Beta propagation notes

- Beta **What's New** comes from the changelog file for the **version code on the beta track**, not from `default.txt`.
- If the uploaded `versionCode` has no matching changelog file, Play may keep showing text from an older beta release.
- Devices must be **beta enrolled** and on a lower `versionCode` than the beta artifact to show **Update** (not **Open**).
