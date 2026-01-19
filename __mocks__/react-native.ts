const reactNativeMock = {
  Platform: {OS: 'ios', select: (obj: {ios?: unknown; default?: unknown}) => obj.ios ?? obj.default},
  StyleSheet: {create: (styles: Record<string, unknown>) => styles},
  NativeModules: {},
};

module.exports = reactNativeMock;
