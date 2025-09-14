import { BiometryTypes } from 'react-native-biometrics';

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

export interface BiometricPreferences {
  enabled: boolean;
  biometryType?: BiometryTypes;
  fallbackToPassword: boolean;
  requireBiometricForSensitiveActions: boolean;
}

export interface BiometricSettings {
  enableBiometric: boolean;
  allowFallback: boolean;
  requireBiometricForVault: boolean;
  requireBiometricForExport: boolean;
  biometryType?: BiometryTypes;
}

export type BiometricType = 'face_id' | 'touch_id' | 'fingerprint' | 'none';

export interface BiometricAuthContext {
  isEnabled: boolean;
  isAvailable: boolean;
  biometryType?: BiometryTypes;
  preferences: BiometricPreferences;
  lastUsed?: Date;
}
