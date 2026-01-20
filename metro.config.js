/* eslint-env node */
// Metro config with Expo compatibility and path aliases
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

config.transformer.getTransformOptions = async () => ({
  transform: {
    // Inline requires for deferred loading of large dependencies
    inlineRequires: true,
  },
});

// Support for axios/apisauce compatibility
config.resolver.unstable_conditionNames = ['require', 'default', 'browser'];

// Support for cjs extension (Firebase, etc.)
config.resolver.sourceExts.push('cjs');

// Configure SVG transformer
const { assetExts, sourceExts } = config.resolver;
config.transformer.babelTransformerPath = require.resolve('react-native-svg-transformer');
config.resolver.assetExts = assetExts.filter(ext => ext !== 'svg');
config.resolver.sourceExts = [...sourceExts, 'svg'];

// Add path aliases to match TypeScript config
config.resolver.alias = {
  '@': path.resolve(__dirname, 'src'),
  '@assets': path.resolve(__dirname, 'assets'),
  '@navigation': path.resolve(__dirname, 'src/navigation'),
  '@shared': path.resolve(__dirname, 'src/shared'),
  '@features': path.resolve(__dirname, 'src/features'),
};

// Save original resolver to preserve Expo's default resolution logic
const originalResolveRequest = config.resolver.resolveRequest;

// Mock native modules on web platform to prevent errors
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web') {
    // Mock react-native-reanimated on web
    if (moduleName === 'react-native-reanimated') {
      return {
        filePath: path.resolve(__dirname, 'src/shared/utils/reanimated-web-mock.js'),
        type: 'sourceFile',
      };
    }
  }

  // Use original Expo resolver for everything else
  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }

  return context.resolveRequest(context, moduleName, platform);
};

// Explicitly set project root
config.projectRoot = __dirname;
config.watchFolders = [__dirname];

module.exports = config;
