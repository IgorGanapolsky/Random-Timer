/**
 * Typography System
 * Using Inter for UI and Space Mono for timer display
 */

import { Platform, TextStyle } from 'react-native';

// Font families
const fonts = {
  inter: {
    light: 'Inter_300Light',
    regular: 'Inter_400Regular',
    medium: 'Inter_500Medium',
    semiBold: 'Inter_600SemiBold',
    bold: 'Inter_700Bold',
  },
  spaceMono: {
    regular: 'SpaceMono_400Regular',
    bold: 'SpaceMono_700Bold',
  },
  // System fallbacks for web
  system: {
    regular: Platform.select({
      web: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      default: 'System',
    }),
    mono: Platform.select({
      web: '"SF Mono", "Monaco", "Inconsolata", "Fira Mono", monospace',
      default: 'SpaceMono_400Regular',
    }),
  },
} as const;

// Font sizes following 4px base scale
const sizes = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
  '4xl': 36,
  '5xl': 48,
  '6xl': 60,
  '7xl': 72,
  '8xl': 96,
} as const;

// Line heights
const lineHeights = {
  tight: 1.1,
  snug: 1.25,
  normal: 1.5,
  relaxed: 1.625,
  loose: 2,
} as const;

// Typography presets
export const typography = {
  fonts,
  sizes,
  lineHeights,

  // Primary font family
  primary: fonts.inter,

  // Timer display font
  timer: fonts.spaceMono,

  // Presets
  presets: {
    // Headings
    h1: {
      fontFamily: fonts.inter.bold,
      fontSize: sizes['4xl'],
      lineHeight: sizes['4xl'] * lineHeights.tight,
      letterSpacing: -1,
    } as TextStyle,

    h2: {
      fontFamily: fonts.inter.bold,
      fontSize: sizes['3xl'],
      lineHeight: sizes['3xl'] * lineHeights.tight,
      letterSpacing: -0.5,
    } as TextStyle,

    h3: {
      fontFamily: fonts.inter.semiBold,
      fontSize: sizes['2xl'],
      lineHeight: sizes['2xl'] * lineHeights.snug,
    } as TextStyle,

    h4: {
      fontFamily: fonts.inter.semiBold,
      fontSize: sizes.xl,
      lineHeight: sizes.xl * lineHeights.snug,
    } as TextStyle,

    // Body text
    body: {
      fontFamily: fonts.inter.regular,
      fontSize: sizes.base,
      lineHeight: sizes.base * lineHeights.normal,
    } as TextStyle,

    bodyLarge: {
      fontFamily: fonts.inter.regular,
      fontSize: sizes.lg,
      lineHeight: sizes.lg * lineHeights.normal,
    } as TextStyle,

    bodySmall: {
      fontFamily: fonts.inter.regular,
      fontSize: sizes.sm,
      lineHeight: sizes.sm * lineHeights.normal,
    } as TextStyle,

    // Caption/label
    caption: {
      fontFamily: fonts.inter.medium,
      fontSize: sizes.xs,
      lineHeight: sizes.xs * lineHeights.normal,
      letterSpacing: 0.5,
      textTransform: 'uppercase',
    } as TextStyle,

    // Timer display (large monospace)
    timerLarge: {
      fontFamily: fonts.spaceMono.bold,
      fontSize: sizes['7xl'],
      lineHeight: sizes['7xl'] * lineHeights.tight,
      letterSpacing: 2,
    } as TextStyle,

    timerMedium: {
      fontFamily: fonts.spaceMono.regular,
      fontSize: sizes['5xl'],
      lineHeight: sizes['5xl'] * lineHeights.tight,
      letterSpacing: 1,
    } as TextStyle,

    // Button text
    button: {
      fontFamily: fonts.inter.semiBold,
      fontSize: sizes.base,
      lineHeight: sizes.base * lineHeights.tight,
      letterSpacing: 0.5,
    } as TextStyle,

    buttonLarge: {
      fontFamily: fonts.inter.semiBold,
      fontSize: sizes.lg,
      lineHeight: sizes.lg * lineHeights.tight,
      letterSpacing: 0.5,
    } as TextStyle,
  },
} as const;

export type Typography = typeof typography;
