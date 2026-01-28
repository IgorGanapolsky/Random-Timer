/**
 * TimerSetupScreen
 * Initial screen for configuring timer settings
 */

import { useState, useEffect, useCallback } from 'react';
import { StyleSheet, View, Switch, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen, Text, Button, GlassCard } from '@shared/components';
import { spacing, useTheme } from '@shared/theme';
import { analyticsService, AnalyticsEvents, AnalyticsScreens } from '@shared/services';
import { RangeSlider, DurationPicker, VolumeSlider } from '../components';
import { TimerConfig } from '../hooks/useRandomTimer';
import { storageService, DEFAULT_CONFIG } from '../services/storageService';
import { soundService } from '../services/soundService';

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
  const [volume, setVolume] = useState(1.0);

  // Load saved settings on mount and track screen view
  useEffect(() => {
    analyticsService.screen(AnalyticsScreens.TIMER_SETUP);
    const savedConfig = storageService.loadConfig();
    setConfig(savedConfig);
    setVolume(soundService.getVolume());
    soundService.initialize();
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

  const handleRandomModeToggle = useCallback((value: boolean) => {
    setConfig(prev => ({ ...prev, randomMode: value }));
    analyticsService.track(AnalyticsEvents.RANDOM_MODE_TOGGLED, { enabled: value });
  }, []);

  const handleVolumeChange = useCallback((newVolume: number) => {
    setVolume(newVolume);
    soundService.setVolume(newVolume);
    analyticsService.track(AnalyticsEvents.VOLUME_CHANGED, { volume: newVolume });
  }, []);

  const handleVolumePreview = useCallback(() => {
    soundService.play(500);
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
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text preset="h1" center>
            Random Timer
          </Text>
        </View>

        <View style={styles.content}>
          {/* Time Range Card */}
          <GlassCard delay={100} padding={spacing.md}>
            <Text preset="h4" style={styles.cardTitle}>
              ⏱️ Timer Range
            </Text>
            <RangeSlider
              min={5}
              max={120}
              minValue={config.minSeconds}
              maxValue={config.maxSeconds}
              onValueChange={handleRangeChange}
              step={5}
              minGap={10}
              formatValue={formatTime}
            />
          </GlassCard>

          {/* Alarm Settings Card */}
          <GlassCard delay={200} padding={spacing.md}>
            <Text preset="h4" style={styles.cardTitle}>
              🔔 Alarm
            </Text>
            <DurationPicker
              value={config.alarmDuration}
              onValueChange={handleDurationChange}
              options={[5, 10, 15, 30, 60]}
            />
            <View style={{ marginTop: spacing.sm }}>
              <VolumeSlider
                value={volume}
                onValueChange={handleVolumeChange}
                onSlidingComplete={handleVolumePreview}
              />
            </View>
          </GlassCard>

          {/* Random Mode Card */}
          <GlassCard delay={300} padding={spacing.md}>
            <View style={styles.randomModeRow}>
              <View style={styles.randomModeText}>
                <Text preset="h4">🎲 Random Mode</Text>
                <Text
                  preset="caption"
                  color={colors.textDim}
                  style={styles.randomModeCaption}
                  numberOfLines={2}
                >
                  Hide countdown timer
                </Text>
              </View>
              <Switch
                value={config.randomMode}
                onValueChange={handleRandomModeToggle}
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
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  cardTitle: {
    marginBottom: spacing.sm,
  },
  content: {
    gap: spacing.lg,
  },
  footer: {
    paddingBottom: spacing.md,
    paddingTop: spacing.xl,
  },
  header: {
    paddingBottom: spacing.lg,
    paddingTop: spacing.md,
  },
  randomModeCaption: {
    marginTop: spacing.xs,
  },
  randomModeRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  randomModeText: {
    flex: 1,
    marginRight: spacing.md,
  },
  scrollContent: {
    flexGrow: 1,
  },
  scrollView: {
    flex: 1,
  },
});
