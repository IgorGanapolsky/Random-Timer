module.exports = {
  testEnvironment: 'node',
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  transformIgnorePatterns: [
    'node_modules/'
  ],
  moduleNameMapper: {
    '^react-native$': '<rootDir>/__mocks__/react-native.js'
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  setupFilesAfterEnv: [],
  collectCoverageFrom: [
    'SimpleApp.tsx',
    'index.js',
  ],
  coverageThreshold: {
    global: {
      branches: 15,
      functions: 5,
      lines: 15,
      statements: 15,
    },
  },
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.[jt]sx?$',
};
