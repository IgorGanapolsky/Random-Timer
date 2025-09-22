const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');
const path = require('path');

/**
 * Metro configuration for React Native 0.81.4
 * https://facebook.github.io/metro/docs/configuration
 */
const config = {
  transformer: {
    // Enable SVG support with react-native-svg-transformer
    babelTransformerPath: require.resolve('react-native-svg-transformer'),
    // Optimize bundle size
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
  resolver: {
    // Support for SVG files
    assetExts: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'psd', 'pdf', 'zip', 'mp3', 'mp4', 'mov', 'avi', 'wmv', 'mkv'],
    sourceExts: ['js', 'jsx', 'ts', 'tsx', 'svg'],
    // Support for absolute imports via @/ alias
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    // Platform-specific file extensions
    platforms: ['ios', 'android', 'native', 'web'],
  },
  watchFolders: [
    // Watch the src directory for changes
    path.resolve(__dirname, 'src'),
  ],
  resetCache: false,
  server: {
    port: 8081,
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
