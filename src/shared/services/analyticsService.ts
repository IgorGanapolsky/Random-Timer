/**
 * Analytics Service
 * PostHog integration with 2026 best practices for React Native
 */

import PostHog, { PostHogOptions } from 'posthog-react-native';

// PostHog configuration
const POSTHOG_API_KEY = process.env.EXPO_PUBLIC_POSTHOG_API_KEY || '';
const POSTHOG_HOST = 'https://us.i.posthog.com';

type JsonPrimitive = string | number | boolean | null;
type JsonArray = JsonPrimitive[] | JsonObject[];
type JsonObject = { [key: string]: JsonPrimitive | JsonArray | JsonObject };
type EventProperties = JsonObject;

class AnalyticsService {
  private posthog: PostHog | null = null;
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized || !POSTHOG_API_KEY) {
      if (!POSTHOG_API_KEY && __DEV__) {
        console.log('[Analytics] No API key - analytics disabled');
      }
      return;
    }

    try {
      // 2026 Best Practices Configuration
      const options: PostHogOptions = {
        host: POSTHOG_HOST,
        // Capture app lifecycle events (install, update, open, background)
        captureAppLifecycleEvents: true,
        // Performance optimization: use memory persistence
        persistence: 'memory',
        // Disable features we don't need for better performance
        enableSessionReplay: false,
      };

      this.posthog = new PostHog(POSTHOG_API_KEY, options);
      await this.posthog.ready();
      this.initialized = true;

      if (__DEV__) {
        console.log('[Analytics] PostHog initialized with 2026 best practices');
      }
    } catch (error) {
      if (__DEV__) {
        console.error('[Analytics] Init failed:', error);
      }
    }
  }

  /**
   * Get the PostHog instance for Provider pattern
   */
  getClient(): PostHog | null {
    return this.posthog;
  }

  /**
   * Track a custom event
   */
  track(event: string, properties?: EventProperties): void {
    if (!this.posthog) return;
    this.posthog.capture(event, properties);
  }

  /**
   * Track screen view - call this manually in each screen
   * (More reliable than automatic screen tracking in React Native)
   */
  screen(name: string, properties?: EventProperties): void {
    if (!this.posthog) return;
    this.posthog.screen(name, properties);
  }

  /**
   * Identify user (for retention tracking)
   */
  identify(userId: string, traits?: EventProperties): void {
    if (!this.posthog) return;
    this.posthog.identify(userId, traits);
  }

  /**
   * Set user properties without identifying
   */
  setUserProperties(properties: EventProperties): void {
    if (!this.posthog) return;
    this.posthog.capture('$set', { $set: properties });
  }

  /**
   * Reset user identity (e.g., on logout)
   */
  reset(): void {
    if (!this.posthog) return;
    this.posthog.reset();
  }

  /**
   * Opt out of tracking (privacy)
   */
  optOut(): void {
    if (!this.posthog) return;
    this.posthog.optOut();
  }

  /**
   * Opt back in to tracking
   */
  optIn(): void {
    if (!this.posthog) return;
    this.posthog.optIn();
  }

  /**
   * Flush pending events
   */
  async flush(): Promise<void> {
    if (!this.posthog) return;
    await this.posthog.flush();
  }

  /**
   * Check if a feature flag is enabled
   */
  isFeatureEnabled(flagKey: string): boolean {
    if (!this.posthog) return false;
    return this.posthog.isFeatureEnabled(flagKey) ?? false;
  }

  /**
   * Get feature flag value (for multivariate flags)
   */
  getFeatureFlag(flagKey: string): string | boolean | undefined {
    if (!this.posthog) return undefined;
    return this.posthog.getFeatureFlag(flagKey);
  }

  /**
   * Reload feature flags from server
   */
  reloadFeatureFlags(): void {
    if (!this.posthog) return;
    this.posthog.reloadFeatureFlags();
  }
}

export const analyticsService = new AnalyticsService();

// Pre-defined event names for consistency
export const AnalyticsEvents = {
  // App lifecycle
  APP_OPENED: 'app_opened',
  APP_BACKGROUNDED: 'app_backgrounded',

  // Timer events
  TIMER_STARTED: 'timer_started',
  TIMER_COMPLETED: 'timer_completed',
  TIMER_PAUSED: 'timer_paused',
  TIMER_RESUMED: 'timer_resumed',
  TIMER_RESET: 'timer_reset',
  TIMER_STOPPED: 'timer_stopped',

  // Settings events
  SETTINGS_CHANGED: 'settings_changed',
  RANDOM_MODE_TOGGLED: 'random_mode_toggled',
  VOLUME_CHANGED: 'volume_changed',

  // Review events
  REVIEW_PROMPTED: 'review_prompted',
  REVIEW_COMPLETED: 'review_completed',
} as const;

// Screen names for consistent tracking
export const AnalyticsScreens = {
  TIMER_SETUP: 'Timer Setup',
  ACTIVE_TIMER: 'Active Timer',
  SETTINGS: 'Settings',
} as const;
