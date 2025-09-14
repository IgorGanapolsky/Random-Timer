import { StorageService } from '../storage';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage');

const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

describe('StorageService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('isFirstLaunch', () => {
    it('should return true for first launch', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);

      const result = await StorageService.isFirstLaunch();
      expect(result).toBe(true);
    });

    it('should return false for subsequent launches', async () => {
      mockAsyncStorage.getItem.mockResolvedValue('false');

      const result = await StorageService.isFirstLaunch();
      expect(result).toBe(false);
    });

    it('should handle errors gracefully', async () => {
      mockAsyncStorage.getItem.mockRejectedValue(new Error('Storage error'));

      const result = await StorageService.isFirstLaunch();
      expect(result).toBe(true); // Default to first launch on error
    });
  });

  describe('setFirstLaunchComplete', () => {
    it('should set first launch complete', async () => {
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.setFirstLaunchComplete();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'first_launch_complete',
        'false'
      );
    });

    it('should handle errors gracefully', async () => {
      mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));

      await expect(StorageService.setFirstLaunchComplete()).resolves.not.toThrow();
    });
  });

  describe('saveUserPreferences', () => {
    it('should save user preferences', async () => {
      const preferences = {
        theme: 'dark',
        defaultOptions: {
          length: 16,
          includeUppercase: true,
          includeLowercase: true,
          includeNumbers: true,
          includeSymbols: true,
          excludeAmbiguous: false,
          customCharacters: '',
          excludeCharacters: '',
        },
        autoSave: true,
        hapticFeedback: true,
        showPasswordStrength: true,
        quickCopyEnabled: true,
      };

      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.saveUserPreferences(preferences);

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'user_preferences',
        JSON.stringify(preferences)
      );
    });

    it('should handle errors gracefully', async () => {
      const preferences = { theme: 'dark' };
      mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));

      await expect(StorageService.saveUserPreferences(preferences)).resolves.not.toThrow();
    });
  });

  describe('getUserPreferences', () => {
    it('should get user preferences', async () => {
      const preferences = {
        theme: 'dark',
        defaultOptions: {
          length: 16,
          includeUppercase: true,
          includeLowercase: true,
          includeNumbers: true,
          includeSymbols: true,
          excludeAmbiguous: false,
          customCharacters: '',
          excludeCharacters: '',
        },
        autoSave: true,
        hapticFeedback: true,
        showPasswordStrength: true,
        quickCopyEnabled: true,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(preferences));

      const result = await StorageService.getUserPreferences();

      expect(result).toEqual(preferences);
    });

    it('should return default preferences when none stored', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);

      const result = await StorageService.getUserPreferences();

      expect(result).toEqual({
        theme: 'system',
        defaultOptions: {
          length: 16,
          includeUppercase: true,
          includeLowercase: true,
          includeNumbers: true,
          includeSymbols: true,
          excludeAmbiguous: false,
          customCharacters: '',
          excludeCharacters: '',
        },
        autoSave: true,
        hapticFeedback: true,
        showPasswordStrength: true,
        quickCopyEnabled: true,
      });
    });

    it('should handle corrupted data gracefully', async () => {
      mockAsyncStorage.getItem.mockResolvedValue('invalid json');

      const result = await StorageService.getUserPreferences();

      expect(result).toEqual({
        theme: 'system',
        defaultOptions: {
          length: 16,
          includeUppercase: true,
          includeLowercase: true,
          includeNumbers: true,
          includeSymbols: true,
          excludeAmbiguous: false,
          customCharacters: '',
          excludeCharacters: '',
        },
        autoSave: true,
        hapticFeedback: true,
        showPasswordStrength: true,
        quickCopyEnabled: true,
      });
    });
  });

  describe('savePasswordHistory', () => {
    it('should save password history', async () => {
      const history = [
        { password: 'password1', timestamp: Date.now() },
        { password: 'password2', timestamp: Date.now() },
      ];

      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.savePasswordHistory(history);

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'password_history',
        JSON.stringify(history)
      );
    });

    it('should handle errors gracefully', async () => {
      const history = [{ password: 'test', timestamp: Date.now() }];
      mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));

      await expect(StorageService.savePasswordHistory(history)).resolves.not.toThrow();
    });
  });

  describe('getPasswordHistory', () => {
    it('should get password history', async () => {
      const history = [
        { password: 'password1', timestamp: Date.now() },
        { password: 'password2', timestamp: Date.now() },
      ];

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(history));

      const result = await StorageService.getPasswordHistory();

      expect(result).toEqual(history);
    });

    it('should return empty array when no history', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);

      const result = await StorageService.getPasswordHistory();

      expect(result).toEqual([]);
    });

    it('should handle corrupted data gracefully', async () => {
      mockAsyncStorage.getItem.mockResolvedValue('invalid json');

      const result = await StorageService.getPasswordHistory();

      expect(result).toEqual([]);
    });
  });

  describe('addPasswordToHistory', () => {
    it('should add password to history', async () => {
      const existingHistory = [
        { password: 'password1', timestamp: Date.now() },
      ];
      const newPassword = 'password2';

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(existingHistory));
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.addPasswordToHistory(newPassword);

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'password_history',
        JSON.stringify([
          { password: 'password2', timestamp: expect.any(Number) },
          { password: 'password1', timestamp: expect.any(Number) },
        ])
      );
    });

    it('should limit history to 10 items', async () => {
      const existingHistory = Array.from({ length: 10 }, (_, i) => ({
        password: `password${i}`,
        timestamp: Date.now(),
      }));
      const newPassword = 'password11';

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(existingHistory));
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.addPasswordToHistory(newPassword);

      const savedHistory = JSON.parse(mockAsyncStorage.setItem.mock.calls[0][1]);
      expect(savedHistory).toHaveLength(10);
      expect(savedHistory[0].password).toBe('password11');
    });

    it('should handle empty history', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.addPasswordToHistory('password1');

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'password_history',
        JSON.stringify([{ password: 'password1', timestamp: expect.any(Number) }])
      );
    });
  });

  describe('clearPasswordHistory', () => {
    it('should clear password history', async () => {
      mockAsyncStorage.removeItem.mockResolvedValue();

      await StorageService.clearPasswordHistory();

      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('password_history');
    });

    it('should handle errors gracefully', async () => {
      mockAsyncStorage.removeItem.mockRejectedValue(new Error('Storage error'));

      await expect(StorageService.clearPasswordHistory()).resolves.not.toThrow();
    });
  });

  describe('saveAdConfig', () => {
    it('should save ad configuration', async () => {
      const adConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 0,
      };

      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.saveAdConfig(adConfig);

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'ad_config',
        JSON.stringify(adConfig)
      );
    });

    it('should handle errors gracefully', async () => {
      const adConfig = { showBanner: true };
      mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));

      await expect(StorageService.saveAdConfig(adConfig)).resolves.not.toThrow();
    });
  });

  describe('getAdConfig', () => {
    it('should get ad configuration', async () => {
      const adConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 0,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(adConfig));

      const result = await StorageService.getAdConfig();

      expect(result).toEqual(adConfig);
    });

    it('should return default config when none stored', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);

      const result = await StorageService.getAdConfig();

      expect(result).toEqual({
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 0,
      });
    });

    it('should handle corrupted data gracefully', async () => {
      mockAsyncStorage.getItem.mockResolvedValue('invalid json');

      const result = await StorageService.getAdConfig();

      expect(result).toEqual({
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 0,
      });
    });
  });

  describe('incrementPasswordCount', () => {
    it('should increment password count', async () => {
      const existingConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 3,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(existingConfig));
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.incrementPasswordCount();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'ad_config',
        JSON.stringify({
          ...existingConfig,
          passwordsGeneratedSinceAd: 4,
        })
      );
    });

    it('should handle missing config', async () => {
      mockAsyncStorage.getItem.mockResolvedValue(null);
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.incrementPasswordCount();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'ad_config',
        JSON.stringify({
          showBanner: true,
          interstitialFrequency: 5,
          passwordsGeneratedSinceAd: 1,
        })
      );
    });
  });

  describe('resetPasswordCount', () => {
    it('should reset password count', async () => {
      const existingConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 5,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(existingConfig));
      mockAsyncStorage.setItem.mockResolvedValue();

      await StorageService.resetPasswordCount();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'ad_config',
        JSON.stringify({
          ...existingConfig,
          passwordsGeneratedSinceAd: 0,
        })
      );
    });
  });

  describe('shouldShowInterstitialAd', () => {
    it('should return true when count reaches frequency', async () => {
      const adConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 5,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(adConfig));

      const result = await StorageService.shouldShowInterstitialAd();

      expect(result).toBe(true);
    });

    it('should return false when count below frequency', async () => {
      const adConfig = {
        showBanner: true,
        interstitialFrequency: 5,
        passwordsGeneratedSinceAd: 3,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(adConfig));

      const result = await StorageService.shouldShowInterstitialAd();

      expect(result).toBe(false);
    });

    it('should return false when frequency is 0', async () => {
      const adConfig = {
        showBanner: true,
        interstitialFrequency: 0,
        passwordsGeneratedSinceAd: 5,
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(adConfig));

      const result = await StorageService.shouldShowInterstitialAd();

      expect(result).toBe(false);
    });
  });
});
