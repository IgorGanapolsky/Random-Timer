#!/usr/bin/env bash
# Codebase hygiene audit — run by pre-push hook and Claude skill
# Exit 1 on failure to block push

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ERRORS=0
WARNINGS=0

error() { echo "  ❌ $1"; ERRORS=$((ERRORS + 1)); }
warn()  { echo "  ⚠️  $1"; WARNINGS=$((WARNINGS + 1)); }

echo "=== Codebase Hygiene Check ==="

# ── 1. Root folder cleanliness ──────────────────────────────────────
echo ""
echo "1. Root folder cleanliness"

ALLOWED_ROOT_MD=(
  "README.md"
  "CLAUDE.md"
  "AGENTS.md"
  "CONTRIBUTING.md"
  "CODE_OF_CONDUCT.md"
  "SECURITY.md"
  "PRIVACY_POLICY.md"
  "LICENSE"
)

for f in "$REPO_ROOT"/*.md; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  found=false
  for allowed in "${ALLOWED_ROOT_MD[@]}"; do
    [ "$base" = "$allowed" ] && found=true && break
  done
  if [ "$found" = false ]; then
    error "Unexpected .md in root: $base (move to docs/ or .claude/)"
  fi
done

# ── 2. No absolute paths in tracked files ───────────────────────────
echo "2. No absolute paths in tracked files"

abs_hits=$(git grep -l '/Users/\|/home/\|C:\\Users\\' -- '*.md' '*.sh' '*.yml' '*.yaml' '*.json' '*.toml' '*.kt' '*.swift' 2>/dev/null | grep -v '.git/' | grep -v 'hygiene-check.sh' || true)
if [ -n "$abs_hits" ]; then
  while IFS= read -r hit; do
    error "Absolute path found in: $hit"
  done <<< "$abs_hits"
fi

# ── 3. No secrets or temp paths ─────────────────────────────────────
echo "3. No secrets or temp paths"

secret_hits=$(git grep -l 'PRIVATE_KEY\|SECRET_KEY\|password.*=\|/private/tmp/\|/tmp/' -- '*.md' '*.sh' '*.yml' '*.yaml' '*.json' '*.kt' '*.swift' 2>/dev/null | grep -v '.gitleaks.toml' | grep -v 'pre-push' | grep -v 'hygiene-check' || true)
if [ -n "$secret_hits" ]; then
  while IFS= read -r hit; do
    warn "Possible secret or temp-path leak in: $hit"
  done <<< "$secret_hits"
fi

# ── 4. No stale publishing docs ─────────────────────────────────────
echo "4. No stale publishing docs in root"

for stale in COMPLETE_PUBLISHING.md PUBLISH_STATUS.md MANUAL_PUBLISH_STEPS.md; do
  [ -f "$REPO_ROOT/$stale" ] && error "Stale doc in root: $stale (should have been deleted)"
done

# ── 5. Native subdirs clean of loose docs ────────────────────────────
echo "5. Native subdirs documentation check"

for dir in native-ios native-android; do
  count=$(find "$REPO_ROOT/$dir" -maxdepth 1 -name '*.md' -not -name 'README.md' | wc -l | tr -d ' ')
  if [ "$count" -gt 3 ]; then
    warn "$dir/ has $count .md files at top level — consider consolidating to docs/"
  fi
done

# ── 6. Build artifacts not tracked ──────────────────────────────────
echo "6. No build artifacts tracked"

build_tracked=$(git ls-files -- '*.apk' '*.aab' '*.ipa' '*.dSYM' '*.class' '*.o' 'native-android/app/build/*' 'native-ios/build/*' 2>/dev/null || true)
if [ -n "$build_tracked" ]; then
  while IFS= read -r hit; do
    error "Build artifact tracked in git: $hit"
  done <<< "$build_tracked"
fi

# ── 7. Required files present ──────────────────────────────────────
echo "7. Required files present"

[ ! -f "$REPO_ROOT/CLAUDE.md" ] && error "Missing CLAUDE.md"
[ ! -f "$REPO_ROOT/AGENTS.md" ] && error "Missing AGENTS.md"
[ ! -f "$REPO_ROOT/README.md" ] && error "Missing README.md"

# ── 8. UI/UX Tactical Standards (2026) ─────────────────────────────
echo "8. UI/UX Tactical Standards (2026)"

# Android: NudgeButton should use tactical symbols \u2212 and +
nudge_def="native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
if [ -f "$nudge_def" ]; then
  if ! grep -q "\\\\u2212\|−" "$nudge_def"; then
    error "Android NudgeButton does not use tactical symbol \u2212"
  fi
fi

# iOS: CircularTimerView should use 16pt stroke width
ios_timer_def="native-ios/RandomTimer/Sources/UI/Components/CircularTimerView.swift"
if [ -f "$ios_timer_def" ]; then
  if ! grep -q "strokeWidth: CGFloat = 16" "$ios_timer_def"; then
    error "iOS CircularTimerView uses incorrect strokeWidth — 2026 'heavy' standard is 16"
  fi
fi

# Button height check (56dp/pt standard)
android_button_def="native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/components/PrimaryButton.kt"
if [ -f "$android_button_def" ]; then
  if ! grep -q "height(56.dp)" "$android_button_def"; then
    error "Android PrimaryButton does not follow the 56dp height standard"
  fi
fi

ios_button_def="native-ios/RandomTimer/Sources/UI/Components/PrimaryButton.swift"
if [ -f "$ios_button_def" ]; then
  if ! grep -q "frame(height: 56)" "$ios_button_def"; then
    error "iOS PrimaryButton does not follow the 56pt height standard"
  fi
fi

# ── Summary ─────────────────────────────────────────────────────────
echo ""
echo "=== Results ==="
echo "Errors: $ERRORS | Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "❌ Hygiene check FAILED — fix errors before pushing."
  exit 1
fi

if [ "$WARNINGS" -gt 0 ]; then
  echo "⚠️  Passed with warnings."
fi

echo "✅ Hygiene check passed."
exit 0
