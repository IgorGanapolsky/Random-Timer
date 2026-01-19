# SecurePass Password Generator

SecurePass is a React Native CLI app for generating strong passwords locally on
device. It offers customizable rules, strength feedback, and a history list
with a premium upsell screen.

## Features
- Generate passwords with length slider and character toggles (uppercase,
  lowercase, numbers, symbols).
- Strength meter with crack-time estimate.
- One-tap copy to clipboard with haptic feedback.
- Password history with swipe-to-delete (free plan limit of 10).
- Theme settings (light, dark, system) and preference toggles.
- Premium screen with mocked purchase flow for now.

## Tech Stack
- React Native CLI + TypeScript
- React Navigation
- React Native Paper
- AsyncStorage
- react-native-linear-gradient, vector icons, haptics
- Jest

## Getting Started
1. Prerequisites: Node.js 18+, Yarn, React Native CLI, Xcode (macOS) or Android
   Studio.
2. Install dependencies:
   - yarn install
   - cd ios && pod install && cd ..
3. Run:
   - yarn start
   - yarn ios or yarn android

## Scripts
- yarn start
- yarn ios
- yarn android
- yarn lint
- yarn test
- yarn typecheck

## Configuration
- Optional Sentry: add SENTRY_DSN to .env for error reporting.

## Integrations (Stubbed)
- Ads placeholder: src/services/ads.tsx
- Firebase placeholder: src/services/firebase.ts
Replace these with real SDKs when enabling production services.

## Project Structure
```
src/
  components/
  constants/
  contexts/
  hooks/
  navigation/
  screens/
  services/
  types/
  utils/
```

## Testing
- yarn test
- yarn typecheck

## License
MIT

## Support
support@securepass.app
