# Random Timer - Claude Code Context

## Project Overview

React Native/Expo timer app that goes off at a random time within a user-defined range. Built with TypeScript, Redux Toolkit, and a dark-first glassmorphism UI.

**Package:** `com.iganapolsky.randomtimer`
**Expo SDK:** 54
**React Native:** 0.81.4 (New Architecture enabled)

---

## Commands

### Development
```bash
npm start                    # Start Expo dev client with cache clear
npm run android              # Build and run on Android
npm run ios                  # Build and run on iOS simulator
npm run android:device       # Run on connected Android device
npm run ios:device           # Run on connected iOS device
```

### Code Quality
```bash
npm run compile              # TypeScript check (tsc --noEmit)
npm run lint                 # ESLint with auto-fix
npm run lint:check           # ESLint without fix
npm run format               # Prettier format all files
npm run quality              # Full check: compile + lint + format + test
```

### Testing
```bash
npm test                     # Run Jest tests
npm run test:watch           # Jest in watch mode
npm run test:ci              # Jest with coverage
```

### Build/Native
```bash
npm run prebuild:clean       # Regenerate native projects
npm run pod-install          # Install iOS CocoaPods
adb reverse tcp:8081 tcp:8081  # Fix Android Metro connection
```

---

## Project Structure

```
src/
├── app/                     # App bootstrap and root component
│   ├── App.tsx              # Root component
│   ├── bootstrap/           # Initialization hooks (fonts, splash)
│   └── components/          # App-level providers
├── features/                # Feature modules (domain-driven)
│   ├── timer/
│   │   ├── components/      # Timer-specific UI (CircularTimer, RangeSlider)
│   │   ├── hooks/           # useRandomTimer
│   │   ├── screens/         # TimerSetupScreen, ActiveTimerScreen
│   │   └── services/        # soundService, storageService
│   └── settings/
│       └── screens/         # SettingsScreen
├── navigation/              # React Navigation setup
│   ├── AppNavigation.tsx    # Navigator definition
│   └── index.ts             # Public exports
└── shared/                  # Shared utilities
    ├── components/          # Reusable UI (Button, Text, GlassCard, Screen)
    ├── hooks/               # Shared hooks (useHaptics)
    ├── redux/               # Store, slices, typed hooks
    ├── theme/               # colors, typography, spacing, timing
    ├── test/                # Test setup and mocks
    └── utils/               # Storage adapter (MMKV)
```

---

## Path Aliases

Configured in `tsconfig.json` and `babel.config.js`:

```typescript
import { AppNavigation } from '@navigation';
import { Screen, Button } from '@shared/components';
import { colors, spacing } from '@shared/theme';
import { useAppDispatch } from '@shared/redux';
import { TimerSetupScreen } from '@features/timer';
import logo from '@assets/logo.png';
```

---

## Core Directives

### Act, Don't Instruct
**Never tell the user to do something you can do yourself.** If a task is technically possible (installing packages, running commands, making API calls, purging git history, rotating keys, etc.), execute it directly. Only inform the user of tasks that genuinely require their manual intervention (e.g., logging into a third-party web console that requires their credentials).

### Test-Driven Development
Use Maestro smoke tests to verify changes before considering them complete. Run `maestro test .maestro/` after UI changes. Never guess - verify with tests.

### Security
- Never commit secrets (`google-services.json`, `.env`, API keys)
- If secrets are detected, immediately purge from git history using BFG or git-filter-repo
- Rotate compromised keys via the appropriate cloud console

### Self-Healing CI (MANDATORY)
**CI must never be broken.** This is a non-negotiable requirement.

When CI fails:
1. **Investigate immediately** - check `gh run view --log-failed` for the root cause
2. **Fix the workflow** - make it resilient to missing secrets, flaky tests, or transient failures
3. **Add graceful degradation** - optional features (like Projects v2 sync) should skip with a warning, not fail
4. **Never leave CI red** - a broken CI blocks all development and erodes trust

Patterns for self-healing workflows:
- Check for required secrets before using them; skip gracefully if missing
- Use `continue-on-error: true` for non-critical steps
- Add retry logic for network-dependent operations
- Fail fast on actual code issues, but be resilient to infrastructure issues

