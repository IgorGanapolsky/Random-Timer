# Expo to React Native CLI Migration Plan

## 1. Initial Setup
- [ ] Create fresh React Native CLI project
- [ ] Copy over source code
- [ ] Set up TypeScript configuration
- [ ] Configure native module support

## 2. Dependencies to Remove
```json
{
  "expo": "*",
  "expo-build-properties": "*",
  "expo-dev-client": "*",
  "expo-secure-store": "*",
  "expo-status-bar": "*"
}
```

## 3. Dependencies to Add
```json
{
  "dependencies": {
    "@react-native-community/cli": "^11.3.7",
    "@react-native-community/cli-platform-android": "^11.3.7",
    "@react-native-community/cli-platform-ios": "^11.3.7",
    "react-native-keychain": "^8.1.2",
    "react-native-biometrics": "^3.0.1"
  }
}
```

## 4. Native Module Replacements
| Expo Module | Native Replacement |
|-------------|-------------------|
| expo-secure-store | react-native-keychain |
| expo-build-properties | native build settings |
| expo-dev-client | React Native CLI dev tools |
| expo-status-bar | react-native StatusBar |

## 5. Build Configuration Changes
- [ ] Remove eas.json
- [ ] Remove app.config.ts
- [ ] Set up android/build.gradle
- [ ] Configure ios/Podfile
- [ ] Update native app configurations

## 6. CI/CD Updates
- [ ] Remove EAS build workflows
- [ ] Configure React Native CLI builds
- [ ] Update build scripts
- [ ] Update test configurations

## 7. Documentation Updates
- [ ] Update README.md
- [ ] Update development guides
- [ ] Update build instructions
- [ ] Update deployment guides
