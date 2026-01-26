/**
 * VolumeSlider Component
 * Single-thumb slider for controlling alarm volume
 */

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

interface VolumeSliderProps {
  /** Current volume (0-1) */
  value: number;
  /** Value change handler */
  onValueChange: (value: number) => void;
  /** Called when user finishes dragging (for preview sound) */
  onSlidingComplete?: () => void;
}

export function VolumeSlider({ value, onValueChange, onSlidingComplete }: VolumeSliderProps) {
  const { colors } = useTheme();
  const trackWidth = useSharedValue(0);
  const sliderX = useSharedValue(0);
  const { trigger } = useHaptics();

  const thumbPosition = useSharedValue(0);

  const THUMB_SIZE = 24;
  const THUMB_RADIUS = THUMB_SIZE / 2;

  const valueToPosition = (val: number, width: number) => {
    'worklet';
    if (width <= THUMB_SIZE) return 0;
    return val * (width - THUMB_SIZE);
  };

  const positionToValue = (position: number, width: number) => {
    'worklet';
    if (width <= THUMB_SIZE) return 0;
    const raw = position / (width - THUMB_SIZE);
    return Math.max(0, Math.min(1, raw));
  };

  const handleLayout = (event: LayoutChangeEvent) => {
    const { width } = event.nativeEvent.layout;
    trackWidth.value = width;
    event.target.measureInWindow(pageX => {
      sliderX.value = pageX;
    });
    thumbPosition.value = valueToPosition(value, width);
  };

  const updateValue = (newValue: number) => {
    onValueChange(newValue);
  };

  const triggerHaptic = () => {
    trigger('selection');
  };

  const handleSlidingComplete = () => {
    onSlidingComplete?.();
  };

  const thumbGesture = Gesture.Pan()
    .onUpdate(event => {
      const relativeX = event.absoluteX - sliderX.value;
      const newPos = Math.max(0, Math.min(trackWidth.value - THUMB_SIZE, relativeX - THUMB_RADIUS));
      thumbPosition.value = newPos;
      const newValue = positionToValue(newPos, trackWidth.value);
      runOnJS(updateValue)(newValue);
    })
    .onEnd(() => {
      runOnJS(triggerHaptic)();
      runOnJS(handleSlidingComplete)();
      thumbPosition.value = withSpring(thumbPosition.value, timing.spring.snappy);
    });

  const thumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: thumbPosition.value }],
  }));

  const activeTrackStyle = useAnimatedStyle(() => ({
    width: thumbPosition.value + THUMB_RADIUS,
  }));

  const getVolumeLabel = () => {
    if (value === 0) return 'Muted';
    if (value < 0.33) return 'Low';
    if (value < 0.66) return 'Medium';
    if (value < 1) return 'High';
    return 'Max';
  };

  const getVolumeIcon = () => {
    if (value === 0) return '🔇';
    if (value < 0.5) return '🔉';
    return '🔊';
  };

  return (
    <View style={styles.container}>
      <View style={styles.labelRow}>
        <Text preset="bodySmall" color={colors.textDim}>
          {getVolumeIcon()} {getVolumeLabel()}
        </Text>
        <Text preset="bodySmall" color={colors.primary}>
          {Math.round(value * 100)}%
        </Text>
      </View>

      <View style={styles.sliderContainer} onLayout={handleLayout}>
        {/* Background track */}
        <View style={[styles.track, { backgroundColor: colors.glass.border }]} />

        {/* Active track */}
        <Animated.View
          style={[styles.activeTrack, { backgroundColor: colors.primary }, activeTrackStyle]}
        />

        {/* Thumb */}
        <GestureDetector gesture={thumbGesture}>
          <Animated.View
            style={[
              styles.thumb,
              { backgroundColor: colors.primary, shadowColor: colors.primary },
              thumbStyle,
            ]}
          >
            <View style={[styles.thumbInner, { backgroundColor: colors.palette.neutral100 }]} />
          </Animated.View>
        </GestureDetector>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  activeTrack: {
    borderRadius: radii.full,
    height: 4,
    left: 0,
    position: 'absolute',
  },
  container: {
    width: '100%',
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  sliderContainer: {
    height: 32,
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
    shadowRadius: 6,
    width: 24,
  },
  thumbInner: {
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  track: {
    borderRadius: radii.full,
    height: 4,
    left: 0,
    position: 'absolute',
    right: 0,
  },
});
