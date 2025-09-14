import SecureStorageService from '../SecureStorageService';
import * as Keychain from 'react-native-keychain';

// Mock the dependencies
jest.mock('react-native-keychain');

const mockKeychain = Keychain as jest.Mocked<typeof Keychain>;

describe('SecureStorageService', () => {
  let secureStorageService: SecureStorageService;

  beforeEach(() => {
    secureStorageService = SecureStorageService.getInstance();
    jest.clearAllMocks();
  });

  describe('getInstance', () => {
    it('should return the same instance (singleton)', () => {
      const instance1 = SecureStorageService.getInstance();
      const instance2 = SecureStorageService.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('storeSecureData', () => {
    it('should store data successfully', async () => {
      const testData = { username: 'test', password: 'secret' };
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.storeSecureData('test_key', testData);

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledWith(
        'test_key',
        'data',
        JSON.stringify(testData),
        expect.any(Object)
      );
    });

    it('should handle errors gracefully', async () => {
      const testData = { username: 'test', password: 'secret' };
      mockKeychain.setInternetCredentials.mockRejectedValue(new Error('Storage error'));

      const result = await secureStorageService.storeSecureData('test_key', testData);

      expect(result).toEqual({
        success: false,
        error: 'Storage error',
      });
    });
  });

  describe('getSecureData', () => {
    it('should retrieve data successfully', async () => {
      const testData = { username: 'test', password: 'secret' };
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: JSON.stringify(testData),
      });

      const result = await secureStorageService.getSecureData('test_key');

      expect(result).toEqual({
        success: true,
        data: testData,
      });
    });

    it('should handle missing data', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue(null);

      const result = await secureStorageService.getSecureData('test_key');

      expect(result).toEqual({
        success: false,
        error: 'No data found for the given key',
      });
    });

    it('should handle errors gracefully', async () => {
      mockKeychain.getInternetCredentials.mockRejectedValue(new Error('Retrieval error'));

      const result = await secureStorageService.getSecureData('test_key');

      expect(result).toEqual({
        success: false,
        error: 'Retrieval error',
      });
    });
  });

  describe('removeSecureData', () => {
    it('should remove data successfully', async () => {
      mockKeychain.resetInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.removeSecureData('test_key');

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.resetInternetCredentials).toHaveBeenCalledWith(
        'test_key',
        expect.any(Object)
      );
    });

    it('should handle errors gracefully', async () => {
      mockKeychain.resetInternetCredentials.mockRejectedValue(new Error('Removal error'));

      const result = await secureStorageService.removeSecureData('test_key');

      expect(result).toEqual({
        success: false,
        error: 'Removal error',
      });
    });
  });

  describe('hasSecureData', () => {
    it('should return true when data exists', async () => {
      const testData = { username: 'test', password: 'secret' };
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: JSON.stringify(testData),
      });

      const result = await secureStorageService.hasSecureData('test_key');

      expect(result).toBe(true);
    });

    it('should return false when data does not exist', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue(null);

      const result = await secureStorageService.hasSecureData('test_key');

      expect(result).toBe(false);
    });

    it('should return false on error', async () => {
      mockKeychain.getInternetCredentials.mockRejectedValue(new Error('Error'));

      const result = await secureStorageService.hasSecureData('test_key');

      expect(result).toBe(false);
    });
  });

  describe('storeMasterPasswordHash', () => {
    it('should store master password hash successfully', async () => {
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.storeMasterPasswordHash('hash123', 'salt456');

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledWith(
        'master_password',
        'data',
        JSON.stringify({
          hash: 'hash123',
          salt: 'salt456',
          timestamp: expect.any(Number),
        }),
        expect.any(Object)
      );
    });
  });

  describe('getMasterPasswordHash', () => {
    it('should retrieve master password hash successfully', async () => {
      const hashData = {
        hash: 'hash123',
        salt: 'salt456',
        timestamp: Date.now(),
      };
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: JSON.stringify(hashData),
      });

      const result = await secureStorageService.getMasterPasswordHash();

      expect(result).toEqual({
        success: true,
        data: hashData,
      });
    });
  });

  describe('storeBiometricKey', () => {
    it('should store biometric key successfully', async () => {
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.storeBiometricKey('test_key', 'test_value');

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledWith(
        'biometric_test_key',
        'data',
        'test_value',
        expect.any(Object)
      );
    });
  });

  describe('getBiometricKey', () => {
    it('should retrieve biometric key successfully', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: 'test_value',
      });

      const result = await secureStorageService.getBiometricKey('test_key');

      expect(result).toEqual({
        success: true,
        data: 'test_value',
      });
    });
  });

  describe('storeEncryptedPassword', () => {
    it('should store encrypted password successfully', async () => {
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.storeEncryptedPassword('pass123', 'encrypted_data');

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledWith(
        'password_pass123',
        'data',
        'encrypted_data',
        expect.any(Object)
      );
    });
  });

  describe('getEncryptedPassword', () => {
    it('should retrieve encrypted password successfully', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: 'encrypted_data',
      });

      const result = await secureStorageService.getEncryptedPassword('pass123');

      expect(result).toEqual({
        success: true,
        data: 'encrypted_data',
      });
    });
  });

  describe('removeEncryptedPassword', () => {
    it('should remove encrypted password successfully', async () => {
      mockKeychain.resetInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.removeEncryptedPassword('pass123');

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.resetInternetCredentials).toHaveBeenCalledWith(
        'password_pass123',
        expect.any(Object)
      );
    });
  });

  describe('storeAppPreferences', () => {
    it('should store app preferences successfully', async () => {
      const preferences = { theme: 'dark', language: 'en' };
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await secureStorageService.storeAppPreferences(preferences);

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledWith(
        'app_preferences',
        'data',
        JSON.stringify(preferences),
        expect.any(Object)
      );
    });
  });

  describe('getAppPreferences', () => {
    it('should retrieve app preferences successfully', async () => {
      const preferences = { theme: 'dark', language: 'en' };
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: JSON.stringify(preferences),
      });

      const result = await secureStorageService.getAppPreferences();

      expect(result).toEqual({
        success: true,
        data: preferences,
      });
    });
  });

  describe('clearAllSecureData', () => {
    it('should clear all secure data successfully', async () => {
      mockKeychain.resetGenericPassword.mockResolvedValue();

      const result = await secureStorageService.clearAllSecureData();

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.resetGenericPassword).toHaveBeenCalled();
    });

    it('should handle errors gracefully', async () => {
      mockKeychain.resetGenericPassword.mockRejectedValue(new Error('Clear error'));

      const result = await secureStorageService.clearAllSecureData();

      expect(result).toEqual({
        success: false,
        error: 'Clear error',
      });
    });
  });

  describe('getStorageStats', () => {
    it('should return storage stats successfully', async () => {
      const preferences = { theme: 'dark', language: 'en', setting: 'value' };
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'data',
        password: JSON.stringify(preferences),
      });

      const result = await secureStorageService.getStorageStats();

      expect(result).toEqual({
        success: true,
        data: {
          totalKeys: 3,
          lastAccessed: expect.any(Number),
        },
      });
    });

    it('should handle errors gracefully', async () => {
      mockKeychain.getInternetCredentials.mockRejectedValue(new Error('Stats error'));

      const result = await secureStorageService.getStorageStats();

      expect(result).toEqual({
        success: false,
        error: 'Stats error',
      });
    });
  });
});
