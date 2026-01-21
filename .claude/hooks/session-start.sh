#!/usr/bin/env bash
# Session Start Hook - Random Timer
# Simplified version without RAG (can be enhanced later)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================"
echo "SESSION START - Random Timer"
echo "============================================"
echo ""

# Show git status
echo "📊 Git Status:"
git -C "$PROJECT_ROOT" status --short 2>/dev/null | head -10
echo ""

# Show recent commits
echo "📝 Recent commits:"
git -C "$PROJECT_ROOT" log --oneline -5 2>/dev/null
echo ""

echo "============================================"
echo "MANDATORY RULES FOR THIS SESSION:"
echo "============================================"
echo ""
echo "1. ACT, DON'T INSTRUCT - Execute tasks directly"
echo ""
echo "2. TDD with Maestro - Run smoke tests after UI changes:"
echo "   maestro test .maestro/"
echo ""
echo "3. Before EVERY commit: git status --short"
echo ""
echo "4. Never commit secrets (google-services.json, .env, API keys)"
echo ""
echo "5. Use Trunk for linting: trunk check"
echo ""
echo "============================================"
echo ""
