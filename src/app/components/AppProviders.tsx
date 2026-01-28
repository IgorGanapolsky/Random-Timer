import { type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as ReduxProvider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from '@shared/redux/store';
import { ThemeProvider, useTheme } from '@shared/theme';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Inner wrapper that has access to theme context
 */
function ThemedContainer({ children }: { children: ReactNode }) {
  const { colors } = useTheme();

  return <View style={[styles.container, { backgroundColor: colors.background }]}>{children}</View>;
}

/**
 * Provider composition wrapper
 * Order matters - providers that depend on others come later
 */
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <GestureHandlerRootView style={styles.container}>
      <ReduxProvider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <ThemeProvider>
            <SafeAreaProvider>
              <ThemedContainer>{children}</ThemedContainer>
            </SafeAreaProvider>
          </ThemeProvider>
        </PersistGate>
      </ReduxProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
