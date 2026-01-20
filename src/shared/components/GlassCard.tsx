/**
 * GlassCard Component
 * Glassmorphism card with blur effect and subtle border
 */

import { StyleSheet, View, ViewStyle, Platform } from 'react-native';
import { BlurView } from 'expo-blur';
import Animated, {
  useAnimatedStyle,
  withSpring,
  useSharedValue,
  withDelay,
} from 'react-native-reanimated';
import { useEffect } from 'react';

import { spacing, radii, shadows, timing, useTheme } from '../theme';

interface GlassCardProps {
  children: React.ReactNode;
  /** Card padding */
  padding?: number;
  /** Border radius */
  radius?: number;
  /** Show border glow effect */
  glow?: boolean;
  /** Glow color */
  glowColor?: string;
  /** Animate entrance */
  animate?: boolean;
  /** Animation delay (ms) */
  delay?: number;
  /** Custom style */
  style?: ViewStyle;
}

export function GlassCard({
  children,
  padding = spacing.lg,
  radius = radii.xl,
  glow = false,
  glowColor,
  animate = true,
  delay = 0,
  style,
}: GlassCardProps) {
  const { colors, isDark } = useTheme();
  const resolvedGlowColor = glowColor ?? colors.primary;

  const scale = useSharedValue(animate ? 0.9 : 1);
  const opacity = useSharedValue(animate ? 0 : 1);

  useEffect(() => {
    if (animate) {
      scale.value = withDelay(delay, withSpring(1, timing.spring.gentle));
      opacity.value = withDelay(delay, withSpring(1, timing.spring.gentle));
    }
  }, [animate, delay, scale, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const cardContent = (
    <View
      style={[
        styles.content,
        {
          padding,
          borderRadius: radius,
          backgroundColor: colors.glass.background,
          borderColor: colors.glass.border,
        },
      ]}
    >
      {children}
    </View>
  );

  // Web doesn't support BlurView well, use fallback
  if (Platform.OS === 'web') {
    return (
      <Animated.View
        style={[
          styles.webCard,
          { borderRadius: radius, backgroundColor: colors.glass.background },
          glow && shadows.glow(resolvedGlowColor),
          animatedStyle,
          style,
        ]}
      >
        {cardContent}
      </Animated.View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        { borderRadius: radius },
        glow && shadows.glow(resolvedGlowColor),
        animatedStyle,
        style,
      ]}
    >
      <BlurView intensity={20} tint={isDark ? 'dark' : 'light'} style={StyleSheet.absoluteFill} />
      {cardContent}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
    ...shadows.md,
  },
  webCard: {
    ...shadows.md,
  },
  content: {
    borderWidth: 1,
  },
});
