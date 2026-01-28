/**
 * Review Service
 * Smart app store review prompts with eligibility tracking
 */

import { storage } from '../utils/storage';
import { analyticsService, AnalyticsEvents } from './analyticsService';

// Dynamically import to handle missing native module in Expo Go
let StoreReview: typeof import('expo-store-review') | null = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  StoreReview = require('expo-store-review');
} catch {
  // Native module not available (Expo Go)
  if (__DEV__) {
    console.log('[Review] expo-store-review not available - review prompts disabled');
  }
}

const STORAGE_KEYS = {
  FIRST_OPEN: 'review_first_open',
  SESSION_COUNT: 'review_session_count',
  SUCCESS_COUNT: 'review_success_count',
  LAST_PROMPT: 'review_last_prompt',
  PROMPT_COUNT: 'review_prompt_count',
};

// Eligibility thresholds (based on 2026 best practices)
const THRESHOLDS = {
  MIN_SESSIONS: 3, // At least 3 app opens
  MIN_DAYS: 7, // At least 7 days since first open
  MIN_SUCCESS_EVENTS: 2, // At least 2 timer completions
  DAYS_BETWEEN_PROMPTS: 90, // Wait 90 days between prompts
  MAX_PROMPTS_PER_YEAR: 3, // iOS limit: 3 prompts per 365 days
};

class ReviewService {
  /**
   * Record app session start
   */
  recordSession(): void {
    // Set first open date if not set
    const firstOpen = storage.getString(STORAGE_KEYS.FIRST_OPEN);
    if (!firstOpen) {
      storage.set(STORAGE_KEYS.FIRST_OPEN, new Date().toISOString());
    }

    // Increment session count
    const sessionCount = storage.getNumber(STORAGE_KEYS.SESSION_COUNT) || 0;
    storage.set(STORAGE_KEYS.SESSION_COUNT, sessionCount + 1);
  }

  /**
   * Record a success event (timer completion)
   */
  recordSuccess(): void {
    const successCount = storage.getNumber(STORAGE_KEYS.SUCCESS_COUNT) || 0;
    storage.set(STORAGE_KEYS.SUCCESS_COUNT, successCount + 1);
  }

  /**
   * Check if user is eligible for review prompt
   */
  private async checkEligibility(): Promise<boolean> {
    // Check if store review is available on this device
    if (!StoreReview) return false;

    const isAvailable = await StoreReview.isAvailableAsync();
    if (!isAvailable) return false;

    const now = new Date();

    // Check session count
    const sessionCount = storage.getNumber(STORAGE_KEYS.SESSION_COUNT) || 0;
    if (sessionCount < THRESHOLDS.MIN_SESSIONS) return false;

    // Check days since first open
    const firstOpenStr = storage.getString(STORAGE_KEYS.FIRST_OPEN);
    if (!firstOpenStr) return false;
    const firstOpen = new Date(firstOpenStr);
    const daysSinceFirstOpen = Math.floor(
      (now.getTime() - firstOpen.getTime()) / (1000 * 60 * 60 * 24),
    );
    if (daysSinceFirstOpen < THRESHOLDS.MIN_DAYS) return false;

    // Check success events
    const successCount = storage.getNumber(STORAGE_KEYS.SUCCESS_COUNT) || 0;
    if (successCount < THRESHOLDS.MIN_SUCCESS_EVENTS) return false;

    // Check days since last prompt
    const lastPromptStr = storage.getString(STORAGE_KEYS.LAST_PROMPT);
    if (lastPromptStr) {
      const lastPrompt = new Date(lastPromptStr);
      const daysSinceLastPrompt = Math.floor(
        (now.getTime() - lastPrompt.getTime()) / (1000 * 60 * 60 * 24),
      );
      if (daysSinceLastPrompt < THRESHOLDS.DAYS_BETWEEN_PROMPTS) return false;
    }

    // Check annual prompt limit
    const promptCount = storage.getNumber(STORAGE_KEYS.PROMPT_COUNT) || 0;
    if (promptCount >= THRESHOLDS.MAX_PROMPTS_PER_YEAR) {
      // Reset if it's been a year since first prompt
      // (simplified - in production, track individual prompt dates)
      return false;
    }

    return true;
  }

  /**
   * Request review if eligible
   * Call this after positive moments (timer completion)
   */
  async maybeRequestReview(): Promise<boolean> {
    if (!StoreReview) return false;

    const eligible = await this.checkEligibility();
    if (!eligible) return false;

    try {
      // Track the prompt attempt
      analyticsService.track(AnalyticsEvents.REVIEW_PROMPTED);

      // Request the review
      await StoreReview.requestReview();

      // Update tracking (we don't know if user actually reviewed)
      storage.set(STORAGE_KEYS.LAST_PROMPT, new Date().toISOString());
      const promptCount = storage.getNumber(STORAGE_KEYS.PROMPT_COUNT) || 0;
      storage.set(STORAGE_KEYS.PROMPT_COUNT, promptCount + 1);

      return true;
    } catch (error) {
      if (__DEV__) {
        console.error('[Review] Failed to request review:', error);
      }
      return false;
    }
  }

  /**
   * Check if review prompt is available (for UI hints)
   */
  async isReviewAvailable(): Promise<boolean> {
    if (!StoreReview) return false;
    return StoreReview.isAvailableAsync();
  }

  /**
   * Get current eligibility stats (for debugging)
   */
  getStats(): {
    sessionCount: number;
    successCount: number;
    daysSinceFirstOpen: number;
    promptCount: number;
  } {
    const firstOpenStr = storage.getString(STORAGE_KEYS.FIRST_OPEN);
    const firstOpen = firstOpenStr ? new Date(firstOpenStr) : new Date();
    const daysSinceFirstOpen = Math.floor(
      (new Date().getTime() - firstOpen.getTime()) / (1000 * 60 * 60 * 24),
    );

    return {
      sessionCount: storage.getNumber(STORAGE_KEYS.SESSION_COUNT) || 0,
      successCount: storage.getNumber(STORAGE_KEYS.SUCCESS_COUNT) || 0,
      daysSinceFirstOpen,
      promptCount: storage.getNumber(STORAGE_KEYS.PROMPT_COUNT) || 0,
    };
  }

  /**
   * Reset all review tracking (for testing)
   */
  reset(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      storage.delete(key);
    });
  }
}

export const reviewService = new ReviewService();
