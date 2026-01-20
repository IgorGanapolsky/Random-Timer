/**
 * TimerControls Component
 * Play, Pause, Reset buttons for timer control
 */

import { StyleSheet, View, Pressable } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withSpring,
  useSharedValue,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Path } from 'react-native-svg';

import { colors, spacing, radii, timing, shadows } from '@shared/theme';
import { useHaptics } from '@shared/hooks/useHaptics';

interface TimerControlsProps {
  /** Timer is currently running */
  isRunning: boolean;
  /** Play/Pause handler */
  onPlayPause: () => void;
  /** Reset handler */
  onReset: () => void;
  /** Stop and go back handler */
  onStop: () => void;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function TimerControls({
  isRunning,
  onPlayPause,
  onReset,
  onStop,
}: TimerControlsProps) {
  const { trigger } = useHaptics();

  return (
    <View style={styles.container}>
      {/* Reset button */}
      <ControlButton
        icon="reset"
        size={56}
        variant="ghost"
        onPress={() => {
          trigger('medium');
          onReset();
        }}
      />

      {/* Play/Pause button */}
      <ControlButton
        icon={isRunning ? 'pause' : 'play'}
        size={80}
        variant="primary"
        onPress={() => {
          trigger('medium');
          onPlayPause();
        }}
      />

      {/* Stop button */}
      <ControlButton
        icon="stop"
        size={56}
        variant="ghost"
        onPress={() => {
          trigger('medium');
          onStop();
        }}
      />
    </View>
  );
}

interface ControlButtonProps {
  icon: 'play' | 'pause' | 'reset' | 'stop';
  size: number;
  variant: 'primary' | 'ghost';
  onPress: () => void;
}

function ControlButton({ icon, size, variant, onPress }: ControlButtonProps) {
  const scale = useSharedValue(1);
  const rotation = useSharedValue(0);

  const handlePressIn = () => {
    scale.value = withSpring(0.9, timing.spring.snappy);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, timing.spring.snappy);
  };

  const handlePress = () => {
    if (icon === 'reset') {
      // Spin animation for reset
      rotation.value = withSequence(
        withTiming(0, { duration: 0 }),
        withSpring(-360, timing.spring.gentle)
      );
    }
    onPress();
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { rotate: `${rotation.value}deg` },
    ],
  }));

  const isPrimary = variant === 'primary';
  const iconSize = size * 0.4;

  return (
    <AnimatedPressable
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      style={[
        styles.button,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
        },
        isPrimary ? styles.primaryButton : styles.ghostButton,
        isPrimary && shadows.glow(colors.primary),
        animatedStyle,
      ]}
    >
      <IconSvg
        icon={icon}
        size={iconSize}
        color={isPrimary ? colors.palette.neutral100 : colors.text}
      />
    </AnimatedPressable>
  );
}

interface IconSvgProps {
  icon: 'play' | 'pause' | 'reset' | 'stop';
  size: number;
  color: string;
}

function IconSvg({ icon, size, color }: IconSvgProps) {
  const paths = {
    play: 'M8 5v14l11-7z',
    pause: 'M6 19h4V5H6v14zm8-14v14h4V5h-4z',
    reset: 'M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z',
    stop: 'M6 6h12v12H6z',
  };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
      <Path d={paths[icon]} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing['2xl'],
  },
  button: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: colors.primary,
  },
  ghostButton: {
    backgroundColor: colors.glass.background,
    borderWidth: 1,
    borderColor: colors.glass.border,
  },
});
