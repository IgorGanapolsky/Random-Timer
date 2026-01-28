/**
 * RangeSlider Component
 * Dual-thumb slider for selecting min/max time range
 */

import { useEffect } from 'react';
import { StyleSheet, View, LayoutChangeEvent } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import { spacing, radii, timing, useTheme } from '@shared/theme';
import { Text } from '@shared/components';
import { useHaptics } from '@shared/hooks/useHaptics';

interface RangeSliderProps {
  /** Minimum value */
  min: number;
  /** Maximum value */
  max: number;
  /** Current min value */
  minValue: number;
  /** Current max value */
  maxValue: number;
  /** Value change handler */
  onValueChange: (min: number, max: number) => void;
  /** Step size */
  step?: number;
  /** Format value for display */
  formatValue?: (value: number) => string;
  /** Label */
  label?: string;
  /** Minimum gap between min and max values (in value units, not pixels) */
  minGap?: number;
}

export function RangeSlider({
  min,
  max,
  minValue,
  maxValue,
  onValueChange,
  step = 1,
  formatValue = v => `${v}s`,
  label,
  minGap,
}: RangeSliderProps) {
  const { colors } = useTheme();
  const trackWidth = useSharedValue(0);
  const sliderX = useSharedValue(0);
  const { trigger } = useHaptics();

  const minPosition = useSharedValue(0);
  const maxPosition = useSharedValue(0);

  const THUMB_SIZE = 24;
  const THUMB_RADIUS = THUMB_SIZE / 2;
  // Use value-based gap if provided, otherwise fall back to step
  const effectiveMinGap = minGap ?? step;

  const valueToPosition = (value: number, width: number) => {
    'worklet';
    if (width <= THUMB_SIZE) return 0;
    return ((value - min) / (max - min)) * (width - THUMB_SIZE);
  };

  const positionToValue = (position: number, width: number) => {
    'worklet';
    if (width <= THUMB_SIZE) return min;
    const raw = min + (position / (width - THUMB_SIZE)) * (max - min);
    const clamped = Math.max(min, Math.min(max, raw));
    return Math.round(clamped / step) * step;
  };

  const handleLayout = (event: LayoutChangeEvent) => {
    const { width } = event.nativeEvent.layout;
    trackWidth.value = width;
    // Measure absolute X position on screen
    event.target.measureInWindow(pageX => {
      sliderX.value = pageX;
    });
    minPosition.value = valueToPosition(minValue, width);
    maxPosition.value = valueToPosition(maxValue, width);
  };

  // Sync positions when values change from parent (e.g., loaded from storage)
  useEffect(() => {
    if (trackWidth.value > 0) {
      minPosition.value = valueToPosition(minValue, trackWidth.value);
      maxPosition.value = valueToPosition(maxValue, trackWidth.value);
    }
    // Position functions are stable - intentionally excluded to prevent animation restarts
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minValue, maxValue]);

  const updateValues = (newMin: number, newMax: number) => {
    onValueChange(newMin, newMax);
  };

  const triggerHaptic = () => {
    trigger('selection');
  };

  // Calculate the gap in pixels based on the value gap
  const gapInPixels = (gap: number, width: number) => {
    'worklet';
    if (width <= THUMB_SIZE) return 0;
    return (gap / (max - min)) * (width - THUMB_SIZE);
  };

  // Min thumb gesture
  const minGesture = Gesture.Pan()
    .onUpdate(event => {
      // Calculate position relative to slider
      const relativeX = event.absoluteX - sliderX.value;
      // Calculate max allowed position: max thumb position minus gap
      const gapPx = gapInPixels(effectiveMinGap, trackWidth.value);
      const maxConstraint = maxPosition.value - gapPx;
      const newPos = Math.max(0, Math.min(maxConstraint, relativeX - THUMB_RADIUS));
      minPosition.value = newPos;
      const newMinValue = positionToValue(newPos, trackWidth.value);
      const currentMaxValue = positionToValue(maxPosition.value, trackWidth.value);
      runOnJS(updateValues)(newMinValue, currentMaxValue);
    })
    .onEnd(() => {
      runOnJS(triggerHaptic)();
      minPosition.value = withSpring(minPosition.value, timing.spring.snappy);
    });

  // Max thumb gesture
  const maxGesture = Gesture.Pan()
    .onUpdate(event => {
      // Calculate position relative to slider
      const relativeX = event.absoluteX - sliderX.value;
      // Calculate min allowed position: min thumb position plus gap
      const gapPx = gapInPixels(effectiveMinGap, trackWidth.value);
      const minConstraint = minPosition.value + gapPx;
      const newPos = Math.max(
        minConstraint,
        Math.min(trackWidth.value - THUMB_SIZE, relativeX - THUMB_RADIUS),
      );
      maxPosition.value = newPos;
      const currentMinValue = positionToValue(minPosition.value, trackWidth.value);
      const newMaxValue = positionToValue(newPos, trackWidth.value);
      runOnJS(updateValues)(currentMinValue, newMaxValue);
    })
    .onEnd(() => {
      runOnJS(triggerHaptic)();
      maxPosition.value = withSpring(maxPosition.value, timing.spring.snappy);
    });

  const minThumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: minPosition.value }],
  }));

  const maxThumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: maxPosition.value }],
  }));

  const activeTrackStyle = useAnimatedStyle(() => ({
    left: minPosition.value + THUMB_RADIUS,
    right: trackWidth.value - maxPosition.value - THUMB_RADIUS,
  }));

  return (
    <View style={styles.container}>
      {label && (
        <Text preset="caption" color={colors.textDim} style={styles.label}>
          {label}
        </Text>
      )}

      <View style={styles.valuesContainer}>
        <Text preset="h4" color={colors.primary}>
          {formatValue(minValue)}
        </Text>
        <Text preset="body" color={colors.textDim}>
          to
        </Text>
        <Text preset="h4" color={colors.primary}>
          {formatValue(maxValue)}
        </Text>
      </View>

      <View style={styles.sliderContainer} onLayout={handleLayout}>
        {/* Background track */}
        <View style={[styles.track, { backgroundColor: colors.glass.border }]} />

        {/* Active range track */}
        <Animated.View
          style={[styles.activeTrack, { backgroundColor: colors.primary }, activeTrackStyle]}
        />

        {/* Min thumb */}
        <GestureDetector gesture={minGesture}>
          <Animated.View
            style={[
              styles.thumb,
              { backgroundColor: colors.primary, shadowColor: colors.primary },
              minThumbStyle,
            ]}
          >
            <View style={[styles.thumbInner, { backgroundColor: colors.palette.neutral100 }]} />
          </Animated.View>
        </GestureDetector>

        {/* Max thumb */}
        <GestureDetector gesture={maxGesture}>
          <Animated.View
            style={[
              styles.thumb,
              { backgroundColor: colors.primary, shadowColor: colors.primary },
              maxThumbStyle,
            ]}
          >
            <View style={[styles.thumbInner, { backgroundColor: colors.palette.neutral100 }]} />
          </Animated.View>
        </GestureDetector>
      </View>

      <View style={styles.rangeLabels}>
        <Text preset="caption" color={colors.textMuted}>
          {formatValue(min)}
        </Text>
        <Text preset="caption" color={colors.textMuted}>
          {formatValue(max)}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  activeTrack: {
    borderRadius: radii.full,
    height: 6,
    position: 'absolute',
  },
  container: {
    width: '100%',
  },
  label: {
    marginBottom: spacing.sm,
  },
  rangeLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.xs,
  },
  sliderContainer: {
    height: 40,
    justifyContent: 'center',
  },
  thumb: {
    alignItems: 'center',
    borderRadius: 12,
    elevation: 5,
    height: 24,
    justifyContent: 'center',
    position: 'absolute',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
    width: 24,
  },
  thumbInner: {
    borderRadius: 5,
    height: 10,
    width: 10,
  },
  track: {
    borderRadius: radii.full,
    height: 6,
    left: 0,
    position: 'absolute',
    right: 0,
  },
  valuesContainer: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.md,
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
});
