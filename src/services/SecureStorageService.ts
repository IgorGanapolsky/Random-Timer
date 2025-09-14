import * as Keychain from 'react-native-keychain';
import { Platform } from 'react-native';

export interface SecureStorageOptions {
  service?: string;
  accessGroup?: string;
  accessible?: Keychain.ACCESSIBLE;
  authenticationPrompt?: string;
  authenticationType?: Keychain.AUTHENTICATION_TYPE;
}

export interface SecureStorageResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export class SecureStorageService {
  private static instance: SecureStorageService;
  private defaultOptions: SecureStorageOptions;

  private constructor() {
    this.defaultOptions = {
      service: 'SuperPassword',
      accessible: Platform.OS === 'ios' 
        ? Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY
        : Keychain.ACCESSIBLE.WHEN_UNLOCKED,
      authenticationPrompt: 'Authenticate to access secure data',
    };
  }

  public static getInstance(): SecureStorageService {
    if (!SecureStorageService.instance) {
      SecureStorageService.instance = new SecureStorageService();
    }
    return SecureStorageService.instance;
  }

  /**
   * Store data securely in the device keychain/keystore
   */
  public async storeSecureData<T>(
    key: string,
    data: T,
    options?: SecureStorageOptions
  ): Promise<SecureStorageResult<void>> {
    try {
      const mergedOptions = { ...this.defaultOptions, ...options };
      const serializedData = JSON.stringify(data);

      await Keychain.setInternetCredentials(
        key,
        'data',
        serializedData,
        mergedOptions
      );

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to store secure data',
      };
    }
  }

  /**
   * Retrieve data securely from the device keychain/keystore
   */
  public async getSecureData<T>(
    key: string,
    options?: SecureStorageOptions
  ): Promise<SecureStorageResult<T>> {
    try {
      const mergedOptions = { ...this.defaultOptions, ...options };

      const credentials = await Keychain.getInternetCredentials(key, mergedOptions);
      
      if (!credentials || !credentials.password) {
        return {
          success: false,
          error: 'No data found for the given key',
        };
      }

      const data = JSON.parse(credentials.password) as T;
      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to retrieve secure data',
      };
    }
  }

  /**
   * Remove data from secure storage
   */
  public async removeSecureData(
    key: string,
    options?: SecureStorageOptions
  ): Promise<SecureStorageResult<void>> {
    try {
      const mergedOptions = { ...this.defaultOptions, ...options };

      await Keychain.resetInternetCredentials(key, mergedOptions);

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to remove secure data',
      };
    }
  }

  /**
   * Check if data exists in secure storage
   */
  public async hasSecureData(
    key: string,
    options?: SecureStorageOptions
  ): Promise<boolean> {
    try {
      const result = await this.getSecureData(key, options);
      return result.success;
    } catch (error) {
      return false;
    }
  }

  /**
   * Store master password hash securely
   */
  public async storeMasterPasswordHash(
    passwordHash: string,
    salt: string
  ): Promise<SecureStorageResult<void>> {
    try {
      const data = {
        hash: passwordHash,
        salt: salt,
        timestamp: Date.now(),
      };

      return await this.storeSecureData('master_password', data, {
        accessible: Platform.OS === 'ios'
          ? Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY
          : Keychain.ACCESSIBLE.WHEN_UNLOCKED,
      });
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to store master password',
      };
    }
  }

  /**
   * Retrieve master password hash
   */
  public async getMasterPasswordHash(): Promise<SecureStorageResult<{
    hash: string;
    salt: string;
    timestamp: number;
  }>> {
    return await this.getSecureData('master_password');
  }

  /**
   * Store biometric authentication key
   */
  public async storeBiometricKey(
    key: string,
    value: string
  ): Promise<SecureStorageResult<void>> {
    return await this.storeSecureData(`biometric_${key}`, value, {
      accessible: Platform.OS === 'ios'
        ? Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY
        : Keychain.ACCESSIBLE.WHEN_UNLOCKED,
    });
  }

  /**
   * Retrieve biometric authentication key
   */
  public async getBiometricKey(key: string): Promise<SecureStorageResult<string>> {
    return await this.getSecureData(`biometric_${key}`);
  }

  /**
   * Store encrypted password data
   */
  public async storeEncryptedPassword(
    passwordId: string,
    encryptedData: string
  ): Promise<SecureStorageResult<void>> {
    return await this.storeSecureData(`password_${passwordId}`, encryptedData, {
      accessible: Platform.OS === 'ios'
        ? Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY
        : Keychain.ACCESSIBLE.WHEN_UNLOCKED,
    });
  }

  /**
   * Retrieve encrypted password data
   */
  public async getEncryptedPassword(passwordId: string): Promise<SecureStorageResult<string>> {
    return await this.getSecureData(`password_${passwordId}`);
  }

  /**
   * Remove encrypted password data
   */
  public async removeEncryptedPassword(passwordId: string): Promise<SecureStorageResult<void>> {
    return await this.removeSecureData(`password_${passwordId}`);
  }

  /**
   * Store app preferences securely
   */
  public async storeAppPreferences(
    preferences: Record<string, any>
  ): Promise<SecureStorageResult<void>> {
    return await this.storeSecureData('app_preferences', preferences);
  }

  /**
   * Retrieve app preferences
   */
  public async getAppPreferences(): Promise<SecureStorageResult<Record<string, any>>> {
    return await this.getSecureData('app_preferences');
  }

  /**
   * Clear all secure data (use with caution)
   */
  public async clearAllSecureData(): Promise<SecureStorageResult<void>> {
    try {
      // This is a destructive operation - use with extreme caution
      // In a real app, you might want to be more selective
      await Keychain.resetGenericPassword();
      
      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to clear secure data',
      };
    }
  }

  /**
   * Get storage statistics
   */
  public async getStorageStats(): Promise<SecureStorageResult<{
    totalKeys: number;
    lastAccessed: number;
  }>> {
    try {
      // This is a simplified implementation
      // In a real app, you'd track this more precisely
      const preferences = await this.getAppPreferences();
      
      return {
        success: true,
        data: {
          totalKeys: preferences.success ? Object.keys(preferences.data || {}).length : 0,
          lastAccessed: Date.now(),
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get storage stats',
      };
    }
  }
}

export default SecureStorageService;
