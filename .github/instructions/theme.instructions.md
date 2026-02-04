# Theme Instructions

applyTo: "src/\*_/_.{ts,tsx}"

## Colors

NEVER hardcode hex values. Use the theme:

```tsx
import { colors } from '@shared/theme';

// Available colors:
colors.background; // #0F0A1A (deep purple)
colors.surface; // elevated surfaces
colors.text; // primary text
colors.textSecondary; // muted text
colors.primary; // accent color
colors.timerActive; // green - timer running
colors.timerWarning; // amber - timer warning
colors.timerDanger; // rose - timer critical

// Glass effects
colors.glass.background; // semi-transparent
colors.glass.border; // glass border
```

## Spacing

NEVER use raw numbers for padding/margin:

```tsx
import { spacing } from '@shared/theme';

// Available spacing:
spacing.xs; // 4
spacing.sm; // 8
spacing.md; // 16
spacing.lg; // 24
spacing.xl; // 32
spacing['2xl']; // 48

// Usage
const styles = StyleSheet.create({
  container: {
    padding: spacing.md, // 16
    marginBottom: spacing.lg, // 24
    gap: spacing.sm, // 8
  },
});
```

## Typography

Use typography constants:

```tsx
import { typography } from '@shared/theme';

// font sizes, weights, line heights
```

## Timing

Use timing constants for animations:

```tsx
import { timing } from '@shared/theme';

// Animation durations
```
