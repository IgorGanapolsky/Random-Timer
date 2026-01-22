/**
 * Text Component
 * Typography component with preset styles and dynamic theming
 */

import { StyleSheet, Text as RNText, TextProps as RNTextProps, TextStyle } from 'react-native';
import { typography, useTheme } from '../theme';

type TextPreset = keyof typeof typography.presets;

interface TextProps extends RNTextProps {
  /** Typography preset */
  preset?: TextPreset;
  /** Text color (overrides theme) */
  color?: string;
  /** Center text */
  center?: boolean;
  /** Custom style */
  style?: TextStyle;
  children: React.ReactNode;
}

export function Text({
  preset = 'body',
  color,
  center = false,
  style,
  children,
  ...props
}: TextProps) {
  const { colors } = useTheme();
  const presetStyle = typography.presets[preset];
  const resolvedColor = color ?? colors.text;

  return (
    <RNText
      style={[presetStyle, { color: resolvedColor }, center && styles.centered, style]}
      {...props}
    >
      {children}
    </RNText>
  );
}

const styles = StyleSheet.create({
  centered: {
    textAlign: 'center',
  },
});
