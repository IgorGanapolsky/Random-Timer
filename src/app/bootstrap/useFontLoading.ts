import { useFonts } from 'expo-font';
import {
  Inter_300Light,
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
} from '@expo-google-fonts/inter';
import {
  SpaceMono_400Regular,
  SpaceMono_700Bold,
} from '@expo-google-fonts/space-mono';

/**
 * Hook for loading custom fonts
 */
export function useFontLoading() {
  const [areFontsLoaded, fontLoadError] = useFonts({
    // Inter - Primary UI font
    Inter_300Light,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
    // Space Mono - Timer display font
    SpaceMono_400Regular,
    SpaceMono_700Bold,
  });

  return { areFontsLoaded, fontLoadError };
}
