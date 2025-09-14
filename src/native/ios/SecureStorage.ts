import { NativeModules } from 'react-native';

const { SecureStorageBridge } = NativeModules;

interface ISecureStorage {
  /**
   * Store an encrypted value in the iOS Keychain
   * @param key - The key to store the value under
   * @param value - The value to encrypt and store
   * @returns Promise<boolean> - Whether the operation was successful
   */
  setSecureItem(key: string, value: string): Promise<boolean>;

  /**
   * Retrieve and decrypt a value from the iOS Keychain
   * @param key - The key of the value to retrieve
   * @returns Promise<string> - The decrypted value
   */
  getSecureItem(key: string): Promise<string>;

  /**
   * Remove a value from the iOS Keychain
   * @param key - The key of the value to remove
   * @returns Promise<boolean> - Whether the operation was successful
   */
  removeSecureItem(key: string): Promise<boolean>;
}

export default SecureStorageBridge as ISecureStorage;
