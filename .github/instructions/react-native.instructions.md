# React Native Instructions

applyTo: "src/\*_/_.tsx"

## Component Structure

Create functional components with this structure:

```tsx
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, spacing } from '@shared/theme';

type Props = {
  // props here
};

export function ComponentName({ prop }: Props) {
  return <View style={styles.container}>{/* content */}</View>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.md,
  },
});
```

## Animations

Use `react-native-reanimated` for animations:

```tsx
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
```

## Navigation

Use React Navigation with typed routes:

```tsx
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
```

## Safe Area

ALWAYS use SafeAreaView from the correct package:

```tsx
// CORRECT
import { SafeAreaView } from 'react-native-safe-area-context';

// WRONG - never do this
import { SafeAreaView } from 'react-native';
```

## Expo APIs

Use Expo modules for device features:

```tsx
import * as Haptics from 'expo-haptics';
import { Audio } from 'expo-av';
import * as SplashScreen from 'expo-splash-screen';
```
