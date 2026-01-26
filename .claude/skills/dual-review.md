# Dual AI Review Skill

Trigger: `/dual-review` or when user opens a PR and wants comprehensive AI review

## Description

Trigger both Claude and Copilot to review a PR, then synthesize their feedback.

## Workflow

1. **Identify PR**
   - Get PR number from user or current branch
   - Fetch PR details via GitHub API

2. **Trigger Reviews**

   Claude review runs automatically via `.github/workflows/claude-review.yml`

   Copilot review runs automatically if auto-review is enabled in repo settings

3. **Fetch Review Comments**
   ```bash
   # Get Claude review (from Actions bot)
   curl -s -H "Authorization: token $GITHUB_PAT" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/pulls/<pr>/comments" \
     | jq '.[] | select(.user.login == "github-actions[bot]")'

   # Get Copilot review
   curl -s -H "Authorization: token $GITHUB_PAT" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/pulls/<pr>/reviews" \
     | jq '.[] | select(.user.login == "copilot[bot]")'
   ```

4. **Synthesize Feedback**
   - Combine unique issues from both reviewers
   - Prioritize by severity (Critical > Style > Suggestion)
   - Create action items

5. **Report Summary**
   ```markdown
   ## AI Review Summary for PR #<number>

   ### Critical Issues (must fix)
   - [Claude] SafeAreaView imported from wrong package (file:line)
   - [Copilot] Missing error handling in async function

   ### Style Issues (should fix)
   - [Claude] Use spacing.md instead of 16
   - [Copilot] Consider extracting to custom hook

   ### Suggestions (nice to have)
   - [Copilot] Add JSDoc comments
   ```

## Checks Performed

| Reviewer | Focus Area |
|----------|------------|
| **Claude** | SafeAreaView imports, MMKV imports, theme usage, Redux patterns, project-specific rules |
| **Copilot** | General code quality, security, performance, best practices, test coverage |

## Example Usage

```
User: /dual-review 264

Claude: Fetching reviews for PR #264...

## AI Review Summary for PR #264

### Claude Review
✅ No critical issues found
- Style: Consider using named export in line 45

### Copilot Review
✅ No critical issues found
- Suggestion: Add unit tests for new function

### Combined Action Items
1. [ ] Add named export (optional)
2. [ ] Add unit tests (recommended)
```
