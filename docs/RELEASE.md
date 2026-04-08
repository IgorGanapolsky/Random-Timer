# Release Process

Formalized release and versioning strategy for Random Tactical Timer (Android + iOS).

## Branch Strategy

```
feature/* ──► develop ──► release/vX.Y.Z ──► main
                (trunk)      (stabilize)      (production truth)
```

| Branch | Purpose | Rules |
|--------|---------|-------|
| `develop` | Primary development trunk | All verified features/fixes merge here fast |
| `release/vX.Y.Z` | Release stabilization branch | Cut from `develop` for store release prep/hotfixes |
| `main` | Production source of truth | Only receives PRs from `release/vX.Y.Z` |
| `feature/*`, `fix/*`, `claude/*` | Short-lived working branches | Branch from `develop`, PR back to `develop` |

**Flow**: `feature/fix` → `develop` → `release/vX.Y.Z` → `main` → tag → release to stores

Version bumps happen on `develop` first, then release branches are cut from `develop`.
`main` always reflects what is live (or being promoted live) in stores.

## Versioning

### Semantic Versioning (X.Y.Z)

| Component | When to bump | Example |
|-----------|-------------|---------|
| **Major (X)** | Breaking changes, major redesign | 1.0.0 → 2.0.0 |
| **Minor (Y)** | New features, significant enhancements | 1.1.0 → 1.2.0 |
| **Patch (Z)** | Bug fixes, minor tweaks | 1.1.0 → 1.1.1 |

### Version Locations

| Platform | File | Field |
|----------|------|-------|
| Android | `native-android/app/build.gradle.kts` | `versionName` (display), `versionCode` (store integer) |
| iOS | `native-ios/RandomTimer.xcodeproj/project.pbxproj` | `MARKETING_VERSION` (display), `CURRENT_PROJECT_VERSION` (build number) |

- **`versionName` / `MARKETING_VERSION`**: Always match across platforms (e.g., "1.2.0")
- **`versionCode`**: Auto-incremented by bump script. Integer, monotonically increasing for Play Store.
- **`CURRENT_PROJECT_VERSION`**: Auto-incremented by fastlane `beta` lane during TestFlight upload. Does NOT need to match Android's versionCode.

## Release Notes Strategy

This repo uses a versioned release-note manifest:

- `release-notes/X.Y.Z.md`

Why this strategy:

- Random Timer is a single consumer app, not a multi-package library monorepo.
- `.changeset/` package fragments are overkill here.
- A single versioned note file gives us one canonical customer-facing summary for GitHub Releases while Android and iOS keep their required store-specific metadata files.

Enforcement:

- `scripts/bump-version.sh` creates `release-notes/X.Y.Z.md`
- `scripts/validate_release_branch.py` blocks `release/vX.Y.Z` and `hotfix/vX.Y.Z` promotion without a filled `release-notes/X.Y.Z.md`
- `scripts/preflight-release.sh` rejects placeholder text in the versioned release note, Android changelog, and iOS `release_notes.txt`
- `native-release.yml` uses `release-notes/X.Y.Z.md` as the canonical GitHub Release body

## Step-by-Step Release Process

### 1. Bump Version on `develop`

```bash
# From develop branch:
./scripts/bump-version.sh 1.2.0

# What this does:
# - Increments Android versionCode (e.g., 5 → 6)
# - Sets Android versionName to "1.2.0"
# - Sets iOS MARKETING_VERSION to "1.2.0" (all build configs)
# - Creates Android changelog placeholder: changelogs/<versionCode>.txt
```

Preview changes first:
```bash
./scripts/bump-version.sh 1.2.0 --dry-run
```

### 2. Update Release Notes

Update platform-specific release notes:

```bash
# Android — edit the changelog for the new versionCode
$EDITOR native-android/fastlane/metadata/android/en-US/changelogs/<versionCode>.txt

# iOS — edit the release notes file
$EDITOR native-ios/fastlane/metadata/en-US/release_notes.txt
```

### 3. Commit to `develop` and Cut a Release Branch

