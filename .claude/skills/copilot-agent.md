# Copilot Agent Skill

Trigger: `/copilot-agent` or when user wants to delegate a task to GitHub Copilot

## Description

Create a GitHub issue and assign it to Copilot coding agent for autonomous implementation.

## Workflow

1. **Gather Requirements**
   - Ask user what they want implemented (if not clear)
   - Determine issue title and description
   - Identify acceptance criteria

2. **Create GitHub Issue**

   ```bash
   curl -s -X POST \
     -H "Authorization: token $GITHUB_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/issues" \
     -d '{
       "title": "<issue-title>",
       "body": "<description>\n\n## Acceptance Criteria\n- [ ] <criteria>\n\n## Technical Notes\n- Follow SafeAreaView import from react-native-safe-area-context\n- Use @shared/utils/storage for MMKV\n- Use theme colors from @shared/theme\n\n@copilot implement this",
       "labels": ["copilot-agent", "automation"]
     }'
   ```

3. **Assign to Copilot**

   ```bash
   curl -s -X POST \
     -H "Authorization: token $GITHUB_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/issues/<issue-number>/assignees" \
     -d '{"assignees": ["copilot"]}'
   ```

4. **Monitor Progress**
   - Copilot will create a `copilot/` branch
   - Copilot will open a draft PR
   - User reviews and requests changes via PR comments

## Example Usage

User: "Create a settings screen with a dark mode toggle"

Claude creates issue:

```
Title: Add settings screen with dark mode toggle

## Description
Create a new SettingsScreen component with a toggle to switch between dark and light themes.

## Acceptance Criteria
- [ ] New screen at src/features/settings/screens/SettingsScreen.tsx
- [ ] Dark mode toggle using Switch component
- [ ] Persist preference using Redux + MMKV
- [ ] Add to navigation stack

## Technical Notes
- Use <Screen preset="scroll"> wrapper
- Import theme from @shared/theme
- Add slice to persistConfig.whitelist

@copilot implement this
```

## Notes

- Copilot coding agent works autonomously in GitHub Actions environment
- It has read-only access to repo, can only push to `copilot/` branches
- Review the draft PR carefully before merging
- Comment on the PR to request changes
