#!/bin/bash

echo "🚫 Checking for hardcoded secrets..."

# Check for common secret patterns
if grep -r -i "password.*=" --include="*.ts" --include="*.js" src/ 2>/dev/null; then
    echo "❌ BLOCKED: Found hardcoded passwords!"
    exit 1
fi

if grep -r -i "secret.*=" --include="*.ts" --include="*.js" src/ 2>/dev/null; then
    echo "❌ BLOCKED: Found hardcoded secrets!"
    exit 1
fi

if grep -r -i "api.*key.*=" --include="*.ts" --include="*.js" src/ 2>/dev/null; then
    echo "❌ BLOCKED: Found hardcoded API keys!"
    exit 1
fi

echo "✅ No hardcoded secrets found"
exit 0
