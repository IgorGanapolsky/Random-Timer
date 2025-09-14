# SuperPassword Android Native Development

## Environment Setup
```bash
# Install dependencies
yarn install
# Build Android app
npm run android
# Run Android tests
./gradlew test
```

## Code Style Guidelines
- Use Kotlin for new native code
- Follow Android Kotlin Style Guide
- Document all public APIs with KDoc
- Follow SOLID principles
- Use Kotlin coroutines for async operations

## Security Requirements
- Use Android KeyStore for sensitive data storage
- Implement AES-256 encryption for data at rest
- Use BiometricPrompt API for biometrics
- Clear sensitive data from memory when app backgrounds
- Follow Android Security Best Practices

## Native Module Implementation
- Keep bridge modules small and focused
- Handle all errors appropriately
- Return promises for async operations
- Use proper memory management
- Document all bridge methods

## Testing Guidelines
- Write unit tests for all native code
- Test all error conditions
- Use JUnit and MockK for testing
- Mock biometric and keystore interactions
- Maintain 90%+ test coverage

## Build Configuration
- Support Android 7.0+ (API 24)
- Configure ProGuard rules properly
- Use proper signing configurations
- Enable all security features
- Set appropriate manifest permissions