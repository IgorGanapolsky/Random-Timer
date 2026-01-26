# GitHub Copilot Instructions for Random Timer

This is a React Native/Expo timer app using TypeScript strict mode, Redux Toolkit, and MMKV persistence.

## Critical Rules (MUST follow)

### Restricted Imports
- NEVER use `SafeAreaView` from `react-native`. ALWAYS use `import { SafeAreaView } from 'react-native-safe-area-context'`
- NEVER import `MMKV` directly from `react-native-mmkv`. ALWAYS use `import { storage } from '@shared/utils/storage'`

### Theme System
- NEVER hardcode colors. Use `import { colors } from '@shared/theme'`
- NEVER hardcode spacing values. Use `import { spacing } from '@shared/theme'` with values: xs (4), sm (8), md (16), lg (24), xl (32), 2xl (48)

### TypeScript
- Strict mode is enabled. No implicit any, no implicit returns.
- Use named exports, not default exports.
- Define types near their usage, not in separate files.

## Code Patterns

### React Components
- Functional components only with hooks
- Use `useCallback` for functions passed to children
- Use `useMemo` for expensive computations
- Use named imports: `import { useState, useEffect } from 'react'`

### Styling
- Use `StyleSheet.create()` at bottom of component files
- Follow the glassmorphism dark theme (base: #0F0A1A)

### Redux
- Store location: `src/shared/redux/store.ts`
- Use typed hooks: `useAppDispatch`, `useAppSelector` from `@shared/redux`
- New slices go in `src/shared/redux/slices/`
- Add persistent slices to `persistConfig.whitelist`

## Path Aliases
```typescript
import { Screen, Button } from '@shared/components';
import { colors, spacing } from '@shared/theme';
import { useAppDispatch } from '@shared/redux';
import { TimerSetupScreen } from '@features/timer';
import { AppNavigation } from '@navigation';
```

## Import Order
1. React, React Native
2. Expo packages
3. External libraries
4. @navigation/*
5. @shared/*, @features/*
6. Relative imports

## Screen Components
- Wrap screens with `<Screen preset="fill">` or `<Screen preset="scroll">`
- Handle loading and error states
- Test on both iOS and Android

## Testing
- Jest + React Native Testing Library
- Test files: `*.test.ts` / `*.test.tsx`
- Run: `npm test`
