import 'react-native-gesture-handler/jestSetup';

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Mock react-native-safe-area-context
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaProvider: ({ children }: { children: React.ReactNode }) => children,
  SafeAreaView: ({ children }: { children: React.ReactNode }) => children,
  useSafeAreaInsets: () => ({ top: 0, right: 0, bottom: 0, left: 0 }),
}));

// Mock react-native-paper
jest.mock('react-native-paper', () => ({
  Provider: ({ children }: { children: React.ReactNode }) => children,
  DefaultTheme: {},
  MD3LightTheme: {},
  MD3DarkTheme: {},
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialCommunityIcons', () => 'Icon');

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock react-native-biometrics
jest.mock('react-native-biometrics', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    isSensorAvailable: jest.fn(),
    createKeys: jest.fn(),
    deleteKeys: jest.fn(),
    createSignature: jest.fn(),
  })),
  BiometryTypes: {
    FaceID: 'FaceID',
    TouchID: 'TouchID',
    Biometrics: 'Biometrics',
  },
}));

// Mock react-native-keychain
jest.mock('react-native-keychain', () => ({
  setInternetCredentials: jest.fn(),
  getInternetCredentials: jest.fn(),
  resetInternetCredentials: jest.fn(),
  resetGenericPassword: jest.fn(),
  ACCESSIBLE: {
    WHEN_UNLOCKED: 'WHEN_UNLOCKED',
    WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY',
  },
  AUTHENTICATION_TYPE: {
    DEVICE_PASSCODE: 'DEVICE_PASSCODE',
    BIOMETRICS: 'BIOMETRICS',
  },
}));

// Mock Sentry
jest.mock('sentry-expo', () => ({
  init: jest.fn(),
  captureException: jest.fn(),
  withScope: jest.fn((callback) => callback({ setContext: jest.fn() })),
}));

// Mock Expo modules
jest.mock('expo-font', () => ({
  loadAsync: jest.fn(),
}));

jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn(),
  hideAsync: jest.fn(),
}));

jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
  selectionAsync: jest.fn(),
}));

jest.mock('expo-clipboard', () => ({
  setStringAsync: jest.fn(),
  getStringAsync: jest.fn(),
}));

// Mock Platform
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'ios',
  select: jest.fn((obj) => obj.ios),
}));

// Silence the warning: Animated: `useNativeDriver` is not supported
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
  log: jest.fn(),
};

// Setup global test timeout
jest.setTimeout(10000);
