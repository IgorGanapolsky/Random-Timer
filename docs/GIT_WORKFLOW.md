# Git Workflow for Solo Development

## Core Principles

### 1. Simple Branch Structure
- `main` - Production code
- `develop` - Development work
- Temporary feature branches (only when needed)

### 2. Branch Types
When needed, create branches following these patterns:
```bash
feature/   # New features (e.g., feature/biometrics)
fix/       # Bug fixes (e.g., fix/login-crash)
chore/     # Maintenance (e.g., chore/update-deps)
```

## Daily Workflow

### 1. Small Changes
Work directly in `develop`:
```bash
git checkout develop
# Make changes
git commit -m "fix: resolve login issue"
git push origin develop
```

### 2. Larger Features
Use a feature branch:
```bash
# Create feature branch
./scripts/manage-branches.sh create feature login-biometrics

# Work on code...

# Create PR when done
gh pr create
```

### 3. Code Review
All changes should be reviewed, either:
- Self-review for small changes in `develop`
- PR review for larger features

## Tools & Scripts

### 1. Branch Management
```bash
# Create new branch
./scripts/manage-branches.sh create feature login-biometrics

# Delete branch
./scripts/manage-branches.sh delete feature/old-branch

# List branches
./scripts/manage-branches.sh list

# Clean up merged branches
./scripts/manage-branches.sh cleanup
```

### 2. Parallel Work (via worktrees)
```bash
# Create worktree for feature
git worktree add ../feature-work feature/new-feature

# Clean up worktrees when done
./scripts/cleanup-worktrees.sh
```

## Best Practices

### 1. Commit Messages
Follow conventional commits:
```bash
feat: add biometric login
fix: resolve crash on startup
chore: update dependencies
docs: improve API documentation
test: add unit tests for login
```

### 2. Pull Requests
- Use PRs for significant changes
- Keep PRs focused and small
- Self-merge after self-review
- Delete branches after merge

### 3. Main Branch Protection
- `develop` - Primary work branch
- `main` - Protected, only merge from develop
- Use PR for develop → main

## Emergency Procedures

### 1. Reset to Clean State
```bash
# Switch to develop
git checkout develop

# Reset local changes
git reset --hard origin/develop

# Clean up branches
./scripts/cleanup-worktrees.sh
```

### 2. Recovery
```bash
# Find lost commit
git reflog

# Recover work
git checkout -b recovery-branch <commit-hash>
```

## CI/CD Integration

### 1. Automated Checks
- PRs run tests automatically
- CI checks required to merge
- Auto-merge enabled for safe changes

### 2. Deployment
```bash
# Stage deployment (from develop)
./scripts/deploy.sh staging

# Production deployment (from main)
./scripts/deploy.sh production
```

## Branch Cleanup

### 1. Regular Cleanup
```bash
# Weekly cleanup
./scripts/manage-branches.sh cleanup

# Remove all worktrees
./scripts/cleanup-worktrees.sh
```

### 2. Deep Cleanup
```bash
# Remove all branches except main/develop
./scripts/cleanup-worktrees.sh

# Reset to clean state
git checkout develop
git pull origin develop
```

## Guidelines

1. **Work in `develop`** for most changes
2. **Use feature branches** for big features
3. **Clean up regularly** using provided scripts
4. **Self-review** all changes
5. **Keep history clean** by using conventional commits
6. **Use worktrees** for parallel work
7. **Stay organized** by deleting old branches

## Script Reference

### manage-branches.sh
Branch management script for creating, deleting, and listing branches.

### cleanup-worktrees.sh
Force cleanup script for removing all worktrees and their branches.

## Support

If you need help:
1. Read this document first
2. Check git logs: `git log --oneline -n 10`
3. Use scripts for common operations
4. When in doubt, work in `develop`