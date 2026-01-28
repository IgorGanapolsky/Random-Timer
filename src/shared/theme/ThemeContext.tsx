/**
 * ThemeContext - Dynamic theming following device preference
 *
 * Best practice for 2026:
 * - Follow system preference (useColorScheme)
 * - No user override needed - respect device settings
 */

import { createContext, useContext, useMemo, ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import { darkTheme, lightTheme } from './colors';

// Union type for both themes
type ThemeColors = typeof darkTheme | typeof lightTheme;

interface ThemeContextValue {
  colors: ThemeColors;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const systemColorScheme = useColorScheme();

  const value = useMemo(() => {
    // Follow device preference, default to dark if null
    const isDark = systemColorScheme !== 'light';

    return {
      colors: isDark ? darkTheme : lightTheme,
      isDark,
    };
  }, [systemColorScheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook to access theme colors and state
 *
 * @example
 * const { colors, isDark } = useTheme();
 * <View style={{ backgroundColor: colors.background }} />
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
