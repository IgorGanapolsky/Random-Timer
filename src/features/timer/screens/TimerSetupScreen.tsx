/**
 * TimerSetupScreen
 * Initial screen for configuring timer settings
 */

import { StyleSheet, View, Switch } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Screen, Text, Button, GlassCard } from '@shared/components';
import { spacing, useTheme } from '@shared/theme';
import { RangeSlider, DurationPicker } from '../components';
import { TimerConfig } from '../hooks/useRandomTimer';
import { storageService, DEFAULT_CONFIG } from '../services/storageService';

type RootStackParamList = {
  Setup: undefined;
  Timer: { config: TimerConfig };
};

interface TimerSetupScreenProps {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Setup'>;
}

export function TimerSetupScreen({ navigation }: TimerSetupScreenProps) {
  const { colors } = useTheme();
  const [config, setConfig] = useState<TimerConfig>(DEFAULT_CONFIG);

  // Load saved settings on mount
  useEffect(() => {
    const savedConfig = storageService.loadConfig();
    setConfig(savedConfig);
  }, []);

  // Save settings when changed
  useEffect(() => {
    storageService.saveConfig(config);
  }, [config]);

  const handleRangeChange = useCallback((min: number, max: number) => {
    setConfig(prev => ({ ...prev, minSeconds: min, maxSeconds: max }));
  }, []);

  const handleDurationChange = useCallback((duration: number) => {
    setConfig(prev => ({ ...prev, alarmDuration: duration }));
  }, []);

  const handleMysteryToggle = useCallback((value: boolean) => {
    setConfig(prev => ({ ...prev, mysteryMode: value }));
  }, []);

  const handleStart = () => {
    navigation.navigate('Timer', { config });
  };

  const formatTime = (seconds: number) => {
    if (seconds >= 60) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
    }
    return `${seconds}s`;
  };

  return (
    <Screen preset="fill">
      <View style={styles.header}>
        <Text preset="h1" center>
          Random Timer
        </Text>
        <Text preset="body" center color={colors.textDim} style={styles.subtitle}>
          Set your timer range and let fate decide
        </Text>
      </View>

      <View style={styles.content}>
        {/* Time Range Card */}
        <GlassCard delay={100}>
          <Text preset="h4" style={styles.cardTitle}>
            ⏱️ Timer Range
          </Text>
          <Text preset="bodySmall" color={colors.textDim} style={styles.cardSubtitle}>
            Timer will go off randomly within this range
          </Text>

          <RangeSlider
            min={5}
            max={600}
            minValue={config.minSeconds}
            maxValue={config.maxSeconds}
            onValueChange={handleRangeChange}
            step={5}
            minGap={55}
            formatValue={formatTime}
          />
        </GlassCard>

        {/* Alarm Duration Card */}
        <GlassCard delay={200}>
          <Text preset="h4" style={styles.cardTitle}>
            🔔 Alarm Duration
          </Text>
          <Text preset="bodySmall" color={colors.textDim} style={styles.cardSubtitle}>
            How long the alarm will sound
          </Text>

          <DurationPicker
            value={config.alarmDuration}
            onValueChange={handleDurationChange}
            options={[5, 10, 15, 30, 60]}
          />
        </GlassCard>

        {/* Mystery Mode Card */}
        <GlassCard delay={300}>
          <View style={styles.mysteryRow}>
            <View style={styles.mysteryText}>
              <Text preset="h4">🎭 Mystery Mode</Text>
              <Text preset="bodySmall" color={colors.textDim}>
                Hide the remaining time for extra suspense
              </Text>
            </View>
            <Switch
              value={config.mysteryMode}
              onValueChange={handleMysteryToggle}
              trackColor={{
                false: colors.glass.background,
                true: colors.primary,
              }}
              thumbColor={colors.palette.neutral100}
            />
          </View>
        </GlassCard>
      </View>

      <View style={styles.footer}>
        <Button label="Start Timer" onPress={handleStart} size="lg" fullWidth />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: spacing['2xl'],
    paddingBottom: spacing.lg,
  },
  subtitle: {
    marginTop: spacing.sm,
  },
  content: {
    flex: 1,
    gap: spacing.lg,
  },
  cardTitle: {
    marginBottom: spacing.xs,
  },
  cardSubtitle: {
    marginBottom: spacing.lg,
  },
  mysteryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  mysteryText: {
    flex: 1,
    marginRight: spacing.md,
  },
  footer: {
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
  },
});
