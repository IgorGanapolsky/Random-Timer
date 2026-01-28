/**
 * Screen Component
 * Base screen wrapper with gradient background and safe area handling
 */

import { StyleSheet, View, ViewStyle, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { spacing, useTheme } from '../theme';

interface ScreenProps {
  /** Screen content */
  children: React.ReactNode;
  /** Preset layout: 'auto' (fit content), 'fill' (full height), 'center' (centered content) */
  preset?: 'auto' | 'fill' | 'center';
  /** Custom padding */
  padding?: number;
  /** Ignore safe area (for edge-to-edge designs) */
  unsafe?: boolean;
  /** Custom style */
  style?: ViewStyle;
}

export function Screen({
  children,
  preset = 'fill',
  padding = spacing.lg,
  unsafe = false,
  style,
}: ScreenProps) {
  const insets = useSafeAreaInsets();
  const { colors, isDark } = useTheme();

  const containerStyle: ViewStyle = {
    flex: preset === 'fill' ? 1 : undefined,
    justifyContent: preset === 'center' ? 'center' : undefined,
    alignItems: preset === 'center' ? 'center' : undefined,
    paddingHorizontal: padding,
    paddingTop: unsafe ? 0 : insets.top + spacing.md,
    paddingBottom: unsafe ? 0 : insets.bottom + spacing.md,
  };

  return (
    <LinearGradient
      colors={colors.gradients.background}
      style={styles.gradient}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      <View style={[containerStyle, style]}>{children}</View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
});
