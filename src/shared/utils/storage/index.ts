import { MMKV } from 'react-native-mmkv';

/**
 * MMKV Storage Singleton
 *
 * IMPORTANT: Never import MMKV directly elsewhere in the app.
 * Always use this singleton to ensure consistent storage behavior.
 */
export const storage = new MMKV({
  id: 'random-timer-storage',
});

/**
 * Type-safe storage helpers
 */
export const StorageKeys = {
  TIMER_SETTINGS: 'timer-settings',
  ONBOARDING_COMPLETE: 'onboarding-complete',
} as const;

export type StorageKey = (typeof StorageKeys)[keyof typeof StorageKeys];
