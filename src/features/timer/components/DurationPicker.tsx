/**
 * DurationPicker Component
 * Simple picker for selecting alarm duration
 */

import { StyleSheet, View, Pressable } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withSpring,
  useSharedValue,
} from 'react-native-reanimated';

import { colors, spacing, radii, timing } from '@shared/theme';
import { Text } from '@shared/components';
import { useHaptics } from '@shared/hooks/useHaptics';

interface DurationPickerProps {
  /** Selected duration in seconds */
  value: number;
  /** Value change handler */
  onValueChange: (value: number) => void;
  /** Available options in seconds */
  options?: number[];
  /** Label */
  label?: string;
}

const DEFAULT_OPTIONS = [5, 10, 15, 30, 60];

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function DurationPicker({
  value,
  onValueChange,
  options = DEFAULT_OPTIONS,
  label,
}: DurationPickerProps) {
  const { trigger } = useHaptics();

  const formatDuration = (seconds: number) => {
    if (seconds >= 60) {
      return `${seconds / 60}m`;
    }
    return `${seconds}s`;
  };

  return (
    <View style={styles.container}>
      {label && (
        <Text preset="caption" color={colors.textDim} style={styles.label}>
          {label}
        </Text>
      )}

      <View style={styles.optionsContainer}>
        {options.map((option) => (
          <OptionButton
            key={option}
            value={option}
            label={formatDuration(option)}
            isSelected={value === option}
            onPress={() => {
              trigger('selection');
              onValueChange(option);
            }}
          />
        ))}
      </View>
    </View>
  );
}

interface OptionButtonProps {
  value: number;
  label: string;
  isSelected: boolean;
  onPress: () => void;
}

function OptionButton({ label, isSelected, onPress }: OptionButtonProps) {
  const scale = useSharedValue(1);

  const handlePressIn = () => {
    scale.value = withSpring(0.9, timing.spring.snappy);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, timing.spring.snappy);
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <AnimatedPressable
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      style={[
        styles.optionButton,
        isSelected && styles.optionButtonSelected,
        animatedStyle,
      ]}
    >
      <Text
        preset="button"
        color={isSelected ? colors.palette.neutral100 : colors.textDim}
      >
        {label}
      </Text>
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  label: {
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  optionsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  optionButton: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.glass.background,
    borderWidth: 1,
    borderColor: colors.glass.border,
  },
  optionButtonSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
});
