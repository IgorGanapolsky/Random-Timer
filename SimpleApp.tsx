import React, {useEffect, useMemo, useRef, useState} from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
  Vibration,
  useColorScheme,
} from 'react-native';

type Mode = 'timer' | 'alarm';
type Status = 'idle' | 'scheduled' | 'running' | 'alarming';

type Colors = {
  background: string;
  card: string;
  surface: string;
  border: string;
  textPrimary: string;
  textSecondary: string;
  accent: string;
  accentText: string;
  chipBackground: string;
  chipText: string;
  error: string;
};

const ALARM_PATTERN = [0, 500, 400, 500, 400, 500];

const lightColors: Colors = {
  background: '#F6F7FB',
  card: '#FFFFFF',
  surface: '#F1F3F6',
  border: '#E0E4EA',
  textPrimary: '#0B0D0F',
  textSecondary: '#5B6470',
  accent: '#4F46E5',
  accentText: '#FFFFFF',
  chipBackground: '#E8ECF3',
  chipText: '#3B4451',
  error: '#D14343',
};

const darkColors: Colors = {
  background: '#0C0F14',
  card: '#141922',
  surface: '#1B2230',
  border: '#263145',
  textPrimary: '#F3F5F9',
  textSecondary: '#A7B0BC',
  accent: '#9B8CFF',
  accentText: '#0B0D0F',
  chipBackground: '#1F2635',
  chipText: '#C6CFDB',
  error: '#FF7A7A',
};

const sanitizeMinutesInput = (value: string) => {
  const cleaned = value.replace(/[^0-9.]/g, '');
  const parts = cleaned.split('.');
  if (parts.length <= 1) {
    return cleaned;
  }
  return `${parts[0]}.${parts.slice(1).join('')}`;
};

const parseMinutes = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const numberValue = Number(trimmed);
  if (!Number.isFinite(numberValue) || numberValue < 0) {
    return null;
  }
  return numberValue;
};

const formatMinutesValue = (value: number) => {
  const rounded = Math.round(value * 10) / 10;
  const text = String(rounded);
  return text.endsWith('.0') ? text.slice(0, -2) : text;
};

const formatDuration = (ms: number) => {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const paddedSeconds = String(seconds).padStart(2, '0');
  if (hours > 0) {
    const paddedMinutes = String(minutes).padStart(2, '0');
    return `${hours}:${paddedMinutes}:${paddedSeconds}`;
  }
  return `${minutes}:${paddedSeconds}`;
};

