# Auto PR Skill

Trigger: `/auto-pr` or when user wants to create and merge a PR autonomously

## Description

Create a PR, wait for CI + AI reviews to pass, then auto-merge. Full autonomous workflow.

## Workflow

1. **Pre-flight Checks**
   ```bash
   # Ensure we're on a feature branch
   git branch --show-current

   # Ensure no uncommitted changes
   git status --porcelain

   # Ensure branch is ahead of develop
   git rev-list --count develop..HEAD
   ```

2. **Push Branch**
   ```bash
   git push -u origin $(git branch --show-current)
   ```

3. **Create PR**
   ```bash
   curl -s -X POST \
     -H "Authorization: token $GITHUB_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/pulls" \
     -d '{
       "title": "<title>",
       "head": "<branch>",
       "base": "develop",
       "body": "<body>"
     }'
   ```

4. **Wait for Checks**
   ```bash
   # Poll for check status
   while true; do
     status=$(curl -s -H "Authorization: token $GITHUB_PAT" \
       "https://api.github.com/repos/IgorGanapolsky/Random-Timer/commits/<sha>/check-runs" \
       | jq -r '.check_runs | map(.conclusion) | unique | if contains(["failure"]) then "failed" elif contains([null]) then "pending" else "passed" end')

     if [ "$status" = "passed" ]; then break; fi
     if [ "$status" = "failed" ]; then echo "CI failed"; exit 1; fi
     sleep 30
   done
   ```

5. **Check AI Reviews**
   - Wait for Claude review comment
   - Wait for Copilot review (if enabled)
   - Verify no REQUEST_CHANGES

6. **Auto-Merge**
   ```bash
   curl -s -X PUT \
     -H "Authorization: token $GITHUB_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/pulls/<pr>/merge" \
     -d '{"merge_method": "squash"}'
   ```

7. **Cleanup**
   ```bash
   git checkout develop
   git pull origin develop
   git branch -d <feature-branch>
   ```

## Safety Guards

- **Never auto-merge if:**
  - CI checks failed
  - Claude review says REQUEST_CHANGES
  - Copilot review says REQUEST_CHANGES
  - PR has merge conflicts

- **Always require:**
  - At least one passing CI check
  - No unresolved review comments

## Example Usage

```
User: /auto-pr

Claude: Starting autonomous PR workflow...

1. ✅ Pre-flight checks passed
2. ✅ Pushed branch feature/add-haptics
3. ✅ Created PR #265
4. ⏳ Waiting for CI... (2 jobs running)
5. ✅ CI passed (Quality: ✓, Security: ✓)
6. ⏳ Waiting for AI reviews...
7. ✅ Claude: APPROVE
8. ✅ Copilot: APPROVE
9. ✅ Merged PR #265 to develop
10. ✅ Cleaned up local branch

PR #265 merged: https://github.com/IgorGanapolsky/Random-Timer/pull/265
```

## Flags

- `--no-wait`: Create PR but don't wait for checks (manual merge later)
- `--draft`: Create as draft PR
- `--force`: Merge even with style warnings (not critical issues)
