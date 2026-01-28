/**
 * App.tsx - Root App Component
 *
 * Architecture:
 * - Bootstrap hooks handle initialization (fonts, splash screen)
 * - AppProviders wraps with Redux, navigation, safe area providers
 */
import { useEffect } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { analyticsService, reviewService } from '@shared/services';
import { AppNavigation } from '@navigation';
import { useFontLoading, useSplashScreen } from './bootstrap';
import { AppProviders } from './components/AppProviders';

SplashScreen.preventAutoHideAsync();

export function App() {
  const { areFontsLoaded, fontLoadError } = useFontLoading();

  const isReady = areFontsLoaded || !!fontLoadError;

  useSplashScreen(isReady);

  // Initialize analytics and record session
  useEffect(() => {
    analyticsService.initialize();
    reviewService.recordSession();
  }, []);

  if (!isReady) {
    return null;
  }

  return (
    <AppProviders>
      <AppNavigation />
    </AppProviders>
  );
}
