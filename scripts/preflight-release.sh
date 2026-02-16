#!/usr/bin/env bash
# preflight-release.sh — Pre-release validation for Random Tactical Timer
# Ensures store listing metadata, privacy policy, changelogs, and build
# integrity are all present and correct before publishing.
#
# Usage:
#   ./scripts/preflight-release.sh --platform android|ios|both [--layer 1|2]
#
# Layers:
#   1 (default) — Metadata & file checks only (fast, no build)
#   2           — Full validation including Gradle/Xcode builds

set -euo pipefail

# ── Globals ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PLATFORM="both"
LAYER=1
ERRORS=()
WARNINGS=()

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ──────────────────────────────────────────────────────────────────

usage() {
  cat <<EOF
Usage: $(basename "$0") --platform android|ios|both [--layer 1|2]

Options:
  --platform   Target platform (required)
  --layer      Validation depth: 1=metadata only, 2=metadata+build (default: 1)
  -h, --help   Show this help
EOF
  exit 0
}

err() { ERRORS+=("❌ $1"); }
warn() { WARNINGS+=("⚠️  $1"); }
info() { echo -e "${CYAN}▸${RESET} $1"; }
header() { echo -e "\n${BOLD}═══ $1 ═══${RESET}"; }

check_file_exists() {
  local path="$1" label="$2"
  if [[ ! -f "$path" ]]; then
    err "$label missing: $path"
    return 1
  fi
  return 0
}

check_file_nonempty() {
  local path="$1" label="$2"
  if [[ ! -f "$path" ]]; then
    err "$label missing: $path"
    return 1
  fi
  if [[ ! -s "$path" ]]; then
    err "$label is empty: $path"
    return 1
  fi
  return 0
}

check_dir_has_files() {
  local dir="$1" pattern="$2" label="$3" min="${4:-1}"
  local count
  count=$(find "$dir" -maxdepth 1 -name "$pattern" -type f 2>/dev/null | wc -l | tr -d ' ')
  if (( count < min )); then
    err "$label: expected at least $min file(s) matching '$pattern' in $dir, found $count"
    return 1
  fi
  return 0
}

# ── Parse args ───────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --layer)    LAYER="$2";    shift 2 ;;
    -h|--help)  usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

if [[ "$PLATFORM" != "android" && "$PLATFORM" != "ios" && "$PLATFORM" != "both" ]]; then
  echo "Invalid --platform: $PLATFORM (must be android, ios, or both)"
  exit 2
fi

if [[ "$LAYER" != "1" && "$LAYER" != "2" ]]; then
  echo "Invalid --layer: $LAYER (must be 1 or 2)"
  exit 2
fi

echo -e "${BOLD}Random Tactical Timer — Preflight Release Check${RESET}"
echo "Platform: $PLATFORM | Layer: $LAYER"
echo "Project:  $PROJECT_ROOT"

# ── Extract versions ─────────────────────────────────────────────────────────

header "Version Detection"

ANDROID_VERSION_NAME=""
ANDROID_VERSION_CODE=""
IOS_VERSION_NAME=""
IOS_BUILD_NUMBER=""

GRADLE_FILE="$PROJECT_ROOT/native-android/app/build.gradle.kts"
if [[ -f "$GRADLE_FILE" ]]; then
  ANDROID_VERSION_NAME=$(sed -n 's/.*versionName *= *"\([^"]*\)".*/\1/p' "$GRADLE_FILE" | head -1)
  ANDROID_VERSION_CODE=$(sed -n 's/.*versionCode *= *\([0-9]*\).*/\1/p' "$GRADLE_FILE" | head -1)
  info "Android: v${ANDROID_VERSION_NAME:-?} (code ${ANDROID_VERSION_CODE:-?})"
fi

PBXPROJ="$PROJECT_ROOT/native-ios/RandomTimer.xcodeproj/project.pbxproj"
if [[ -f "$PBXPROJ" ]]; then
  IOS_VERSION_NAME=$(grep -m1 'MARKETING_VERSION' "$PBXPROJ" | sed -n 's/.*= *\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/p' || true)
  IOS_BUILD_NUMBER=$(grep -m1 'CURRENT_PROJECT_VERSION' "$PBXPROJ" | sed -n 's/.*= *\([0-9]*\).*/\1/p' || true)
  info "iOS:     v${IOS_VERSION_NAME:-?} (build ${IOS_BUILD_NUMBER:-?})"
fi

# Cross-platform version parity warning
if [[ -n "$ANDROID_VERSION_NAME" && -n "$IOS_VERSION_NAME" ]]; then
  if [[ "$ANDROID_VERSION_NAME" != "$IOS_VERSION_NAME" ]]; then
    warn "Version mismatch: Android $ANDROID_VERSION_NAME vs iOS $IOS_VERSION_NAME"
  fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Metadata & File Checks
# ══════════════════════════════════════════════════════════════════════════════

# ── Privacy Policy ───────────────────────────────────────────────────────────

header "Privacy Policy"

