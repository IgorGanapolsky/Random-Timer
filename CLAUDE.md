# SuperPassword iOS Native Development

## Environment Setup
```bash
# Install dependencies
pod install
# Build iOS app
npm run ios
# Run iOS tests
xcodebuild test -workspace SuperPassword.xcworkspace -scheme SuperPassword -destination 'platform=iOS Simulator,name=iPhone 15'
```

## Code Style Guidelines
- Use Swift for new native code
- Follow Apple's Swift API Design Guidelines
- Document all public APIs with SwiftDoc
- Follow SOLID principles
- Use Swift Result type for error handling

## Security Requirements
- Use Keychain for sensitive data storage
- Implement AES-256 encryption for data at rest
- Use Local Authentication framework for biometrics
- Clear sensitive data from memory when app backgrounds
- Follow Apple's Security Guidelines

## Native Module Implementation
- Keep bridge modules small and focused
- Handle all errors appropriately
- Return promises for async operations
- Use proper memory management
- Document all bridge methods

## Testing Guidelines
- Write unit tests for all native code
- Test all error conditions
- Use XCTest for native tests
- Mock biometric and keychain interactions
- Maintain 90%+ test coverage

## Build Configuration
- Support iOS 15.0 and above
- Use CocoaPods for dependencies
- Configure proper signing
- Enable all security features
- Set appropriate capability flags