---

## Coding Standards

### TypeScript
- **Strict mode enabled** - no implicit any, no implicit returns
- Use named exports, not default exports
- Define types/interfaces near their usage, not in separate files
- Prefer `type` for object shapes, `interface` for extensible contracts

### React/React Native
- **Functional components only** with hooks
- Use `useCallback` for functions passed to children
- Use `useMemo` for expensive computations
- Never import `React` default - use named imports: `import { useState } from 'react'`

### Styling
- Use `StyleSheet.create()` at bottom of component files
- Follow the theme system - never hardcode colors/spacing
- Use `spacing` constants from theme (xs, sm, md, lg, xl, 2xl)

### Import Order (enforced by ESLint)
1. React, React Native
2. Expo packages
3. External libraries
4. `@navigation/*`
5. `@shared/*`, `@features/*`
6. Relative imports

### Restricted Imports
- **Never** use `SafeAreaView` from `react-native` - use `react-native-safe-area-context`
- **Never** import `MMKV` directly - use `@shared/utils/storage`

---

## State Management

### Redux Toolkit + Persist
- Store: `src/shared/redux/store.ts`
- Uses MMKV for persistence (not AsyncStorage)
- Typed hooks: `useAppDispatch`, `useAppSelector`

### Adding a New Slice
1. Create slice in `src/shared/redux/slices/`
2. Add to `rootReducer` in `store.ts`
3. Add to `persistConfig.whitelist` if persistence needed

---

## Theme System

