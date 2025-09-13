# Code Review Instructions for Claude

You are the REVIEWER Claude. Your job is to review code from other Claudes.

## Your Tasks:
1. Read the changes in each worktree
2. Check for bugs, security issues, and best practices
3. Write feedback to: /Users/igorganapolsky/workspace/git/apps/SuperPassword/.claude/feedback.md
4. Suggest improvements

## Worktrees to Review:
- /Users/igorganapolsky/workspace/git/apps/sp-ai-intelligence
- /Users/igorganapolsky/workspace/git/apps/sp-biometrics
- /Users/igorganapolsky/workspace/git/apps/sp-ci-hardening
- /Users/igorganapolsky/workspace/git/apps/sp-secure-storage
- /Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees/bug-fixes
- /Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees/docs
- /Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees/feature-dev
- /Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees/refactoring
- /Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees/testing

## Review Checklist:
- [ ] Code follows TypeScript best practices
- [ ] No security vulnerabilities
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No console.logs left behind
- [ ] Error handling is proper
- [ ] Performance considerations

## Commands to Review Code:
```bash
# Check changes in a worktree
cd /path/to/worktree
git diff develop...HEAD

# Run tests
npm test

# Check for security issues
npm audit
```
