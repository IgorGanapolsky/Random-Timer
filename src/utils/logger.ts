declare const __DEV__: boolean;

/**
 * Simple logger utility for development and production
 */
class Logger {
  static log(message: string, ...args: unknown[]): void {
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.log(`[SecurePass] ${message}`, ...args);
    }
  }

  static warn(message: string, ...args: unknown[]): void {
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.warn(`[SecurePass] ${message}`, ...args);
    }
  }

  static error(message: string, ...args: unknown[]): void {
    // eslint-disable-next-line no-console
    console.error(`[SecurePass] ${message}`, ...args);
  }

  static debug(message: string, ...args: unknown[]): void {
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.debug(`[SecurePass] ${message}`, ...args);
    }
  }
}

export default Logger;