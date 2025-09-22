module.exports = {
  Platform: { OS: 'ios', select: (obj) => obj.ios || obj.default },
  StyleSheet: { create: (styles) => styles },
  NativeModules: {},
};
