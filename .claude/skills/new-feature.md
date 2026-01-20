# Skill: New Feature

Scaffold a complete feature module following the project's architecture conventions.

## Trigger
User invokes `/new-feature` or asks to create/add a new feature.

## Workflow

### 1. Gather Requirements
Ask the user:
- **Feature name** (e.g., "notifications", "history", "presets")
- **Needs screens?** (yes/no)
- **Needs Redux state?** (yes/no)
- **Needs services?** (yes/no)

### 2. Create Directory Structure
```bash
mkdir -p src/features/{feature-name}/components
mkdir -p src/features/{feature-name}/screens
mkdir -p src/features/{feature-name}/hooks
mkdir -p src/features/{feature-name}/services
```

### 3. Generate Feature Index
Create `src/features/{feature-name}/index.ts`:
```typescript
// {FeatureName} Feature
// Public exports

export * from './screens';
// export * from './components';
// export * from './hooks';
```

### 4. Generate Screen (if needed)
Create `src/features/{feature-name}/screens/{FeatureName}Screen.tsx`:
```typescript
/**
 * {FeatureName}Screen
 * [Brief description]
 */

import { StyleSheet, View } from 'react-native';

import { Screen, Text } from '@shared/components';
import { colors, spacing } from '@shared/theme';

export function {FeatureName}Screen() {
  return (
    <Screen preset="fill">
      <View style={styles.container}>
        <Text preset="h1">{FeatureName}</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
```

Create `src/features/{feature-name}/screens/index.ts`:
```typescript
export * from './{FeatureName}Screen';
```

### 5. Generate Redux Slice (if needed)
Create `src/shared/redux/slices/{featureName}Slice.ts`:
```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface {FeatureName}State {
  // Define state shape
}

const initialState: {FeatureName}State = {
  // Initial values
};

const {featureName}Slice = createSlice({
  name: '{featureName}',
  initialState,
  reducers: {
    // Add reducers
  },
});

export const { } = {featureName}Slice.actions;
export const {featureName}Reducer = {featureName}Slice.reducer;
```

Then update `src/shared/redux/store.ts`:
- Import the new reducer
- Add to `rootReducer`
- Add to `persistConfig.whitelist` if persistence needed

### 6. Add to Navigation
Update `src/navigation/AppNavigation.tsx`:
- Import the new screen
- Add to stack navigator
- Add TypeScript types to `RootStackParamList`

### 7. Update CLAUDE.md
Invoke `/update-claude-md` to document the new feature.

## Success Criteria
- Feature directory created with proper structure
- Screen renders without errors
- Navigation works
- Redux state (if any) persists correctly

## Output
List all created files and provide next steps for implementation.
