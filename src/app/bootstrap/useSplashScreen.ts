import { useCallback, useEffect, useRef } from 'react';
import * as SplashScreen from 'expo-splash-screen';

/**
 * Hook for managing splash screen hide timing
 */
export function useSplashScreen(isReady: boolean) {
  const hasHiddenSplash = useRef(false);

  const hideSplash = useCallback(async () => {
    if (hasHiddenSplash.current) return;
    hasHiddenSplash.current = true;

    try {
      await SplashScreen.hideAsync();
    } catch (error) {
      console.warn('Error hiding splash screen:', error);
    }
  }, []);

  useEffect(() => {
    if (isReady) {
      hideSplash();
    }
  }, [isReady, hideSplash]);
}
