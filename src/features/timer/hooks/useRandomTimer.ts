/**
 * useRandomTimer Hook
 * Core timer logic with random time selection
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useHaptics } from '@shared/hooks/useHaptics';

export interface TimerConfig {
  /** Minimum time in seconds */
  minSeconds: number;
  /** Maximum time in seconds */
  maxSeconds: number;
  /** How long the alarm should sound (seconds) */
  alarmDuration: number;
  /** Hide remaining time (random mode - aligns with app brand) */
  randomMode: boolean;
}

export interface TimerState {
  /** Timer is currently running */
  isRunning: boolean;
  /** Time remaining in seconds */
  timeRemaining: number;
  /** Total time that was selected */
  totalTime: number;
  /** Timer has completed (alarm is playing) */
  isComplete: boolean;
  /** Alarm time remaining */
  alarmTimeRemaining: number;
}

interface UseRandomTimerReturn {
  state: TimerState;
  start: () => void;
  pause: () => void;
  resume: () => void;
  reset: () => void;
  stop: () => void;
}

export function useRandomTimer(config: TimerConfig): UseRandomTimerReturn {
  const { trigger } = useHaptics();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const alarmIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [state, setState] = useState<TimerState>({
    isRunning: false,
    timeRemaining: 0,
    totalTime: 0,
    isComplete: false,
    alarmTimeRemaining: 0,
  });

  // Generate random time within range
  const getRandomTime = useCallback(() => {
    const range = config.maxSeconds - config.minSeconds;
    return config.minSeconds + Math.floor(Math.random() * (range + 1));
  }, [config.minSeconds, config.maxSeconds]);

  // Start the timer
  const start = useCallback(() => {
    const randomTime = getRandomTime();

    setState({
      isRunning: true,
      timeRemaining: randomTime,
      totalTime: randomTime,
      isComplete: false,
      alarmTimeRemaining: 0,
    });

    trigger('success');
  }, [getRandomTime, trigger]);

  // Pause the timer
  const pause = useCallback(() => {
    setState(prev => ({ ...prev, isRunning: false }));
    trigger('light');
  }, [trigger]);

  // Resume the timer
  const resume = useCallback(() => {
    if (state.timeRemaining > 0) {
      setState(prev => ({ ...prev, isRunning: true }));
      trigger('light');
    }
  }, [state.timeRemaining, trigger]);

  // Reset the timer (generate new random time)
  const reset = useCallback(() => {
    // Clear any running intervals
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (alarmIntervalRef.current) {
      clearInterval(alarmIntervalRef.current);
      alarmIntervalRef.current = null;
    }

    const randomTime = getRandomTime();

    setState({
      isRunning: true,
      timeRemaining: randomTime,
      totalTime: randomTime,
      isComplete: false,
      alarmTimeRemaining: 0,
    });

    trigger('medium');
  }, [getRandomTime, trigger]);

  // Stop and go back
  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (alarmIntervalRef.current) {
      clearInterval(alarmIntervalRef.current);
      alarmIntervalRef.current = null;
    }

    setState({
      isRunning: false,
      timeRemaining: 0,
      totalTime: 0,
      isComplete: false,
      alarmTimeRemaining: 0,
    });

    trigger('light');
  }, [trigger]);

  // Timer countdown effect
  useEffect(() => {
    if (state.isRunning && state.timeRemaining > 0) {
      intervalRef.current = setInterval(() => {
        setState(prev => {
          const newTime = prev.timeRemaining - 1;

          // Timer complete!
          if (newTime <= 0) {
            trigger('error'); // Strong haptic for alarm
            return {
              ...prev,
              isRunning: false,
              timeRemaining: 0,
              isComplete: true,
              alarmTimeRemaining: config.alarmDuration,
            };
          }

          // Warning haptic at 10 seconds
          if (newTime === 10) {
            trigger('warning');
          }

          return { ...prev, timeRemaining: newTime };
        });
      }, 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [state.isRunning, state.timeRemaining, config.alarmDuration, trigger]);

  // Alarm countdown effect
  useEffect(() => {
    if (state.isComplete && state.alarmTimeRemaining > 0) {
      alarmIntervalRef.current = setInterval(() => {
        setState(prev => {
          const newAlarmTime = prev.alarmTimeRemaining - 1;

          if (newAlarmTime <= 0) {
            return {
              ...prev,
              isComplete: false,
              alarmTimeRemaining: 0,
            };
          }

          return { ...prev, alarmTimeRemaining: newAlarmTime };
        });
      }, 1000);
    }

    return () => {
      if (alarmIntervalRef.current) {
        clearInterval(alarmIntervalRef.current);
        alarmIntervalRef.current = null;
      }
    };
  }, [state.isComplete, state.alarmTimeRemaining]);

  return {
    state,
    start,
    pause,
    resume,
    reset,
    stop,
  };
}
