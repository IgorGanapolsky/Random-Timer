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
  "BUGBOT.md"
  "GEMINI.md"
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

secret_hits=$(git grep -l -E 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}' -- '*.md' '*.sh' '*.yml' '*.yaml' '*.json' '*.kt' '*.swift' '*.py' 2>/dev/null | grep -v '.gitleaks.toml' | grep -v 'pre-push' | grep -v 'hygiene-check' || true)
if [ -n "$secret_hits" ]; then
  while IFS= read -r hit; do
    error "Possible committed secret in: $hit"
  done <<< "$secret_hits"
fi

temp_hits=$(git grep -l '/private/tmp/' -- '*.md' '*.sh' '*.yml' '*.yaml' '*.json' '*.kt' '*.swift' '*.py' 2>/dev/null | grep -v 'hygiene-check' || true)
if [ -n "$temp_hits" ]; then
  while IFS= read -r hit; do
    warn "Machine-local temp path found in: $hit"
  done <<< "$temp_hits"
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

# ── 7. AGENTS.md and CLAUDE.md exist ────────────────────────────────
echo "7. Required files present"

[ ! -f "$REPO_ROOT/CLAUDE.md" ] && error "Missing CLAUDE.md"
[ ! -f "$REPO_ROOT/AGENTS.md" ] && error "Missing AGENTS.md"
[ ! -f "$REPO_ROOT/README.md" ] && error "Missing README.md"

# ── 8. English-only rule verification ───────────────────────────────
echo "8. English-only AI config"
if [ -f "$REPO_ROOT/scripts/shell/verify-english-rules.sh" ]; then
  bash "$REPO_ROOT/scripts/shell/verify-english-rules.sh" || error "verify-english-rules.sh failed"
else
  warn "scripts/shell/verify-english-rules.sh missing"
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
