/**
 * CircularTimer Component
 * Beautiful circular countdown with animated progress arc
 */

import { StyleSheet, View } from 'react-native';
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';
import Animated, { useAnimatedProps, useDerivedValue, withTiming } from 'react-native-reanimated';
import { colors } from '@shared/theme';
import { Text } from '@shared/components';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface CircularTimerProps {
  /** Current time remaining in seconds */
  timeRemaining: number;
  /** Total time in seconds */
  totalTime: number;
  /** Size of the timer */
  size?: number;
  /** Stroke width */
  strokeWidth?: number;
  /** Hide time display (mystery mode) */
  hideTime?: boolean;
  /** Timer is paused */
  isPaused?: boolean;
}

export function CircularTimer({
  timeRemaining,
  totalTime,
  size = 280,
  strokeWidth = 12,
  hideTime = false,
  isPaused = false,
}: CircularTimerProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const center = size / 2;

  // Progress percentage (1 = full, 0 = empty)
  const progress = useDerivedValue(() => {
    return totalTime > 0 ? timeRemaining / totalTime : 0;
  }, [timeRemaining, totalTime]);

  // Animated stroke dash offset
  const animatedProps = useAnimatedProps(() => {
    const strokeDashoffset = circumference * (1 - progress.value);
    return {
      strokeDashoffset: withTiming(strokeDashoffset, { duration: 100 }),
    };
  });

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size} style={styles.svg}>
        <Defs>
          <LinearGradient id="timerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor={colors.timerActive} />
            <Stop offset="50%" stopColor={colors.timerWarning} />
            <Stop offset="100%" stopColor={colors.timerDanger} />
          </LinearGradient>
        </Defs>

        {/* Background track */}
        <Circle
          cx={center}
          cy={center}
          r={radius}
          stroke={colors.glass.border}
          strokeWidth={strokeWidth}
          fill="transparent"
        />

        {/* Progress arc - hidden in mystery mode */}
        {!hideTime && (
          <AnimatedCircle
            cx={center}
            cy={center}
            r={radius}
            stroke="url(#timerGradient)"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeLinecap="round"
            strokeDasharray={circumference}
            animatedProps={animatedProps}
            rotation={-90}
            origin={`${center}, ${center}`}
          />
        )}
      </Svg>

      {/* Time display */}
      <View style={styles.timeContainer}>
        {hideTime ? (
          <Text preset="timerLarge" center color={colors.text}>
            ???
          </Text>
        ) : (
          <>
            <Text
              preset="timerLarge"
              center
              color={colors.text}
              style={isPaused ? styles.pausedText : undefined}
            >
              {formatTime(timeRemaining)}
            </Text>
            {isPaused && (
              <Text preset="caption" center color={colors.textDim}>
                PAUSED
              </Text>
            )}
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  pausedText: {
    opacity: 0.6,
  },
  svg: {
    position: 'absolute',
  },
  timeContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