### Colors (`src/shared/theme/colors.ts`)
- Dark-first palette based on deep purple (#0F0A1A)
- Semantic colors: `colors.text`, `colors.primary`, `colors.timerActive`
- Glass effects: `colors.glass.background`, `colors.glass.border`
- Timer states: `timerActive` (green), `timerWarning` (amber), `timerDanger` (rose)

### Spacing
```typescript
spacing.xs   // 4
spacing.sm   // 8
spacing.md   // 16
spacing.lg   // 24
spacing.xl   // 32
spacing['2xl'] // 48
```

---

## Common Issues & Solutions

### Android: SocketTimeoutException / Metro Connection Failed
1. Run `adb reverse tcp:8081 tcp:8081`
2. Ensure `network_security_config.xml` exists in `android/app/src/main/res/xml/`
3. Verify phone and computer on same Wi-Fi network

### iOS: Pod Install Failures
```bash
cd ios && pod deintegrate && pod install
```

### Expo: Clear All Caches
```bash
npx expo start --clear
rm -rf node_modules/.cache
```

### Build: Regenerate Native Projects
```bash
npm run prebuild:clean
```

---

## Testing

- Framework: Jest + React Native Testing Library
- Setup: `src/shared/test/setup.ts`
- Mocks: `src/shared/test/mockFile.ts`
- Pattern: `*.test.ts` / `*.test.tsx` (excluded from tsconfig)

### TDD Enforcement
The PostToolUse hook automatically runs related tests after editing source files:
- Triggered on Write/Edit to `src/**/*.ts` or `src/**/*.tsx`
- Runs `npm test -- --findRelatedTests <file>`
- Runs in background to avoid blocking

### Debug Parameters (Development Only)
Navigate to timer screen with debug overrides for testing specific states:

```typescript
// In development, pass debug params to Timer screen
navigation.navigate('Timer', {
  config: timerConfig,
  debug: {
    debugTimeRemaining: 5,        // Override remaining seconds
    debugState: 'warning',        // Jump to: 'running' | 'warning' | 'danger' | 'complete'
    debugSkipToAlarm: true,       // Skip directly to alarm state
  }
});
```

Useful for Maestro tests to verify specific timer states without waiting.

---

## Adding a New Feature

### Workflow
1. Create feature directory: `src/features/{feature-name}/`
2. Add subdirectories as needed: `components/`, `screens/`, `hooks/`, `services/`
3. Create `index.ts` with public exports
4. Add screen to navigation in `AppNavigation.tsx`
5. If state needed, create Redux slice and wire to store

### New Screen Checklist
- [ ] Use `<Screen preset="fill">` or `preset="scroll"` wrapper
- [ ] Use theme colors and spacing
- [ ] Add to navigation stack
- [ ] Handle loading/error states
- [ ] Test on both iOS and Android

---

## Git Conventions

### Branch: `develop` (main working branch)

### Commit Messages
Follow Conventional Commits:
```
feat: add mystery mode toggle
fix: resolve Android connection timeout
refactor: extract timer logic to custom hook
docs: update README with setup instructions
```

---

## Claude Skills

### Shared Skills (cross-project)
Located in `~/.claude-shared/skills/`, symlinked to `.claude/shared-skills/`

| Skill | Trigger | Description |
|-------|---------|-------------|
| `/setup-android` | Android issues | Fix network security, ADB, Metro connection |
| `/debug-metro` | Metro problems | Nuclear cache clear, kill processes, restart |
| `/new-feature` | Add feature | Scaffold feature module with screens, state |
| `/fix` | Common errors | Quick fixes for RN build/runtime errors |
| `/update-claude-md` | Doc sync | Update CLAUDE.md to match codebase |

### Project-Specific Skills
Located in `.claude/skills/`

| Skill | Trigger | Description |
|-------|---------|-------------|
| `/ralph-mode` | Complex tasks, iterations | Track attempts in ATTEMPTS.md with specs and learnings |
| `/self-heal` | After mistakes | Consolidate lessons from feedback logs |
| `/delegate` | Delegate to Copilot | Create issue and assign to GitHub Copilot coding agent |
| `/copilot-agent` | Full Copilot workflow | Create detailed issue with context for Copilot |
| `/dual-review` | PR review | Synthesize feedback from both Claude and Copilot |
| `/auto-pr` | Autonomous PR | Create PR, wait for CI + AI reviews, auto-merge |
| `/sync-memory` | Copilot memory | Reinforce Copilot's memory of project patterns |
| `/plan-feature` | Ambiguous features | Use Plan mode for requirement discovery before coding |
| `/fresh-start` | Context cleanup | Archive session learnings and start clean context |

### Adding Skills
- **Shared skill:** Create in `~/.claude-shared/skills/`
- **Project skill:** Create in `.claude/skills/`

---

## Autonomous Operation

### Hooks System
The project uses Claude Code hooks for autonomous operation:

| Hook | Purpose |
|------|---------|
| `SessionStart` | Load context, RAG injection, pre-flight checks |
| `UserPromptSubmit` | Validate user prompts |
| `PreToolUse` | Validate commands before execution |
| `PostToolUse` | Auto-RLHF feedback capture, anti-pattern detection, TDD enforcement |
| `PermissionRequest` | Auto-approve safe read operations |
| `Stop` | Verify task completion, log incomplete work |

### Self-Improvement Protocol
When I make a mistake:
1. The error is automatically logged to `.claude/memory/feedback/feedback-log.jsonl`
2. At session start, past mistakes are loaded via RAG
3. Run `/self-heal` periodically to consolidate lessons

### Automatic Anti-Pattern Detection
The PostToolUse hook detects:
- SafeAreaView from wrong import
- Direct MMKV imports
- Hardcoded colors outside theme
- Dangerous bash commands
- Edits to sensitive files

### CI/CD Integration
PRs are automatically reviewed by dual AI systems:

**Claude (via GitHub Actions):**
- Critical checks (imports, theme, TypeScript)
- Style suggestions
- Security scan
- On-demand assist via `@claude` mention in PR comments

**GitHub Copilot (native):**
- Automatic code review on all PRs
- Copilot coding agent for issue implementation
- Copilot Memory for pattern learning

### GitHub Copilot Integration

The project uses GitHub Copilot Pro features:

| Feature | How to Use |
|---------|------------|
| **Coding Agent** | Assign issue to `@copilot` or use `/delegate` skill |
| **Code Review** | Automatic on all PRs |
| **Memory** | Learns patterns from `.github/copilot-instructions.md` |
| **Spaces** | Bundle project context (optional) |

Custom instructions location:
- `.github/copilot-instructions.md` - Main rules
- `.github/instructions/*.instructions.md` - Path-specific rules
