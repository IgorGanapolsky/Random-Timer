# Delegate to Copilot Skill

Trigger: `/delegate` or "let copilot handle this" or "assign to copilot"

## Description

Quickly delegate the current task or a described task to GitHub Copilot coding agent.

## Quick Workflow

1. **Parse Task**
   - Extract task description from user message
   - Generate appropriate issue title
   - Add project-specific technical notes

2. **Create & Assign Issue**

   Single API call approach:
   ```bash
   # Create issue with @copilot mention (triggers assignment)
   curl -s -X POST \
     -H "Authorization: token $GITHUB_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     "https://api.github.com/repos/IgorGanapolsky/Random-Timer/issues" \
     -d '{
       "title": "<task-title>",
       "body": "## Task\n<description>\n\n## Project Context\n- React Native/Expo app\n- TypeScript strict mode\n- Redux Toolkit + MMKV\n- Theme: @shared/theme\n\n## Instructions for Copilot\n- Use SafeAreaView from react-native-safe-area-context\n- Use storage from @shared/utils/storage\n- Follow existing patterns in codebase\n\n@copilot implement this",
       "labels": ["copilot-agent"]
     }'
   ```

3. **Report**
   - Return issue URL
   - Explain next steps (Copilot will open draft PR)

## Template Injection

Always append these technical notes to the issue body:

```markdown
## Project Context
- React Native 0.81.4 / Expo SDK 54
- TypeScript strict mode
- Redux Toolkit with MMKV persistence
- Dark-first glassmorphism UI

## Copilot Instructions
Follow .github/copilot-instructions.md:
- SafeAreaView from 'react-native-safe-area-context'
- Storage from '@shared/utils/storage'
- Colors from '@shared/theme'
- Spacing constants (xs, sm, md, lg, xl)
```

## Example Interactions

**Simple delegation:**
```
User: delegate adding a vibration toggle to settings

Claude: Created issue #267: "Add vibration toggle to settings"
        Assigned to Copilot coding agent.

        Copilot will:
        1. Create branch copilot/issue-267
        2. Implement the feature
        3. Open draft PR for your review

        Track progress: https://github.com/IgorGanapolsky/Random-Timer/issues/267
```

**With context:**
```
User: let copilot handle refactoring the timer slice to use RTK Query

Claude: Created issue #268: "Refactor timerSlice to use RTK Query"

        I've included context about:
        - Current slice location: src/shared/redux/slices/timerSlice.ts
        - Persistence requirements (MMKV)
        - Typed hooks pattern

        Copilot will work on this autonomously.
        https://github.com/IgorGanapolsky/Random-Timer/issues/268
```

## When to Use

| Scenario | Use `/delegate` |
|----------|-----------------|
| Simple feature additions | ✅ Yes |
| Bug fixes with clear repro | ✅ Yes |
| Refactoring with clear scope | ✅ Yes |
| Complex architectural changes | ❌ No (do manually) |
| Security-sensitive code | ❌ No (review carefully) |
| Unclear requirements | ❌ No (clarify first) |
