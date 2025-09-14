export default {
  // Run prettier on all files
  '**/*.{js,jsx,ts,tsx,json,md}': ['prettier --write'],

  // Run ESLint on TS/JS files
  '**/*.{js,jsx,ts,tsx}': [
    'eslint --fix',
    // Temporarily disable TypeScript check until Expo migration is complete
    // () => 'tsc --noEmit',
  ],

  // Run tests related to changed files
  '{src,tests}/**/*.{js,jsx,ts,tsx}': ['jest --bail --findRelatedTests --passWithNoTests'],

  // Check native iOS files
  'ios/**/*.{h,m,mm,swift}': [
    'cd ios && swiftlint',
    'cd ios && pod install', // Ensure CocoaPods is up to date
  ],

  // Check native Android files
  'android/**/*.{java,kt}': ['cd android && ./gradlew ktlintCheck'],
};
