#!/usr/bin/env bash
# bump-version.sh — Bump version across Android + iOS in lockstep
#
# Usage:
#   ./scripts/bump-version.sh <new_version> [--dry-run]
#
# Examples:
#   ./scripts/bump-version.sh 1.2.0           # Bump both platforms to 1.2.0
#   ./scripts/bump-version.sh 1.2.0 --dry-run # Preview changes without writing
#
# What it does:
#   1. Validates semantic version format (X.Y.Z)
#   2. Increments Android versionCode by 1
#   3. Sets Android versionName to <new_version>
#   4. Sets iOS MARKETING_VERSION to <new_version> (all build configs)
#   5. Creates Android changelog placeholder for new versionCode
#   6. Prints summary of all changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Parse args ───────────────────────────────────────────────────────────────

NEW_VERSION=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help)
      echo "Usage: $(basename "$0") <new_version> [--dry-run]"
      echo "  new_version  Semantic version (e.g., 1.2.0)"
      echo "  --dry-run    Preview changes without writing files"
      exit 0
      ;;
    *)
      if [[ -z "$NEW_VERSION" ]]; then
        NEW_VERSION="$1"
      else
        echo "Unknown argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$NEW_VERSION" ]]; then
  echo "Error: new_version is required" >&2
  echo "Usage: $(basename "$0") <new_version> [--dry-run]" >&2
  exit 1
fi

# Validate semver format
if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo -e "${RED}Error: '$NEW_VERSION' is not a valid semantic version (expected X.Y.Z)${RESET}" >&2
  exit 1
fi

# ── Paths ────────────────────────────────────────────────────────────────────

GRADLE_FILE="$PROJECT_ROOT/native-android/app/build.gradle.kts"
PBXPROJ="$PROJECT_ROOT/native-ios/RandomTimer.xcodeproj/project.pbxproj"
ANDROID_CHANGELOGS="$PROJECT_ROOT/native-android/fastlane/metadata/android/en-US/changelogs"

# ── Read current versions ────────────────────────────────────────────────────

echo -e "${BOLD}Version Bump: → $NEW_VERSION${RESET}"
echo ""

if [[ ! -f "$GRADLE_FILE" ]]; then
  echo -e "${RED}Error: $GRADLE_FILE not found${RESET}" >&2
  exit 1
fi

CURRENT_VERSION_NAME=$(sed -n 's/.*versionName *= *"\([^"]*\)".*/\1/p' "$GRADLE_FILE" | head -1)
CURRENT_VERSION_CODE=$(sed -n 's/.*versionCode *= *\([0-9]*\).*/\1/p' "$GRADLE_FILE" | head -1)
NEW_VERSION_CODE=$((CURRENT_VERSION_CODE + 1))

if [[ ! -f "$PBXPROJ" ]]; then
  echo -e "${RED}Error: $PBXPROJ not found${RESET}" >&2
  exit 1
fi

IOS_CURRENT_VERSION=$(grep -m1 'MARKETING_VERSION' "$PBXPROJ" | sed -n 's/.*= *\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/p')

echo -e "${CYAN}Current state:${RESET}"
echo "  Android: v${CURRENT_VERSION_NAME} (code ${CURRENT_VERSION_CODE})"
echo "  iOS:     v${IOS_CURRENT_VERSION}"
echo ""
echo -e "${CYAN}After bump:${RESET}"
echo "  Android: v${NEW_VERSION} (code ${NEW_VERSION_CODE})"
echo "  iOS:     v${NEW_VERSION}"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
  echo -e "${BOLD}[DRY RUN] No files modified.${RESET}"
  exit 0
fi

# ── Android: update build.gradle.kts ─────────────────────────────────────────

sed -i "s/versionCode *= *[0-9]*/versionCode = ${NEW_VERSION_CODE}/" "$GRADLE_FILE"
sed -i "s/versionName *= *\"[^\"]*\"/versionName = \"${NEW_VERSION}\"/" "$GRADLE_FILE"
echo -e "${GREEN}✓${RESET} Android build.gradle.kts updated"

# ── iOS: update project.pbxproj (all build configurations) ──────────────────

sed -i "s/MARKETING_VERSION = [0-9]*\.[0-9]*\.[0-9]*/MARKETING_VERSION = ${NEW_VERSION}/" "$PBXPROJ"
echo -e "${GREEN}✓${RESET} iOS project.pbxproj MARKETING_VERSION updated"

# ── Android changelog placeholder ────────────────────────────────────────────

mkdir -p "$ANDROID_CHANGELOGS"
CHANGELOG_FILE="$ANDROID_CHANGELOGS/${NEW_VERSION_CODE}.txt"
if [[ ! -f "$CHANGELOG_FILE" ]]; then
  echo "What's new in v${NEW_VERSION}" > "$CHANGELOG_FILE"
  echo -e "${GREEN}✓${RESET} Created changelog placeholder: changelogs/${NEW_VERSION_CODE}.txt"
else
  echo -e "${CYAN}▸${RESET} Changelog ${NEW_VERSION_CODE}.txt already exists, skipping"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}Version bump complete.${RESET}"
echo ""
echo "Files modified:"
echo "  - native-android/app/build.gradle.kts"
echo "  - native-ios/RandomTimer.xcodeproj/project.pbxproj"
echo "  - native-android/fastlane/metadata/android/en-US/changelogs/${NEW_VERSION_CODE}.txt"
echo ""
echo "Next steps:"
echo "  1. Update changelogs/${NEW_VERSION_CODE}.txt with actual release notes"
echo "  2. Update native-ios/fastlane/metadata/en-US/release_notes.txt"
echo "  3. git add -A && git commit -m \"chore: bump version to ${NEW_VERSION}\""
echo "  4. PR develop → main, then trigger native-release workflow"