const SimpleApp = () => {
  const colorScheme = useColorScheme();
  const colors = colorScheme === 'dark' ? darkColors : lightColors;
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [mode, setMode] = useState<Mode>('timer');
  const [activeMode, setActiveMode] = useState<Mode | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [minMinutes, setMinMinutes] = useState('1');
  const [maxMinutes, setMaxMinutes] = useState('5');
  const [nextTriggerAt, setNextTriggerAt] = useState<number | null>(null);
  const [triggeredAt, setTriggeredAt] = useState<number | null>(null);
  const [selectedDelayMs, setSelectedDelayMs] = useState<number | null>(
    null,
  );
  const [now, setNow] = useState(Date.now());

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const minValue = parseMinutes(minMinutes);
  const maxValue = parseMinutes(maxMinutes);
  const rangeValid =
    minValue !== null && maxValue !== null && minValue <= maxValue;
  const modeDisabled = status !== 'idle';

  const countdownMs = nextTriggerAt ? Math.max(0, nextTriggerAt - now) : 0;
  const elapsedMs = triggeredAt ? Math.max(0, now - triggeredAt) : 0;
  const selectedDelayText =
    selectedDelayMs !== null ? formatDuration(selectedDelayMs) : null;

  const clearTimer = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const handleStart = () => {
    if (!rangeValid || status !== 'idle' || minValue === null || maxValue === null) {
      return;
    }
    const randomMinutes =
      minValue === maxValue
        ? minValue
        : minValue + Math.random() * (maxValue - minValue);
    const delayMs = Math.max(0, Math.round(randomMinutes * 60 * 1000));
    const startTime = Date.now();
    setActiveMode(mode);
    setSelectedDelayMs(delayMs);
    setNextTriggerAt(startTime + delayMs);
    setTriggeredAt(null);
    setStatus('scheduled');
    setNow(startTime);
  };

  const handleStop = () => {
    clearTimer();
    Vibration.cancel();
    setStatus('idle');
    setActiveMode(null);
    setNextTriggerAt(null);
    setTriggeredAt(null);
    setSelectedDelayMs(null);
    setNow(Date.now());
  };

  const handleSnooze = () => {
    if (status !== 'alarming') {
      return;
    }
    const snoozeDelayMs = 5 * 60 * 1000;
    const startTime = Date.now();
    Vibration.cancel();
    setActiveMode('alarm');
    setSelectedDelayMs(snoozeDelayMs);
    setNextTriggerAt(startTime + snoozeDelayMs);
    setTriggeredAt(null);
    setStatus('scheduled');
    setNow(startTime);
  };

  const handleMinuteAdjust = (
    setter: React.Dispatch<React.SetStateAction<string>>,
    currentValue: string,
    delta: number,
  ) => {
    const parsed = parseMinutes(currentValue);
    const nextValue =
      parsed === null ? Math.max(0, delta) : Math.max(0, parsed + delta);
    setter(formatMinutesValue(nextValue));
  };

  useEffect(() => {
    if (status === 'idle') {
      return;
    }
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [status]);

  useEffect(() => {
    if (status !== 'scheduled' || !nextTriggerAt || !activeMode) {
      return;
    }
    const delayMs = Math.max(0, nextTriggerAt - Date.now());
    clearTimer();
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      setTriggeredAt(Date.now());
      if (activeMode === 'alarm') {
        setStatus('alarming');
        Vibration.vibrate(ALARM_PATTERN, true);
      } else {
        setStatus('running');
      }
    }, delayMs);
    return () => clearTimer();
  }, [status, nextTriggerAt, activeMode]);

  useEffect(() => {
    return () => {
      clearTimer();
      Vibration.cancel();
    };
  }, []);

  const statusLabel =
    status === 'idle'
      ? 'Idle'
      : status === 'scheduled'
        ? 'Scheduled'
        : status === 'running'
          ? 'Running'
          : 'Alarm';

  const statusTitle =
    status === 'idle'
      ? 'Ready'
      : status === 'scheduled'
        ? 'Next trigger in'
        : status === 'running'
          ? 'Timer running'
          : 'Alarm active';

  const statusValue =
    status === 'scheduled'
      ? formatDuration(countdownMs)
      : status === 'running'
        ? formatDuration(elapsedMs)
        : status === 'alarming'
          ? 'Beeping now'
          : 'Set your range';

  const statusDetail =
    status === 'idle'
      ? 'Choose a random range and press Start.'
      : status === 'scheduled'
        ? `Random delay selected: ${selectedDelayText ?? '—'}.`
        : status === 'running'
          ? `Started after ${selectedDelayText ?? '—'} delay.`
          : 'Stop or snooze to pause the alarm.';

  const rangeSummary =
    rangeValid && minValue !== null && maxValue !== null
      ? `${formatMinutesValue(minValue)}–${formatMinutesValue(maxValue)} min`
      : 'Enter a valid range (min ≤ max).';

  const canStart = rangeValid && status === 'idle';
  const primaryActionLabel =
    status === 'idle' ? 'Start random timer' : 'Stop';

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar
        barStyle={colorScheme === 'dark' ? 'light-content' : 'dark-content'}
      />
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Random Timer</Text>
          <Text style={styles.subtitle}>
            A single-screen randomizer that launches a timer or haptic alarm
            when you least expect it.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionLabel}>Mode</Text>
          <View style={styles.segmentedControl}>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{selected: mode === 'timer', disabled: modeDisabled}}
              onPress={() => {
                if (!modeDisabled) {
                  setMode('timer');
                }
              }}
              style={[
                styles.segment,
                mode === 'timer' && styles.segmentActive,
                modeDisabled && styles.segmentDisabled,
              ]}
            >
              <Text
                style={[
                  styles.segmentText,
                  mode === 'timer'
                    ? styles.segmentTextActive
                    : styles.segmentTextInactive,
                ]}
              >
                Timer
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{selected: mode === 'alarm', disabled: modeDisabled}}
              onPress={() => {
                if (!modeDisabled) {
                  setMode('alarm');
                }
              }}
              style={[
                styles.segment,
                mode === 'alarm' && styles.segmentActive,
                modeDisabled && styles.segmentDisabled,
              ]}
            >
              <Text
                style={[
                  styles.segmentText,
                  mode === 'alarm'
                    ? styles.segmentTextActive
                    : styles.segmentTextInactive,
                ]}
              >
                Alarm
              </Text>
            </Pressable>
          </View>
          <Text style={styles.helperText}>
            Timer counts up after the random delay. Alarm vibrates until you
            stop or snooze it.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionLabel}>Random interval</Text>
          <View style={styles.rangeRow}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Min (minutes)</Text>
              <View style={styles.inputRow}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Decrease minimum minutes"
                  onPress={() =>
                    handleMinuteAdjust(setMinMinutes, minMinutes, -1)
                  }
                  style={styles.stepButton}
                >
                  <Text style={styles.stepButtonText}>−</Text>
                </Pressable>
                <TextInput
                  value={minMinutes}
                  onChangeText={(text) =>
                    setMinMinutes(sanitizeMinutesInput(text))
                  }
                  keyboardType="numeric"
                  placeholder="1"
                  placeholderTextColor={colors.textSecondary}
                  style={styles.textInput}
                />
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Increase minimum minutes"
                  onPress={() =>
                    handleMinuteAdjust(setMinMinutes, minMinutes, 1)
                  }
                  style={styles.stepButton}
                >
                  <Text style={styles.stepButtonText}>+</Text>
                </Pressable>
              </View>
            </View>
            <View style={styles.rangeSpacer} />
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Max (minutes)</Text>
              <View style={styles.inputRow}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Decrease maximum minutes"
                  onPress={() =>
                    handleMinuteAdjust(setMaxMinutes, maxMinutes, -1)
                  }
                  style={styles.stepButton}
                >
                  <Text style={styles.stepButtonText}>−</Text>
                </Pressable>
                <TextInput
                  value={maxMinutes}
                  onChangeText={(text) =>
                    setMaxMinutes(sanitizeMinutesInput(text))
                  }
                  keyboardType="numeric"
                  placeholder="5"
                  placeholderTextColor={colors.textSecondary}
                  style={styles.textInput}
                />
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Increase maximum minutes"
                  onPress={() =>
                    handleMinuteAdjust(setMaxMinutes, maxMinutes, 1)
                  }
                  style={styles.stepButton}
                >
                  <Text style={styles.stepButtonText}>+</Text>
                </Pressable>
              </View>
            </View>
          </View>
          <Text
            style={[
              styles.helperText,
              !rangeValid && styles.errorText,
            ]}
          >
            {rangeSummary}
          </Text>
        </View>

        <View style={styles.card}>
          <View style={styles.statusHeader}>
            <Text style={styles.sectionLabel}>{statusTitle}</Text>
            <View style={styles.statusChip}>
              <Text style={styles.statusChipText}>{statusLabel}</Text>
            </View>
          </View>
          <Text
            style={
              status === 'scheduled' || status === 'running'
                ? styles.statusValue
                : styles.statusValueSmall
            }
          >
            {statusValue}
          </Text>
          <Text style={styles.statusDetail}>
            Mode: {(activeMode ?? mode) === 'timer' ? 'Timer' : 'Alarm'} ·{' '}
            {status === 'idle' ? 'Range ready' : 'Range'}: {rangeSummary}
          </Text>
          <Text style={styles.statusDetail}>{statusDetail}</Text>
        </View>

        <View style={styles.buttonRow}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={primaryActionLabel}
            disabled={!canStart && status === 'idle'}
            onPress={status === 'idle' ? handleStart : handleStop}
            style={({pressed}) => [
              styles.primaryButton,
              (!canStart && status === 'idle') && styles.primaryButtonDisabled,
              pressed && styles.primaryButtonPressed,
            ]}
          >
            <Text style={styles.primaryButtonText}>{primaryActionLabel}</Text>
          </Pressable>
          {status === 'alarming' && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Snooze alarm for five minutes"
              onPress={handleSnooze}
              style={({pressed}) => [
                styles.secondaryButton,
                pressed && styles.secondaryButtonPressed,
              ]}
            >
              <Text style={styles.secondaryButtonText}>Snooze 5 minutes</Text>
            </Pressable>
          )}
        </View>

        <Text style={styles.footnote}>
          Alarm mode uses haptics and visual cues. Keep haptics enabled for the
          best experience.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};

