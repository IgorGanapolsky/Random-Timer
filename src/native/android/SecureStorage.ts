import { NativeModules } from 'react-native';

const { SecureStorageBridge } = NativeModules;

export default {
  setSecureItem: (key: string, value: string) => SecureStorageBridge.setSecureItem(key, value),
  getSecureItem: (key: string) => SecureStorageBridge.getSecureItem(key),
  removeSecureItem: (key: string) => SecureStorageBridge.removeSecureItem(key),
};
