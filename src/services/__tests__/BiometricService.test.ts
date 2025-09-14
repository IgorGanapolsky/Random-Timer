import BiometricService from '../BiometricService';
import ReactNativeBiometrics from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';

// Mock the dependencies
jest.mock('react-native-biometrics');
jest.mock('react-native-keychain');

const mockReactNativeBiometrics = ReactNativeBiometrics as jest.Mocked<typeof ReactNativeBiometrics>;
const mockKeychain = Keychain as jest.Mocked<typeof Keychain>;

describe('BiometricService', () => {
  let biometricService: BiometricService;

  beforeEach(() => {
    biometricService = BiometricService.getInstance();
    jest.clearAllMocks();
  });

  describe('getInstance', () => {
    it('should return the same instance (singleton)', () => {
      const instance1 = BiometricService.getInstance();
      const instance2 = BiometricService.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('checkBiometricCapabilities', () => {
    it('should return available biometric capabilities', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });

      const result = await biometricService.checkBiometricCapabilities();

      expect(result).toEqual({
        available: true,
        biometryType: 'FaceID',
      });
    });

    it('should handle unavailable biometrics', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: false,
        biometryType: null,
      });

      const result = await biometricService.checkBiometricCapabilities();

      expect(result).toEqual({
        available: false,
        biometryType: undefined,
      });
    });

    it('should handle errors gracefully', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockRejectedValue(
        new Error('Sensor error')
      );

      const result = await biometricService.checkBiometricCapabilities();

      expect(result).toEqual({
        available: false,
        error: 'Sensor error',
      });
    });
  });

  describe('isBiometricEnabled', () => {
    it('should return true when biometric is enabled', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'enabled',
        password: 'true',
      });

      const result = await biometricService.isBiometricEnabled();

      expect(result).toBe(true);
    });

    it('should return false when biometric is not enabled', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue(null);

      const result = await biometricService.isBiometricEnabled();

      expect(result).toBe(false);
    });

    it('should handle errors gracefully', async () => {
      mockKeychain.getInternetCredentials.mockRejectedValue(new Error('Keychain error'));

      const result = await biometricService.isBiometricEnabled();

      expect(result).toBe(false);
    });
  });

  describe('enableBiometric', () => {
    it('should enable biometric authentication successfully', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });
      mockReactNativeBiometrics.prototype.createKeys.mockResolvedValue({
        publicKey: 'test-public-key',
      });
      mockKeychain.setInternetCredentials.mockResolvedValue();

      const result = await biometricService.enableBiometric();

      expect(result).toEqual({
        success: true,
        biometryType: 'FaceID',
      });
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledTimes(2);
    });

    it('should fail when biometric is not available', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: false,
        biometryType: null,
      });

      const result = await biometricService.enableBiometric();

      expect(result).toEqual({
        success: false,
        error: 'Biometric authentication is not available on this device',
      });
    });

    it('should handle errors during enablement', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });
      mockReactNativeBiometrics.prototype.createKeys.mockRejectedValue(
        new Error('Key creation failed')
      );

      const result = await biometricService.enableBiometric();

      expect(result).toEqual({
        success: false,
        error: 'Key creation failed',
      });
    });
  });

  describe('disableBiometric', () => {
    it('should disable biometric authentication successfully', async () => {
      mockReactNativeBiometrics.prototype.deleteKeys.mockResolvedValue();
      mockKeychain.resetInternetCredentials.mockResolvedValue();

      const result = await biometricService.disableBiometric();

      expect(result).toEqual({
        success: true,
      });
      expect(mockKeychain.resetInternetCredentials).toHaveBeenCalledTimes(2);
    });

    it('should handle errors during disablement', async () => {
      mockReactNativeBiometrics.prototype.deleteKeys.mockRejectedValue(
        new Error('Key deletion failed')
      );

      const result = await biometricService.disableBiometric();

      expect(result).toEqual({
        success: false,
        error: 'Key deletion failed',
      });
    });
  });

  describe('authenticateWithBiometrics', () => {
    it('should authenticate successfully when enabled', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'enabled',
        password: 'true',
      });
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });
      mockReactNativeBiometrics.prototype.createSignature.mockResolvedValue({
        success: true,
        signature: 'test-signature',
      });

      const result = await biometricService.authenticateWithBiometrics();

      expect(result).toEqual({
        success: true,
        biometryType: 'FaceID',
      });
    });

    it('should fail when biometric is not enabled', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue(null);

      const result = await biometricService.authenticateWithBiometrics();

      expect(result).toEqual({
        success: false,
        error: 'Biometric authentication is not enabled',
      });
    });

    it('should fail when biometric is not available', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'enabled',
        password: 'true',
      });
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: false,
        biometryType: null,
      });

      const result = await biometricService.authenticateWithBiometrics();

      expect(result).toEqual({
        success: false,
        error: 'Biometric authentication is not available',
      });
    });

    it('should handle authentication failure', async () => {
      mockKeychain.getInternetCredentials.mockResolvedValue({
        username: 'enabled',
        password: 'true',
      });
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });
      mockReactNativeBiometrics.prototype.createSignature.mockResolvedValue({
        success: false,
        signature: null,
      });

      const result = await biometricService.authenticateWithBiometrics();

      expect(result).toEqual({
        success: false,
        error: 'Biometric authentication failed',
      });
    });
  });

  describe('getBiometricTypeName', () => {
    it('should return correct name for Face ID', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'FaceID',
      });

      const result = await biometricService.getBiometricTypeName();

      expect(result).toBe('Face ID');
    });

    it('should return correct name for Touch ID', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'TouchID',
      });

      const result = await biometricService.getBiometricTypeName();

      expect(result).toBe('Touch ID');
    });

    it('should return correct name for Fingerprint', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: 'Biometrics',
      });

      const result = await biometricService.getBiometricTypeName();

      expect(result).toBe('Fingerprint');
    });

    it('should return default name for unknown type', async () => {
      mockReactNativeBiometrics.prototype.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: null,
      });

      const result = await biometricService.getBiometricTypeName();

      expect(result).toBe('Biometric Authentication');
    });
  });
});
