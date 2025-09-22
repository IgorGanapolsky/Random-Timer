#!/usr/bin/env bash
set -euo pipefail

echo "🚫 Checking for hardcoded secrets..."

# Patterns tuned to reduce false positives in constants and UI strings
PATTERNS=(
  "(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{6,}['\"]"
  "(secret|seckey|private|priv)\s*[=:]\s*['\"][^'\"]{10,}['\"]"
  "(api[_-]?key|apikey|access[_-]?key|auth[_-]?token|token)\s*[=:]\s*['\"][^'\"]{16,}['\"]"
)

found=false
for pattern in "${PATTERNS[@]}"; do
  if grep -r -E -i "$pattern" \
      --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
      --exclude="*.test.*" --exclude="*.spec.*" \
      --exclude="src/utils/passwordGenerator.ts" \
      src/ 2>/dev/null; then
    echo "❌ Potential secret matched: $pattern"
    found=true
  fi
done

if [[ "$found" == true ]]; then
  echo "❌ COMMIT BLOCKED: Hardcoded secrets detected!"
  exit 1
fi

echo "✅ No hardcoded secrets found"
