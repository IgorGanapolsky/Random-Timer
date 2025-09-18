#!/bin/bash

# Super Simple Commit Helper
# Just run this after making changes

MESSAGE="${1:-Auto-commit at $(date)}"

echo "🔄 Adding all changes..."
git add .

echo "📝 Committing with message: $MESSAGE"
git commit -m "$MESSAGE"

echo "✅ Done! Changes committed to git."

# Show recent commits
echo ""
echo "📋 Recent commits:"
git log --oneline -3
