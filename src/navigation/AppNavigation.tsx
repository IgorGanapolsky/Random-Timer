/**
 * AppNavigation
 * Root navigation for the app
 */

import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { TimerSetupScreen, ActiveTimerScreen } from '@features/timer';
import { TimerConfig } from '@features/timer';
import { useTheme } from '@shared/theme';

/**
 * Debug parameters for testing timer states without waiting.
 * Use via deep links: randomtimer://timer?debugTimeRemaining=5&debugState=warning
 */
export interface TimerDebugParams {
  /** Override remaining time in seconds */
  debugTimeRemaining?: number;
  /** Jump to specific state: 'running' | 'warning' | 'danger' | 'complete' */
  debugState?: 'running' | 'warning' | 'danger' | 'complete';
  /** Skip directly to alarm */
  debugSkipToAlarm?: boolean;
}

export type RootStackParamList = {
  Setup: undefined;
  Timer: { config: TimerConfig; debug?: TimerDebugParams };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function AppNavigation() {
  const { colors } = useTheme();

  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Setup"
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.background },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="Setup" component={TimerSetupScreen} />
        <Stack.Screen
          name="Timer"
          component={ActiveTimerScreen}
          options={{
            gestureEnabled: false, // Prevent swipe back during timer
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