```bash
git add native-android/app/build.gradle.kts \
       native-ios/RandomTimer.xcodeproj/project.pbxproj \
       native-android/fastlane/metadata/android/en-US/changelogs/ \
       native-ios/fastlane/metadata/en-US/release_notes.txt

git commit -m "chore: bump version to 1.2.0"
git push origin develop
```

Cut release branch from `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0
git push -u origin release/v1.2.0
```

Create a PR from `release/v1.2.0` → `main`. The `enforce-release-branch-to-main` workflow enforces:
- PR source must be `release/vX.Y.Z`
- branch version must match Android `versionName`
- branch version must match iOS `MARKETING_VERSION`

### 4. Run Preflight Checks

```bash
# Metadata-only check (fast)
./scripts/preflight-release.sh --platform both --layer 1

# Full check including builds
./scripts/preflight-release.sh --platform both --layer 2
```

This validates:
- Privacy policy exists
- Store listing metadata is complete (titles, descriptions, screenshots)
- Changelog exists for current versionCode
- Field length limits (title ≤30, short desc ≤80, keywords ≤100)
- Screenshot counts and dimensions
- Builds compile successfully (layer 2)

### 5. Merge `release/*` to `main` and Release

After the PR is approved and CI passes:

1. **Merge** the PR (squash merge)
2. **Trigger** the release workflow:

```bash
# Release both platforms to production (default platform is both — use this for versioned releases)
gh workflow run native-release.yml --ref release/vX.Y.Z -f platform=both -f android_track=production

# Or release to beta/alpha first
gh workflow run native-release.yml -f platform=android -f android_track=alpha
gh workflow run native-release.yml -f platform=ios -f confirm_ios_only_release=true

# On a release/v* branch, iOS-only skips Google Play. That is blocked unless you confirm intent:
# gh workflow run native-release.yml --ref release/vX.Y.Z -f platform=ios -f confirm_ios_only_release=true

# To also submit iOS for App Review after TestFlight verification
gh workflow run native-release.yml -f platform=both -f android_track=production -f submit_review=true

# Release/hotfix refs mirror Android to Firebase internal by default.
# Production release now requires prior internal signoff on the exact release SHA:
# 1. Run internal distribution first.
# 2. Approve TestFlight and Firebase internal builds.
# 3. Then run native-release.yml.
gh workflow run internal-distribution.yml --ref release/vX.Y.Z -f ref=release/vX.Y.Z -f target=all
gh workflow run native-release.yml --ref release/vX.Y.Z -f platform=both -f android_track=production
```

### 6. Automatic Post-Release

The `native-release.yml` workflow automatically:

1. **Runs preflight checks** (layer 1 metadata validation)
2. **Builds** the app (AAB for Android, IPA for iOS)
3. **Uploads to stores** (Google Play / TestFlight)
4. **Syncs store metadata** from fastlane directories:
   - **Android**: title, short description, full description, icon, feature graphic, screenshots, changelogs — all from `native-android/fastlane/metadata/android/en-US/`
   - **iOS**: screenshots and metadata via fastlane `deliver`
5. **Verifies** builds landed on the correct store track
6. **Tags the commit** as `vX.Y.Z` (idempotent — skips if tag exists)
7. **Creates a GitHub Release** with combined Android + iOS release notes
8. **Creates annotated GitHub tag + release** on the exact release commit SHA

Release branch safety:

- `platform=ios` on `release/v*` now hard-fails unless `confirm_ios_only_release=true` is passed.
- This prevents silent Google Play skips on versioned releases.

### Delegation Contract Gate

High-impact iOS actions now run through an explicit delegation contract:

- `ios_metadata_sync` (CI/local readiness): requires local listing readiness and no active blockers.
- `ios_submit_for_review` (external submission): requires explicit submit intent plus proven ASC readiness checks with evidence.

Manual command:

```bash
python scripts/delegation_contract.py \
  --operation ios_submit_for_review \
  --asc-ready-json .artifacts/asc_ready.json \
  --intent true \
  --json-out .artifacts/delegation_contract.json \
  --enforce
```

CI/workflows persist contract artifacts under the runner temp directory so every "ready" claim is backed by machine-readable evidence.

