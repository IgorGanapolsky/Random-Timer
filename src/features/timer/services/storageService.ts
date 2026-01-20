/**
 * Storage Service
 * Persist timer settings using shared MMKV storage
 */

import { storage, StorageKeys } from '@shared/utils/storage';
import { TimerConfig } from '../hooks/useRandomTimer';

export const DEFAULT_CONFIG: TimerConfig = {
  minSeconds: 60,      // 1 minute
  maxSeconds: 300,     // 5 minutes
  alarmDuration: 10,   // 10 seconds
  mysteryMode: false,
};

export const storageService = {
  saveConfig(config: TimerConfig) {
    storage.set(StorageKeys.TIMER_SETTINGS, JSON.stringify(config));
  },

  loadConfig(): TimerConfig {
    const stored = storage.getString(StorageKeys.TIMER_SETTINGS);
    if (stored) {
      try {
        return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
      } catch {
        return DEFAULT_CONFIG;
      }
    }
    return DEFAULT_CONFIG;
  },

  clearConfig() {
    storage.delete(StorageKeys.TIMER_SETTINGS);
  },
};
