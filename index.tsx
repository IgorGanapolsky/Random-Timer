import { Platform } from 'react-native';
import '@expo/metro-runtime';
import { registerRootComponent } from 'expo';

import { App } from './src/app/App';

// Only import native-specific modules on native platforms
if (Platform.OS !== 'web') {
  // IMPORTANT: gesture-handler must be imported first
  require('react-native-gesture-handler');
  // IMPORTANT: reanimated must be imported at the root after gesture-handler
  require('react-native-reanimated');
}

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