## Store Metadata Locations

## Android Firebase App Distribution

Android Firebase App Distribution is documented separately in [FIREBASE_ANDROID_INFRASTRUCTURE.md](FIREBASE_ANDROID_INFRASTRUCTURE.md).

As of April 7, 2026, production release is blocked until CEO signoff exists for internal builds on the exact release SHA. The default `Internal Distribution` target is now `all` so the approval path produces both artifacts you need to review:
- iOS TestFlight
- Android Google Play internal
- Android Firebase App Distribution

Use `target=all_safe` only when Firebase APK delivery must be skipped for explicit debugging reasons.

Target behavior:
- `all`: iOS TestFlight + Android Google Play internal + Android Firebase App Distribution
- `all_safe`: iOS TestFlight + Android Google Play internal
- `ios`: iOS TestFlight only
- `android_play`: Android Google Play internal only
- `android_firebase`: Android Firebase App Distribution only

There is no iOS Firebase App Distribution path in CI. iOS internal delivery is TestFlight-only.

Important: Android runtime Firebase and Android App Distribution do not currently use the same Firebase project. Check that document before rotating any Firebase secret.

### Android (Google Play)

```
native-android/fastlane/metadata/android/en-US/
├── title.txt              # ≤30 chars
├── short_description.txt  # ≤80 chars
├── full_description.txt   # ≤4000 chars
├── video.txt              # YouTube URL (optional)
├── changelogs/
│   ├── 5.txt              # Release notes for versionCode 5
│   └── 6.txt              # Release notes for versionCode 6
└── images/
    ├── icon.png
    ├── featureGraphic/
    │   └── feature.png
    └── phoneScreenshots/
        ├── 1_setup.png
        ├── 2_running.png
        └── ...
```

Metadata is synced to Play Console via the Google Play Publishing API during release. The inline Python script in `native-release.yml` handles: listings update, image upload (icon, feature graphic, screenshots), and changelog attachment.

The Android Fastfile also has a `metadata` lane for manual syncs:
```bash
cd native-android && fastlane metadata
```

### iOS (App Store Connect)

```
native-ios/fastlane/metadata/en-US/
├── name.txt               # ≤30 chars
├── subtitle.txt           # ≤30 chars
├── description.txt        # Full description
├── keywords.txt           # ≤100 chars, comma-separated
├── release_notes.txt      # What's New
├── privacy_url.txt        # Must be https://
└── support_url.txt        # Support link

native-ios/fastlane/screenshots/en-US/
├── 1_setup.png
├── 2_active.png
├── 3_alarm.png
├── 4_running.png
├── 5_ipad_setup.png       # Required iPad screenshots
├── 6_ipad_running.png
└── 7_ipad_stopped.png
```

Metadata is synced via fastlane `deliver` (metadata lane) and `submit_review` lane.

Regenerate screenshot creatives before metadata sync:

```bash
python scripts/generate_ios_store_creatives.py --repo-root . --locale en-US
python scripts/refresh_ios_screenshot_creatives.py
```

## Git Tags

After a successful release, the workflow creates:
- **Git tag**: `vX.Y.Z` (e.g., `v1.2.0`)
- **GitHub Release**: With combined release notes from both platforms

Tags are created only if they don't already exist (idempotent).

To list releases:
```bash
git tag --sort=-v:refname
gh release list
```

## Quick Reference

| Action | Command |
|--------|---------|
| Bump version | `./scripts/bump-version.sh 1.2.0` |
| Dry-run bump | `./scripts/bump-version.sh 1.2.0 --dry-run` |
| Preflight check | `./scripts/preflight-release.sh --platform both --layer 1` |
| Release both | `gh workflow run native-release.yml -f platform=both -f android_track=production` |
| Release Android alpha | `gh workflow run native-release.yml -f platform=android -f android_track=alpha` |
| Release iOS + submit | `gh workflow run native-release.yml -f platform=ios -f confirm_ios_only_release=true -f submit_review=true` |
| List tags | `git tag --sort=-v:refname` |
| List releases | `gh release list` |