const makeStyles = (colors: Colors) =>
  StyleSheet.create({
    safeArea: {
      flex: 1,
      backgroundColor: colors.background,
    },
    container: {
      padding: 20,
      paddingBottom: 40,
    },
    header: {
      marginBottom: 24,
    },
    title: {
      fontSize: 32,
      fontWeight: '700',
      letterSpacing: -0.4,
      color: colors.textPrimary,
    },
    subtitle: {
      marginTop: 6,
      fontSize: 15,
      lineHeight: 22,
      color: colors.textSecondary,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 16,
      padding: 16,
      borderWidth: 1,
      borderColor: colors.border,
      marginBottom: 16,
    },
    sectionLabel: {
      fontSize: 12,
      fontWeight: '700',
      letterSpacing: 0.6,
      textTransform: 'uppercase',
      color: colors.textSecondary,
      marginBottom: 12,
    },
    segmentedControl: {
      flexDirection: 'row',
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 4,
      borderWidth: 1,
      borderColor: colors.border,
    },
    segment: {
      flex: 1,
      paddingVertical: 10,
      alignItems: 'center',
      borderRadius: 10,
    },
    segmentActive: {
      backgroundColor: colors.accent,
    },
    segmentDisabled: {
      opacity: 0.6,
    },
    segmentText: {
      fontSize: 15,
      fontWeight: '600',
    },
    segmentTextActive: {
      color: colors.accentText,
    },
    segmentTextInactive: {
      color: colors.textSecondary,
    },
    helperText: {
      marginTop: 10,
      fontSize: 13,
      lineHeight: 18,
      color: colors.textSecondary,
    },
    rangeRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
    },
    rangeSpacer: {
      width: 12,
    },
    inputGroup: {
      flex: 1,
    },
    inputLabel: {
      fontSize: 13,
      fontWeight: '600',
      color: colors.textPrimary,
      marginBottom: 6,
    },
    inputRow: {
      flexDirection: 'row',
      alignItems: 'center',
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 10,
      backgroundColor: colors.surface,
    },
    stepButton: {
      paddingVertical: 6,
      paddingHorizontal: 12,
    },
    stepButtonText: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.accent,
    },
    textInput: {
      flex: 1,
      paddingVertical: 8,
      textAlign: 'center',
      fontSize: 16,
      color: colors.textPrimary,
    },
    errorText: {
      color: colors.error,
    },
    statusHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 6,
    },
    statusChip: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 999,
      backgroundColor: colors.chipBackground,
    },
    statusChipText: {
      fontSize: 12,
      fontWeight: '600',
      color: colors.chipText,
    },
    statusValue: {
      fontSize: 40,
      fontWeight: '700',
      color: colors.textPrimary,
    },
    statusValueSmall: {
      fontSize: 20,
      fontWeight: '600',
      color: colors.textPrimary,
    },
    statusDetail: {
      marginTop: 8,
      fontSize: 13,
      lineHeight: 18,
      color: colors.textSecondary,
    },
    buttonRow: {
      marginTop: 4,
    },
    primaryButton: {
      borderRadius: 14,
      paddingVertical: 14,
      alignItems: 'center',
      backgroundColor: colors.accent,
    },
    primaryButtonPressed: {
      opacity: 0.85,
    },
    primaryButtonDisabled: {
      opacity: 0.5,
    },
    primaryButtonText: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.accentText,
    },
    secondaryButton: {
      marginTop: 10,
      borderRadius: 14,
      paddingVertical: 12,
      alignItems: 'center',
      borderWidth: 1,
      borderColor: colors.border,
    },
    secondaryButtonPressed: {
      opacity: 0.85,
    },
    secondaryButtonText: {
      fontSize: 15,
      fontWeight: '600',
      color: colors.textPrimary,
    },
    footnote: {
      marginTop: 16,
      fontSize: 12,
      lineHeight: 18,
      color: colors.textSecondary,
    },
  });

export default SimpleApp;