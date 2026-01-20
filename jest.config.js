/** @type {import('@jest/types').Config.ProjectConfig} */
module.exports = {
  preset: 'jest-expo',
  globals: {
    $RefreshReg$: () => {},
    $RefreshSig$: () => type => type,
  },
  setupFilesAfterEnv: ['<rootDir>/src/shared/test/setup.ts'],
  moduleNameMapper: {
    '^@shared/(.*)$': '<rootDir>/src/shared/$1',
    '^@navigation$': '<rootDir>/src/navigation',
    '^@navigation/(.*)$': '<rootDir>/src/navigation/$1',
    '^@assets/(.*)$': '<rootDir>/assets/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@/(.*)$': '<rootDir>/src/$1',
    // Mock all image files
    '\\.(png|jpg|jpeg|gif|svg)$': '<rootDir>/src/shared/test/mockFile.ts',
  },
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|native-base|react-native-svg|@reduxjs/toolkit|redux-persist|react-redux|immer)',
  ],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/ios/', '<rootDir>/android/'],
  collectCoverage: false,
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['json', 'json-summary', 'lcov', 'text', 'clover'],
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/src/shared/test/',
    '/__tests__/',
    '/assets/',
  ],
};
