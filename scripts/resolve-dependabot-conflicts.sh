#!/bin/bash

# Script to resolve merge conflicts in Dependabot PRs
# This script will help resolve conflicts and enable auto-merge

set -e

echo "🔧 Resolving Dependabot PR conflicts..."

# Get all open Dependabot PRs with conflicts
CONFLICTING_PRS=$(gh pr list --author app/dependabot --state open --json number,title,mergeable --jq '.[] | select(.mergeable == "CONFLICTING") | .number')

if [ -z "$CONFLICTING_PRS" ]; then
    echo "✅ No conflicting Dependabot PRs found"
    exit 0
fi

echo "📋 Found conflicting PRs: $CONFLICTING_PRS"

for pr_number in $CONFLICTING_PRS; do
    echo "🔄 Processing PR #$pr_number..."
    
    # Get PR details
    pr_info=$(gh pr view $pr_number --json title,headRefName,baseRefName)
    title=$(echo $pr_info | jq -r '.title')
    head_ref=$(echo $pr_info | jq -r '.headRefName')
    base_ref=$(echo $pr_info | jq -r '.baseRefName')
    
    echo "  📝 Title: $title"
    echo "  🌿 Head: $head_ref"
    echo "  🎯 Base: $base_ref"
    
    # Checkout the PR branch
    echo "  📥 Checking out PR branch..."
    gh pr checkout $pr_number
    
    # Update base branch
    echo "  🔄 Updating base branch..."
    git fetch origin $base_ref
    git merge origin/$base_ref
    
    # Check if there are conflicts
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo "  ⚠️  Merge conflicts detected. Attempting auto-resolution..."
        
        # Try to resolve conflicts automatically
        # For dependency updates, we usually want to keep the newer version
        git status --porcelain | grep "^UU" | while read status file; do
            echo "    🔧 Resolving conflict in: $file"
            
            # For package.json and package-lock.json, prefer the newer version
            if [[ "$file" == "package.json" ]] || [[ "$file" == "package-lock.json" ]]; then
                echo "    📦 Using newer version for $file"
                git checkout --theirs "$file"
                git add "$file"
            else
                echo "    ⚠️  Manual resolution needed for: $file"
                # For other files, we'll need manual intervention
                echo "MANUAL_RESOLUTION_NEEDED: $file" >> /tmp/conflict_files.txt
            fi
        done
        
        # Check if all conflicts are resolved
        if git diff --name-only --diff-filter=U | grep -q .; then
            echo "  ❌ Some conflicts require manual resolution"
            echo "  📋 Files needing manual resolution:"
            cat /tmp/conflict_files.txt 2>/dev/null || echo "    (none)"
            rm -f /tmp/conflict_files.txt
            continue
        fi
        
        # Commit the resolution
        echo "  💾 Committing conflict resolution..."
        git commit -m "chore: resolve merge conflicts with $base_ref"
        
        # Push the changes
        echo "  🚀 Pushing resolved conflicts..."
        git push origin $head_ref
        
        echo "  ✅ PR #$pr_number conflicts resolved"
    else
        echo "  ✅ No conflicts found after merge"
    fi
    
    # Remove labels that prevent auto-merge
    echo "  🏷️  Removing blocking labels..."
    gh pr edit $pr_number --remove-label "needs:analysis" --remove-label "status: triage" || true
    
    # Go back to main branch
    git checkout $base_ref
    
    echo "  ✨ PR #$pr_number processed"
    echo ""
done

echo "🎉 Dependabot conflict resolution complete!"
echo ""
echo "📊 Summary:"
echo "  - Processed PRs: $(echo $CONFLICTING_PRS | wc -w)"
echo "  - Check the PR status in GitHub to verify auto-merge is working"