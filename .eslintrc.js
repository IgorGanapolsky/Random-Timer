// ESLint configuration following Subway_RN_Demo conventions
module.exports = {
  root: true,
  extends: [
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-native/all',
    'expo',
    'plugin:react/jsx-runtime',
    'prettier',
  ],
  plugins: ['prettier', 'react-native'],
  settings: {
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json',
      },
      'babel-module': {
        alias: {
          '@': './src',
        },
      },
    },
  },
  rules: {
    'prettier/prettier': 'error',
    // typescript-eslint
    '@typescript-eslint/array-type': 0,
    '@typescript-eslint/ban-ts-comment': 0,
    '@typescript-eslint/no-explicit-any': 0,
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      },
    ],
    '@typescript-eslint/no-var-requires': 0,
    '@typescript-eslint/no-require-imports': 0,
    '@typescript-eslint/no-empty-object-type': 0,
    // eslint
    'no-use-before-define': 0,
    'no-restricted-imports': [
      'error',
      {
        paths: [
          // Prefer named exports from 'react' instead of importing `React`
          {
            name: 'react',
            importNames: ['default'],
            message: "Import named exports from 'react' instead.",
          },
          {
            name: 'react-native',
            importNames: ['SafeAreaView'],
            message: "Use SafeAreaView from 'react-native-safe-area-context' instead.",
          },
          // Prevent direct MMKV imports - use storage adapter
          {
            name: 'react-native-mmkv',
            importNames: ['MMKV'],
            message:
              'Never import MMKV directly. Use the storage adapter from @/shared/utils/storage instead.',
          },
        ],
      },
    ],
    // react
    'react/prop-types': 0,
    // react-native
    'react-native/no-raw-text': 0,
    'react-native/no-unused-styles': 'off',
    // eslint-config-standard overrides
    'comma-dangle': 0,
    'no-global-assign': 0,
    quotes: 0,
    'space-before-function-paren': 0,
    // eslint-import
    'import/order': [
      'warn',
      {
        'newlines-between': 'never',
        groups: [['builtin', 'external'], 'internal', 'unknown', ['parent', 'sibling'], 'index'],
        distinctGroup: false,
        pathGroups: [
          {
            pattern: 'react',
            group: 'external',
            position: 'before',
          },
          {
            pattern: 'react-native',
            group: 'external',
            position: 'before',
          },
          {
            pattern: 'expo{,-*}',
            group: 'external',
            position: 'before',
          },
          {
            pattern: '@navigation{,/**}',
            group: 'internal',
            position: 'before',
          },
          {
            pattern: '@/**',
            group: 'unknown',
            position: 'after',
          },
        ],
        pathGroupsExcludedImportTypes: ['react', 'react-native', 'expo', 'expo-*'],
      },
    ],
    'import/newline-after-import': 1,
  },
  overrides: [
    {
      // Allow direct MMKV import ONLY in the storage index file
      files: ['src/shared/utils/storage/index.ts'],
      rules: {
        'no-restricted-imports': 'off',
      },
    },
  ],
};
