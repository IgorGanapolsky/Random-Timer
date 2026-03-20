#!/usr/bin/env bash
# Verify English-only configuration. Exit 0 if pass, 1 if fail.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IGOR="$(dirname "$REPO")"
PASS=0
FAIL=0

check() {
  local file="$1"
  local pattern="$2"
  local desc="$3"
  if [ -f "$file" ] && grep -q "$pattern" "$file"; then
    echo "PASS: $desc ($file)"
    PASS=$((PASS + 1))
    return 0
  else
    echo "FAIL: $desc ($file)"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

echo "=== English rule verification ==="
echo ""

check "$REPO/CLAUDE.md" "Interaction Language" "Random-Timer CLAUDE.md has Interaction Language section"
check "$REPO/CLAUDE.md" "use \*\*English\*\*" "Random-Timer CLAUDE.md specifies English"
check "$REPO/AGENTS.md" "Interaction Language" "Random-Timer AGENTS.md has Interaction Language section"
check "$REPO/AGENTS.md" "use \*\*English\*\*" "Random-Timer AGENTS.md specifies English"
check "$REPO/.cursor/rules/english-only.mdc" "alwaysApply: true" "Cursor rule has alwaysApply"
check "$REPO/.cursor/rules/english-only.mdc" "English" "Cursor rule specifies English"

if [ -f "$IGOR/CLAUDE.md" ]; then
  check "$IGOR/CLAUDE.md" "Interaction Language" "igor CLAUDE.md has Interaction Language section"
  check "$IGOR/CLAUDE.md" "use \*\*English\*\*" "igor CLAUDE.md specifies English"
fi
if [ -f "$IGOR/AGENTS.md" ]; then
  check "$IGOR/AGENTS.md" "Interaction Language" "igor AGENTS.md has Interaction Language section"
  check "$IGOR/AGENTS.md" "use \*\*English\*\*" "igor AGENTS.md specifies English"
fi

echo ""
echo "--- Chinese rule check (must find none in active instruction files) ---"

FILES_TO_SCAN=(
  "$REPO/CLAUDE.md"
  "$REPO/AGENTS.md"
  "$REPO/.cursor/rules/english-only.mdc"
)

if [ -f "$IGOR/CLAUDE.md" ]; then
  FILES_TO_SCAN+=("$IGOR/CLAUDE.md")
fi
if [ -f "$IGOR/AGENTS.md" ]; then
  FILES_TO_SCAN+=("$IGOR/AGENTS.md")
fi

CHINESE=()
for file in "${FILES_TO_SCAN[@]}"; do
  if [ -f "$file" ] && grep -q "交互语言\|一律使用" "$file"; then
    CHINESE+=("$file")
  fi
done

if [ "${#CHINESE[@]}" -eq 0 ]; then
  echo "PASS: No Chinese language rule found in active instruction files"
  PASS=$((PASS + 1))
else
  printf 'FAIL: Chinese rule found in:\n'
  printf '%s\n' "${CHINESE[@]}"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
