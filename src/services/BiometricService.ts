import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';

export interface BiometricAuthResult {
  success: boolean;
  error?: string;
  biometryType?: BiometryTypes;
}

export interface BiometricCapabilities {
  available: boolean;
  biometryType?: BiometryTypes;
  error?: string;
}

export class BiometricService {
  private static instance: BiometricService;
  private rnBiometrics: ReactNativeBiometrics;

  private constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true,
    });
  }

  public static getInstance(): BiometricService {
    if (!BiometricService.instance) {
      BiometricService.instance = new BiometricService();
    }
    return BiometricService.instance;
  }

  /**
   * Check if biometric authentication is available on the device
   */
  public async checkBiometricCapabilities(): Promise<BiometricCapabilities> {
    try {
      const { available, biometryType } = await this.rnBiometrics.isSensorAvailable();
      return {
        available,
        biometryType: biometryType || undefined,
      };
    } catch (error) {
      return {
        available: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check if biometric authentication is enabled for the app
   */
  public async isBiometricEnabled(): Promise<boolean> {
    try {
      const credentials = await Keychain.getInternetCredentials('biometric_enabled');
      return credentials && credentials.password === 'true';
    } catch (error) {
      console.warn('Failed to check biometric enabled status:', error);
      return false;
    }
  }

  /**
   * Enable biometric authentication for the app
   */
  public async enableBiometric(): Promise<BiometricAuthResult> {
    try {
      const capabilities = await this.checkBiometricCapabilities();
      
      if (!capabilities.available) {
        return {
          success: false,
          error: 'Biometric authentication is not available on this device',
        };
      }

      // Create biometric key pair
      const { publicKey } = await this.rnBiometrics.createKeys();
      
      // Store the public key securely
      await Keychain.setInternetCredentials(
        'biometric_public_key',
        'public_key',
        publicKey
      );

      // Mark biometric as enabled
      await Keychain.setInternetCredentials(
        'biometric_enabled',
        'enabled',
        'true'
      );

      return {
        success: true,
        biometryType: capabilities.biometryType,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to enable biometric authentication',
      };
    }
  }

  /**
   * Disable biometric authentication for the app
   */
  public async disableBiometric(): Promise<BiometricAuthResult> {
    try {
      // Delete biometric keys
      await this.rnBiometrics.deleteKeys();
      
      // Remove stored credentials
      await Keychain.resetInternetCredentials('biometric_public_key');
      await Keychain.resetInternetCredentials('biometric_enabled');

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to disable biometric authentication',
      };
    }
  }

  /**
   * Authenticate using biometrics
   */
  public async authenticateWithBiometrics(): Promise<BiometricAuthResult> {
    try {
      const isEnabled = await this.isBiometricEnabled();
      if (!isEnabled) {
        return {
          success: false,
          error: 'Biometric authentication is not enabled',
        };
      }

      const capabilities = await this.checkBiometricCapabilities();
      if (!capabilities.available) {
        return {
          success: false,
          error: 'Biometric authentication is not available',
        };
      }

      // Create biometric signature
      const { success, signature } = await this.rnBiometrics.createSignature({
        promptMessage: 'Authenticate to access SuperPassword',
        cancelButtonText: 'Cancel',
      });

      if (success && signature) {
        return {
          success: true,
          biometryType: capabilities.biometryType,
        };
      } else {
        return {
          success: false,
          error: 'Biometric authentication failed',
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Biometric authentication error',
      };
    }
  }

  /**
   * Get the type of biometric authentication available
   */
  public async getBiometryType(): Promise<BiometryTypes | null> {
    try {
      const capabilities = await this.checkBiometricCapabilities();
      return capabilities.biometryType || null;
    } catch (error) {
      console.warn('Failed to get biometry type:', error);
      return null;
    }
  }

  /**
   * Check if Face ID is available (iOS only)
   */
  public async isFaceIdAvailable(): Promise<boolean> {
    const biometryType = await this.getBiometryType();
    return biometryType === BiometryTypes.FaceID;
  }

  /**
   * Check if Touch ID is available (iOS only)
   */
  public async isTouchIdAvailable(): Promise<boolean> {
    const biometryType = await this.getBiometryType();
    return biometryType === BiometryTypes.TouchID;
  }

  /**
   * Check if Fingerprint is available (Android only)
   */
  public async isFingerprintAvailable(): Promise<boolean> {
    const biometryType = await this.getBiometryType();
    return biometryType === BiometryTypes.Biometrics;
  }

  /**
   * Get user-friendly name for the biometric type
   */
  public async getBiometricTypeName(): Promise<string> {
    const biometryType = await this.getBiometryType();
    
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return 'Fingerprint';
      default:
        return 'Biometric Authentication';
    }
  }
}

export default BiometricService;
