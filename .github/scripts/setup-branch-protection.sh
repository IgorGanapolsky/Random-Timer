#!/bin/bash

# This script sets up branch protection rules using the GitHub CLI
# Required environment variables:
# - GITHUB_TOKEN with admin:repo scope

# Function to check if GitHub CLI is installed
check_gh() {
  if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed. Please install it first."
    exit 1
  fi
}

# Function to check if logged in to GitHub CLI
check_auth() {
  if ! gh auth status &> /dev/null; then
    echo "Not logged in to GitHub CLI. Please run 'gh auth login' first."
    exit 1
  fi
}

apply_branch_protection() {
  local branch="$1"
  local required_linear_history="$2"

  echo "Setting up ${branch} branch protection..."

  local payload
  payload="$(mktemp)"
  cat > "$payload" <<JSON
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "Autonomous Android Tests", "app_id": -1 },
      { "context": "Autonomous iOS Build Check", "app_id": -1 },
      { "context": "Autonomous Security", "app_id": -1 },
      { "context": "Autonomous AI Review", "app_id": -1 }
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": ${required_linear_history},
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}
JSON

  gh api \
    --method PUT \
    "/repos/$GITHUB_REPOSITORY/branches/${branch}/protection" \
    --input "$payload"

  rm -f "$payload"
}

# Main execution
main() {
  check_gh
  check_auth
  
  echo "Setting up branch protection rules for $GITHUB_REPOSITORY"
  
  # Create or update branch protection rules
  apply_branch_protection "develop" "false"
  apply_branch_protection "main" "true"
  
  echo "Branch protection rules set up successfully!"
}

main "$@"
