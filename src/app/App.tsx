/**
 * App.tsx - Root App Component
 *
 * Architecture:
 * - Bootstrap hooks handle initialization (fonts, splash screen)
 * - AppProviders wraps with Redux, navigation, safe area providers
 */
import * as SplashScreen from 'expo-splash-screen';

import { AppNavigation } from '@navigation';

import { useFontLoading, useSplashScreen } from './bootstrap';
import { AppProviders } from './components/AppProviders';

SplashScreen.preventAutoHideAsync();

export function App() {
  const { areFontsLoaded, fontLoadError } = useFontLoading();

  const isReady = areFontsLoaded || !!fontLoadError;

  useSplashScreen(isReady);

  if (!isReady) {
    return null;
  }

  return (
    <AppProviders>
      <AppNavigation />
    </AppProviders>
  );
}
