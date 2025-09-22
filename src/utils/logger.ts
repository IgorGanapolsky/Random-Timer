/**
 * Simple logger utility for development and production
 */
class Logger {
  static log(message: string, ...args: any[]): void {
    if (__DEV__) {
      console.log(`[SecurePass] ${message}`, ...args);
    }
  }

  static warn(message: string, ...args: any[]): void {
    if (__DEV__) {
      console.warn(`[SecurePass] ${message}`, ...args);
    }
  }

  static error(message: string, ...args: any[]): void {
    console.error(`[SecurePass] ${message}`, ...args);
  }

  static debug(message: string, ...args: any[]): void {
    if (__DEV__) {
      console.debug(`[SecurePass] ${message}`, ...args);
    }
  }
}

export default Logger;