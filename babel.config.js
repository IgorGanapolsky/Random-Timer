/** @type {import('@babel/core').TransformOptions} */
module.exports = function (api) {
  // Get platform info before caching
  const caller = api.caller(c => c?.platform);
  const isWeb = caller === 'web';

  // Cache the config based on platform
  api.cache.using(() => caller);

  const plugins = [
    [
      'module-resolver',
      {
        alias: {
          '@navigation': './src/navigation',
          '@': './src',
          '@assets': './assets',
          '@shared': './src/shared',
          '@features': './src/features',
        },
      },
    ],
  ];

  // Add reanimated plugin only for native platforms (not web)
  if (!isWeb) {
    plugins.push('react-native-reanimated/plugin');
  }

  return {
    presets: ['babel-preset-expo'],
    plugins,
  };
};