PRIVACY_FILE="$PROJECT_ROOT/PRIVACY_POLICY.md"
if check_file_nonempty "$PRIVACY_FILE" "PRIVACY_POLICY.md"; then
  info "PRIVACY_POLICY.md present ($(wc -l < "$PRIVACY_FILE" | tr -d ' ') lines)"
else
  err "PRIVACY_POLICY.md must exist at project root"
fi

# ── Android Metadata ─────────────────────────────────────────────────────────

if [[ "$PLATFORM" == "android" || "$PLATFORM" == "both" ]]; then
  header "Android Store Listing"

  ANDROID_META="$PROJECT_ROOT/native-android/fastlane/metadata/android/en-US"

  # Required text files
  for f in title.txt short_description.txt full_description.txt; do
    check_file_nonempty "$ANDROID_META/$f" "Android $f"
  done

  # Changelog for current version code
  if [[ -n "$ANDROID_VERSION_CODE" ]]; then
    CHANGELOG="$ANDROID_META/changelogs/${ANDROID_VERSION_CODE}.txt"
    if check_file_nonempty "$CHANGELOG" "Android changelog (versionCode $ANDROID_VERSION_CODE)"; then
      info "Changelog $ANDROID_VERSION_CODE.txt present"
    fi
  else
    warn "Could not detect Android versionCode — skipping changelog check"
  fi

  # Screenshots
  SCREENSHOTS_DIR="$ANDROID_META/images/phoneScreenshots"
  if [[ -d "$SCREENSHOTS_DIR" ]]; then
    check_dir_has_files "$SCREENSHOTS_DIR" "*.png" "Android phone screenshots" 3
    SHOT_COUNT=$(find "$SCREENSHOTS_DIR" -name "*.png" -type f | wc -l | tr -d ' ')
    info "Phone screenshots: $SHOT_COUNT found"
  else
    err "Android phoneScreenshots directory missing: $SCREENSHOTS_DIR"
  fi

  # Feature graphic
  FG_DIR="$ANDROID_META/images/featureGraphic"
  if [[ -d "$FG_DIR" ]]; then
    check_dir_has_files "$FG_DIR" "*.png" "Android feature graphic" 1
  else
    warn "Android featureGraphic directory missing (recommended but not required)"
  fi

  # App icon
  check_file_exists "$ANDROID_META/images/icon.png" "Android store icon"

  # Description length checks
  if [[ -f "$ANDROID_META/short_description.txt" ]]; then
    SHORT_LEN=$(wc -c < "$ANDROID_META/short_description.txt" | tr -d ' ')
    if (( SHORT_LEN > 80 )); then
      err "Android short_description.txt exceeds 80 char limit ($SHORT_LEN chars)"
    fi
  fi

  if [[ -f "$ANDROID_META/title.txt" ]]; then
    TITLE_LEN=$(wc -c < "$ANDROID_META/title.txt" | tr -d ' ')
    if (( TITLE_LEN > 30 )); then
      err "Android title.txt exceeds 30 char limit ($TITLE_LEN chars)"
    fi
  fi
fi

# ── iOS Metadata ─────────────────────────────────────────────────────────────

