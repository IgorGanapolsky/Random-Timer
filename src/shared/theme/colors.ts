/**
 * Premium 2026 Color Palette
 * Supports both light and dark themes with vibrant accents and glassmorphism
 */

const palette = {
  // Deep purple-black backgrounds (dark mode)
  background900: '#0F0A1A',
  background800: '#1A1325',
  background700: '#251D30',
  background600: '#302840',

  // Light backgrounds (light mode)
  light100: '#FFFFFF',
  light200: '#F8F7FC',
  light300: '#F0EEF5',
  light400: '#E8E5F0',

  // Neutral grays
  neutral100: '#FFFFFF',
  neutral200: '#F5F5F7',
  neutral300: '#E5E5EA',
  neutral400: '#C7C7CC',
  neutral500: '#8E8E93',
  neutral600: '#636366',
  neutral700: '#48484A',
  neutral800: '#3A3A3C',
  neutral900: '#2C2C2E',

  // Primary - Indigo
  primary100: '#E0E7FF',
  primary200: '#C7D2FE',
  primary300: '#A5B4FC',
  primary400: '#818CF8',
  primary500: '#6366F1',
  primary600: '#4F46E5',
  primary700: '#4338CA',

  // Secondary - Purple
  secondary100: '#F3E8FF',
  secondary200: '#E9D5FF',
  secondary300: '#D8B4FE',
  secondary400: '#C084FC',
  secondary500: '#A855F7',
  secondary600: '#9333EA',
  secondary700: '#7E22CE',

  // Success - Emerald (time remaining)
  success100: '#D1FAE5',
  success200: '#A7F3D0',
  success300: '#6EE7B7',
  success400: '#34D399',
  success500: '#10B981',
  success600: '#059669',

  // Warning - Amber (almost done)
  warning100: '#FEF3C7',
  warning200: '#FDE68A',
  warning300: '#FCD34D',
  warning400: '#FBBF24',
  warning500: '#F59E0B',
  warning600: '#D97706',

  // Danger - Rose (expired/alarm)
  danger100: '#FFE4E6',
  danger200: '#FECDD3',
  danger300: '#FDA4AF',
  danger400: '#FB7185',
  danger500: '#F43F5E',
  danger600: '#E11D48',
} as const;

/**
 * Dark theme colors
 */
export const darkTheme = {
  palette,
  transparent: 'rgba(0, 0, 0, 0)',

  // Text
  text: palette.neutral100,
  textDim: palette.neutral400,
  textMuted: palette.neutral500,

  // Backgrounds
  background: palette.background900,
  backgroundSecondary: palette.background800,

  // Borders
  border: palette.neutral700,
  borderLight: palette.neutral800,

  // Timer states
  timerActive: palette.success500,
  timerWarning: palette.warning500,
  timerDanger: palette.danger500,
  timerIdle: palette.neutral500,

  // Primary actions
  primary: palette.primary500,
  primaryLight: palette.primary400,
  primaryDark: palette.primary600,

  // Glassmorphism
  glass: {
    background: 'rgba(255, 255, 255, 0.08)',
    backgroundLight: 'rgba(255, 255, 255, 0.12)',
    border: 'rgba(255, 255, 255, 0.15)',
    borderLight: 'rgba(255, 255, 255, 0.25)',
  },

  // Gradients (start, end)
  gradients: {
    background: [palette.background900, palette.background700] as const,
    primary: [palette.primary500, palette.secondary500] as const,
    timerActive: [palette.success400, palette.success600] as const,
    timerWarning: [palette.warning400, palette.warning600] as const,
    timerDanger: [palette.danger400, palette.danger600] as const,
  },
} as const;

/**
 * Light theme colors
 */
export const lightTheme = {
  palette,
  transparent: 'rgba(0, 0, 0, 0)',

  // Text - dark text on light backgrounds
  text: palette.neutral900,
  textDim: palette.neutral600,
  textMuted: palette.neutral500,

  // Backgrounds
  background: palette.light200,
  backgroundSecondary: palette.light300,

  // Borders
  border: palette.neutral300,
  borderLight: palette.neutral200,

  // Timer states
  timerActive: palette.success600,
  timerWarning: palette.warning600,
  timerDanger: palette.danger600,
  timerIdle: palette.neutral500,

  // Primary actions
  primary: palette.primary600,
  primaryLight: palette.primary500,
  primaryDark: palette.primary700,

  // Glassmorphism - white cards with subtle shadows for light mode
  glass: {
    background: 'rgba(255, 255, 255, 0.85)',
    backgroundLight: 'rgba(255, 255, 255, 0.95)',
    border: 'rgba(255, 255, 255, 0.9)',
    borderLight: 'rgba(0, 0, 0, 0.05)',
  },

  // Gradients (start, end)
  gradients: {
    background: [palette.light200, palette.light400] as const,
    primary: [palette.primary500, palette.secondary500] as const,
    timerActive: [palette.success400, palette.success600] as const,
    timerWarning: [palette.warning400, palette.warning600] as const,
    timerDanger: [palette.danger400, palette.danger600] as const,
  },
} as const;

export type ThemeColors = typeof darkTheme;

/**
 * @deprecated Use useTheme() hook instead for dynamic theming
 * Kept for backwards compatibility during migration
 */
export const colors = darkTheme;

export type Colors = typeof colors;
