/**
 * Button Component
 * Animated button with haptic feedback and multiple variants
 */

import { StyleSheet, Pressable, ViewStyle, ActivityIndicator } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';
import { colors, spacing, radii, timing } from '../theme';
import { Text } from './Text';
import { useHaptics } from '../hooks/useHaptics';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  /** Button label */
  label: string;
  /** Press handler */
  onPress: () => void;
  /** Button variant */
  variant?: ButtonVariant;
  /** Button size */
  size?: ButtonSize;
  /** Disabled state */
  disabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Custom style */
  style?: ViewStyle;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
}: ButtonProps) {
  const scale = useSharedValue(1);
  const { trigger } = useHaptics();

  const handlePressIn = () => {
    scale.value = withSpring(0.95, timing.spring.snappy);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, timing.spring.snappy);
  };

  const handlePress = () => {
    if (disabled || loading) return;
    trigger('light');
    onPress();
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const variantStyles = getVariantStyles(variant);
  const sizeStyles = getSizeStyles(size);

  return (
    <AnimatedPressable
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled || loading}
      style={[
        styles.base,
        variantStyles.container,
        sizeStyles.container,
        fullWidth && styles.fullWidth,
        disabled && styles.disabled,
        animatedStyle,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator size="small" color={variantStyles.textColor} />
      ) : (
        <Text preset={size === 'lg' ? 'buttonLarge' : 'button'} color={variantStyles.textColor}>
          {label}
        </Text>
      )}
    </AnimatedPressable>
  );
}

function getVariantStyles(variant: ButtonVariant) {
  switch (variant) {
    case 'primary':
      return {
        container: styles.primaryContainer,
        textColor: colors.palette.neutral100,
      };
    case 'secondary':
      return {
        container: styles.secondaryContainer,
        textColor: colors.primary,
      };
    case 'ghost':
      return {
        container: styles.ghostContainer,
        textColor: colors.text,
      };
    case 'danger':
      return {
        container: styles.dangerContainer,
        textColor: colors.palette.neutral100,
      };
  }
}

function getSizeStyles(size: ButtonSize) {
  switch (size) {
    case 'sm':
      return {
        container: {
          paddingVertical: spacing.sm,
          paddingHorizontal: spacing.lg,
        },
      };
    case 'md':
      return {
        container: {
          paddingVertical: spacing.md,
          paddingHorizontal: spacing.xl,
        },
      };
    case 'lg':
      return {
        container: {
          paddingVertical: spacing.lg,
          paddingHorizontal: spacing['2xl'],
        },
      };
  }
}

const styles = StyleSheet.create({
  base: {
    alignItems: 'center',
    borderRadius: radii.lg,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  dangerContainer: {
    backgroundColor: colors.timerDanger,
  },
  disabled: {
    opacity: 0.5,
  },
  fullWidth: {
    width: '100%',
  },
  ghostContainer: {
    backgroundColor: colors.transparent,
  },
  primaryContainer: {
    backgroundColor: colors.primary,
  },
  secondaryContainer: {
    backgroundColor: colors.glass.backgroundLight,
    borderColor: colors.primary,
    borderWidth: 1,
  },
});
