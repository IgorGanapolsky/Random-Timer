/**
 * ActiveTimerScreen
 * Display running timer with controls
 */

import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  useReducedMotion,
} from 'react-native-reanimated';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { GlassCard, Screen, Text } from '@shared/components';
import { colors, spacing } from '@shared/theme';
import {
  analyticsService,
  AnalyticsEvents,
  AnalyticsScreens,
  reviewService,
} from '@shared/services';
import { RootStackParamList, TimerDebugParams } from '@navigation';
import { CircularTimer, TimerControls } from '../components';
import { useRandomTimer } from '../hooks/useRandomTimer';
import { soundService } from '../services/soundService';

interface ActiveTimerScreenProps {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Timer'>;
  route: RouteProp<RootStackParamList, 'Timer'>;
}

export function ActiveTimerScreen({ navigation, route }: ActiveTimerScreenProps) {
  const { config, debug } = route.params;
  const { state, start, pause, resume, reset, stop } = useRandomTimer(config);

  // Apply debug overrides for testing (development only)
  const effectiveState = __DEV__ && debug ? applyDebugOverrides(state, debug) : state;

  // Pulsing animation for alarm state
  const pulseScale = useSharedValue(1);
  const pulseOpacity = useSharedValue(1);
  const reduceMotion = useReducedMotion();

  // Initialize sound and start timer
  useEffect(() => {
    analyticsService.screen(AnalyticsScreens.ACTIVE_TIMER);
    soundService.initialize();
    start();
    analyticsService.track(AnalyticsEvents.TIMER_STARTED, {
      minSeconds: config.minSeconds,
      maxSeconds: config.maxSeconds,
      randomMode: config.randomMode,
    });

    return () => {
      soundService.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle alarm state
  useEffect(() => {
    if (effectiveState.isComplete) {
      // Play alarm sound
      soundService.play(config.alarmDuration * 1000);

      // Track completion and maybe request review
      analyticsService.track(AnalyticsEvents.TIMER_COMPLETED, {
        totalTime: effectiveState.totalTime,
      });
      reviewService.recordSuccess();
      reviewService.maybeRequestReview();

      // Start pulse animation (skip if reduce motion enabled)
      if (!reduceMotion) {
        pulseScale.value = withRepeat(
          withSequence(withTiming(1.05, { duration: 500 }), withTiming(1, { duration: 500 })),
          -1,
          true,
        );
        pulseOpacity.value = withRepeat(
          withSequence(withTiming(0.7, { duration: 500 }), withTiming(1, { duration: 500 })),
          -1,
          true,
        );
      }
    } else {
      // Stop animation
      pulseScale.value = withTiming(1);
      pulseOpacity.value = withTiming(1);
    }
    // effectiveState.totalTime is intentionally excluded - we only want to track once on completion
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveState.isComplete, config.alarmDuration, pulseScale, pulseOpacity, reduceMotion]);

  const handlePlayPause = () => {
    if (effectiveState.isComplete) {
      // Dismiss alarm and reset
      soundService.stop();
      reset();
    } else if (effectiveState.isRunning) {
      pause();
      analyticsService.track(AnalyticsEvents.TIMER_PAUSED);
    } else {
      resume();
      analyticsService.track(AnalyticsEvents.TIMER_RESUMED);
    }
  };

  const handleReset = () => {
    soundService.stop();
    reset();
    analyticsService.track(AnalyticsEvents.TIMER_RESET);
  };

  const handleStop = () => {
    soundService.stop();
    stop();
    analyticsService.track(AnalyticsEvents.TIMER_STOPPED);
    navigation.goBack();
  };

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseScale.value }],
    opacity: pulseOpacity.value,
  }));

  return (
    <Screen preset="fill">
      <View style={styles.mainContent}>
        <Animated.View style={[styles.timerContainer, effectiveState.isComplete && pulseStyle]}>
          {effectiveState.isComplete ? (
            <GlassCard glow glowColor={colors.timerDanger} padding={spacing['3xl']}>
              <View style={styles.alarmContent}>
                <Text
                  preset="h1"
                  center
                  color={colors.timerDanger}
                  accessibilityIgnoresInvertColors
                >
                  ⏰
                </Text>
                <Text preset="h2" center style={styles.alarmTitle}>
                  Time&apos;s Up!
                </Text>
                <Text preset="body" center color={colors.textDim}>
                  Alarm stops in {effectiveState.alarmTimeRemaining}s
                </Text>
              </View>
            </GlassCard>
          ) : (
            <CircularTimer
              timeRemaining={effectiveState.timeRemaining}
              totalTime={effectiveState.totalTime}
              hideTime={config.randomMode}
              isPaused={!effectiveState.isRunning}
            />
          )}
        </Animated.View>

        {!config.randomMode && effectiveState.totalTime > 0 && !effectiveState.isComplete && (
          <Text preset="caption" center color={colors.textMuted} style={styles.totalTime}>
            TOTAL: {formatTime(effectiveState.totalTime).toUpperCase()}
          </Text>
        )}

        <View style={styles.controls}>
          <TimerControls
            isRunning={effectiveState.isRunning}
            onPlayPause={handlePlayPause}
            onReset={handleReset}
            onStop={handleStop}
          />
        </View>
      </View>

      {config.randomMode && !effectiveState.isComplete && (
        <GlassCard style={styles.randomBadge} padding={spacing.md}>
          <Text preset="caption" center color={colors.palette.secondary400}>
            🎲 RANDOM MODE
          </Text>
        </GlassCard>
      )}
    </Screen>
  );
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * Apply debug overrides for testing timer states
 * Only active in __DEV__ mode
 */
function applyDebugOverrides(
  state: ReturnType<typeof useRandomTimer>['state'],
  debug: TimerDebugParams,
): typeof state {
  const overrides: Partial<typeof state> = {};

  if (debug.debugTimeRemaining !== undefined) {
    overrides.timeRemaining = debug.debugTimeRemaining;
  }

  if (debug.debugSkipToAlarm) {
    overrides.isComplete = true;
    overrides.timeRemaining = 0;
  }

  if (debug.debugState) {
    switch (debug.debugState) {
      case 'warning':
        // Warning state: ~30% remaining
        overrides.timeRemaining = Math.floor(state.totalTime * 0.3);
        break;
      case 'danger':
        // Danger state: ~10% remaining
        overrides.timeRemaining = Math.floor(state.totalTime * 0.1);
        break;
      case 'complete':
        overrides.isComplete = true;
        overrides.timeRemaining = 0;
        break;
    }
  }

  return { ...state, ...overrides };
}

const styles = StyleSheet.create({
  alarmContent: {
    alignItems: 'center',
    gap: spacing.md,
  },
  alarmTitle: {
    marginTop: spacing.sm,
  },
  controls: {
    marginTop: spacing.xl,
  },
  mainContent: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    paddingTop: spacing['2xl'],
  },
  randomBadge: {
    alignSelf: 'center',
    position: 'absolute',
    top: spacing['5xl'],
  },
  timerContainer: {
    marginBottom: spacing.lg,
  },
  totalTime: {
    letterSpacing: 2,
    marginBottom: spacing.xl,
  },
});
