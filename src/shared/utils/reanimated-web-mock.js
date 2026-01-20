// Mock for react-native-reanimated on web platform
// This prevents WorkletsError when running in browser

module.exports = {
  default: {
    call: () => {},
  },
  useSharedValue: (init) => ({ value: init }),
  useAnimatedStyle: (fn) => fn(),
  withTiming: (value) => value,
  withSpring: (value) => value,
  withSequence: (...values) => values[values.length - 1],
  withDelay: (_, animation) => animation,
  runOnJS: (fn) => fn,
  runOnUI: (fn) => fn,
  Easing: {
    linear: (x) => x,
    ease: (x) => x,
    bezier: () => (x) => x,
    in: () => (x) => x,
    out: () => (x) => x,
    inOut: () => (x) => x,
  },
  interpolate: (value) => value,
  Extrapolate: {
    CLAMP: 'clamp',
    EXTEND: 'extend',
    IDENTITY: 'identity',
  },
  cancelAnimation: () => {},
  makeMutable: (value) => ({ value }),
};
