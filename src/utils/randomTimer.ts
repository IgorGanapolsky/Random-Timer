/**
 * Random Timer Utility
 * Generates random intervals for timer functionality
 */

export interface RandomTimerConfig {
  minInterval: number; // in milliseconds
  maxInterval: number; // in milliseconds
  onTrigger: () => void;
}

export class RandomTimer {
  private config: RandomTimerConfig;
  private timeoutId: ReturnType<typeof setTimeout> | null = null;
  private isRunning: boolean = false;
  private nextTriggerTime: number | null = null;

  constructor(config: RandomTimerConfig) {
    this.config = config;
  }

  /**
   * Generate a random interval within the configured range
   */
  private generateRandomInterval(): number {
    const { minInterval, maxInterval } = this.config;
    return Math.floor(Math.random() * (maxInterval - minInterval + 1)) + minInterval;
  }

  /**
   * Start the random timer
   */
  start(): void {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    this.scheduleNext();
  }

  /**
   * Schedule the next trigger
   */
  private scheduleNext(): void {
    if (!this.isRunning) {
      return;
    }

    const interval = this.generateRandomInterval();
    this.nextTriggerTime = Date.now() + interval;

    this.timeoutId = setTimeout(() => {
      this.config.onTrigger();
      this.scheduleNext();
    }, interval);
  }

  /**
   * Stop the random timer
   */
  stop(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    this.isRunning = false;
    this.nextTriggerTime = null;
  }

  /**
   * Update the timer configuration
   */
  updateConfig(config: Partial<RandomTimerConfig>): void {
    this.config = { ...this.config, ...config };
    if (this.isRunning) {
      this.stop();
      this.start();
    }
  }

  /**
   * Get the time remaining until next trigger
   */
  getTimeRemaining(): number | null {
    if (!this.nextTriggerTime) {
      return null;
    }
    return Math.max(0, this.nextTriggerTime - Date.now());
  }

  /**
   * Check if timer is running
   */
  getIsRunning(): boolean {
    return this.isRunning;
  }
}