if [[ "$PLATFORM" == "ios" || "$PLATFORM" == "both" ]]; then
  header "iOS Store Listing"

  IOS_META="$PROJECT_ROOT/native-ios/fastlane/metadata/en-US"

  # Required text files
  for f in name.txt subtitle.txt description.txt keywords.txt release_notes.txt; do
    check_file_nonempty "$IOS_META/$f" "iOS $f"
  done

  # Privacy URL (required by App Store)
  if check_file_nonempty "$IOS_META/privacy_url.txt" "iOS privacy_url.txt"; then
    PRIVACY_URL=$(cat "$IOS_META/privacy_url.txt" | tr -d '[:space:]')
    if [[ ! "$PRIVACY_URL" =~ ^https:// ]]; then
      err "iOS privacy_url.txt must start with https:// (got: $PRIVACY_URL)"
    fi
  fi

  # Support URL
  check_file_nonempty "$IOS_META/support_url.txt" "iOS support_url.txt"

  # Screenshots (fastlane stores these in screenshots/, not metadata/)
  # Enforce release-grade App Store coverage:
  # - at least 3 iPhone 6.9"/6.5" screenshots
  # - at least 3 iPad 13" screenshots
  IOS_SCREENSHOTS_DIR="$PROJECT_ROOT/native-ios/fastlane/screenshots/en-US"
  if [[ -d "$IOS_SCREENSHOTS_DIR" ]]; then
    mapfile -t IOS_SCREENSHOTS < <(find "$IOS_SCREENSHOTS_DIR" -maxdepth 1 -name "*.png" -type f 2>/dev/null | sort)
    IOS_SHOTS="${#IOS_SCREENSHOTS[@]}"
    if (( IOS_SHOTS < 6 )); then
      err "iOS screenshots: expected at least 6 PNG files in $IOS_SCREENSHOTS_DIR, found $IOS_SHOTS"
    fi

    IPHONE_CLASS=0
    IPAD_CLASS=0
    OTHER_CLASS=0

    for shot in "${IOS_SCREENSHOTS[@]}"; do
      if ! command -v sips >/dev/null 2>&1; then
        err "sips is required to validate iOS screenshot dimensions"
        break
      fi

      SIZE=$(sips -g pixelWidth -g pixelHeight "$shot" 2>/dev/null | awk '/pixelWidth/{w=$2}/pixelHeight/{h=$2}END{print w"x"h}')
      case "$SIZE" in
        1320x2868|2868x1320|1290x2796|2796x1290|1284x2778|2778x1284|1242x2688|2688x1242)
          IPHONE_CLASS=$((IPHONE_CLASS + 1))
          ;;
        2064x2752|2752x2064|2048x2732|2732x2048)
          IPAD_CLASS=$((IPAD_CLASS + 1))
          ;;
        *)
          OTHER_CLASS=$((OTHER_CLASS + 1))
          ;;
      esac
    done

    info "iOS screenshots: $IOS_SHOTS total (iPhone 6.9/6.5: $IPHONE_CLASS, iPad 13\": $IPAD_CLASS, other: $OTHER_CLASS)"

    if (( IPHONE_CLASS < 3 )); then
      err "iOS screenshots: need >=3 iPhone 6.9\"/6.5\" screenshots (found $IPHONE_CLASS)"
    fi
    if (( IPAD_CLASS < 3 )); then
      err "iOS screenshots: need >=3 iPad 13\" screenshots (found $IPAD_CLASS)"
    fi

    for required_ipad in 5_ipad_setup.png 6_ipad_running.png 7_ipad_stopped.png; do
      if [[ ! -f "$IOS_SCREENSHOTS_DIR/$required_ipad" ]]; then
        err "iOS screenshots: missing required iPad capture $required_ipad"
      fi
    done
  else
    err "iOS screenshots directory missing: $IOS_SCREENSHOTS_DIR"
  fi

  # Field length checks
  if [[ -f "$IOS_META/name.txt" ]]; then
    NAME_LEN=$(wc -c < "$IOS_META/name.txt" | tr -d ' ')
    if (( NAME_LEN > 30 )); then
      err "iOS name.txt exceeds 30 char limit ($NAME_LEN chars)"
    fi
  fi

  if [[ -f "$IOS_META/subtitle.txt" ]]; then
    SUB_LEN=$(wc -c < "$IOS_META/subtitle.txt" | tr -d ' ')
    if (( SUB_LEN > 30 )); then
      err "iOS subtitle.txt exceeds 30 char limit ($SUB_LEN chars)"
    fi
  fi

  if [[ -f "$IOS_META/keywords.txt" ]]; then
    KW_LEN=$(wc -c < "$IOS_META/keywords.txt" | tr -d ' ')
    if (( KW_LEN > 100 )); then
      err "iOS keywords.txt exceeds 100 char limit ($KW_LEN chars)"
    fi
  fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — Build Validation (optional)
# ══════════════════════════════════════════════════════════════════════════════

if [[ "$LAYER" == "2" ]]; then

  if [[ "$PLATFORM" == "android" || "$PLATFORM" == "both" ]]; then
    header "Android Build Check"
    info "Running: ./gradlew assembleDebug (dry-run build)"
    if (cd "$PROJECT_ROOT/native-android" && ./gradlew assembleDebug --no-daemon 2>&1); then
      info "Android debug build succeeded"
    else
      err "Android debug build failed — check Gradle output above"
    fi
  fi

  if [[ "$PLATFORM" == "ios" || "$PLATFORM" == "both" ]]; then
    header "iOS Build Check"
    info "Running: xcodebuild build (debug, no signing)"
    SCHEME="RandomTimer"
    if (cd "$PROJECT_ROOT/native-ios" && xcodebuild build \
        -scheme "$SCHEME" \
        -destination 'generic/platform=iOS Simulator' \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        CODE_SIGNING_ALLOWED=NO \
        -quiet 2>&1); then
      info "iOS debug build succeeded"
    else
      err "iOS debug build failed — check xcodebuild output above"
    fi
  fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════

header "Results"

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo -e "${YELLOW}Warnings (${#WARNINGS[@]}):${RESET}"
  for w in "${WARNINGS[@]}"; do
    echo -e "  ${YELLOW}$w${RESET}"
  done
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo -e "\n${RED}Errors (${#ERRORS[@]}):${RESET}"
  for e in "${ERRORS[@]}"; do
    echo -e "  ${RED}$e${RESET}"
  done
  echo ""
  echo -e "${RED}${BOLD}PREFLIGHT FAILED${RESET} — fix the errors above before releasing."
  exit 1
fi

echo ""
echo -e "${GREEN}${BOLD}✅ PREFLIGHT PASSED${RESET} — all checks clear for ${PLATFORM}."
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo -e "${YELLOW}  (${#WARNINGS[@]} warning(s) — review above)${RESET}"
fi
exit 0
