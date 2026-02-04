# Sync Copilot Memory Skill

Trigger: `/sync-memory` or when Copilot seems to forget project patterns

## Description

Reinforce GitHub Copilot's memory by making interactions that teach it project patterns.

## Why This Exists

Copilot Memory (agentic memory) learns from interactions but can forget or miss patterns. This skill:

1. Reviews current Copilot instructions
2. Tests if Copilot remembers them
3. Reinforces patterns through targeted interactions

## Workflow

1. **Check Current Instructions**

   ```bash
   cat .github/copilot-instructions.md
   cat .github/instructions/*.instructions.md
   ```

2. **Test Memory via GitHub API**

   Create a test interaction in Copilot Chat (via Copilot Spaces API if available)
   or document patterns for manual reinforcement.

3. **Generate Reinforcement Prompts**

   Create prompts that teach Copilot the critical rules:

   ```
   Prompt 1: "In this React Native project, how should I import SafeAreaView?"
   Expected: "Import from 'react-native-safe-area-context', not 'react-native'"

   Prompt 2: "How do I access persistent storage in this app?"
   Expected: "Use storage from '@shared/utils/storage', not MMKV directly"

   Prompt 3: "What colors should I use for the timer states?"
   Expected: "colors.timerActive (green), colors.timerWarning (amber), colors.timerDanger (rose)"
   ```

4. **Update Instructions if Needed**

   If Copilot consistently misses a pattern:
   - Add explicit rule to `.github/copilot-instructions.md`
   - Add example to path-specific instructions
   - Create targeted `.instructions.md` file

## Memory Reinforcement Checklist

Run through these in VS Code Copilot Chat periodically:

- [ ] Ask about SafeAreaView import → should mention react-native-safe-area-context
- [ ] Ask about storage → should mention @shared/utils/storage
- [ ] Ask about colors → should reference theme system
- [ ] Ask about spacing → should mention spacing constants
- [ ] Ask about Redux → should mention typed hooks
- [ ] Ask about new screen → should mention Screen component wrapper

## Troubleshooting

**Copilot ignoring instructions?**

1. Verify `.github/copilot-instructions.md` is on default branch
2. Check file is under 8KB (Copilot has size limits)
3. Ensure instructions are clear and specific
4. Try more explicit wording

**Memory not persisting?**

1. Memory is scoped to repository
2. Expires after 28 days of no interaction
3. Check https://github.com/settings/copilot for memory management
4. Consider creating Copilot Space for persistent context

## Manual Memory Sync

If automated approaches fail, manually reinforce by:

1. Opening Copilot Chat in VS Code
2. Asking: "Read the .github/copilot-instructions.md file and summarize the key rules"
3. Then asking project-specific questions to verify understanding
4. Correcting any wrong answers (Copilot learns from corrections)

## Example Session

````
User: /sync-memory

Claude: Testing Copilot memory for Random Timer project...

Testing SafeAreaView knowledge...
✅ Copilot correctly identifies react-native-safe-area-context

Testing storage knowledge...
⚠️ Copilot mentioned MMKV directly, not @shared/utils/storage

Reinforcement needed. Adding explicit example to instructions...

Updated .github/copilot-instructions.md with:
```typescript
// WRONG - never do this
import { MMKV } from 'react-native-mmkv';

// CORRECT - always use the wrapper
import { storage } from '@shared/utils/storage';
````

Memory sync complete. Test again in next session.

```

```
