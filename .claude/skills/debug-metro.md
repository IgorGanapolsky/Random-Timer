# Skill: Debug Metro

Diagnose and fix Metro bundler connection issues. Nuclear option for when nothing else works.

## Trigger
User invokes `/debug-metro` or mentions Metro connection problems, "unable to load script", or bundler not connecting.

## Workflow

Execute these steps autonomously:

### 1. Kill Existing Metro Processes
```bash
# Kill any running Metro processes
pkill -f "react-native.*start" || true
pkill -f "expo.*start" || true
pkill -f "metro" || true

# Also kill any process on port 8081
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
```

### 2. Clear All Caches
```bash
# Clear Expo cache
rm -rf .expo

# Clear Metro cache
rm -rf node_modules/.cache

# Clear Watchman (if installed)
watchman watch-del-all 2>/dev/null || true

# Clear temp files
rm -rf $TMPDIR/react-* 2>/dev/null || true
rm -rf $TMPDIR/metro-* 2>/dev/null || true
rm -rf $TMPDIR/haste-* 2>/dev/null || true
```

### 3. Android-Specific Fixes
```bash
# Setup ADB reverse proxy
adb reverse tcp:8081 tcp:8081

# Check device connection
adb devices
```

### 4. Verify Network
```bash
# Get local IP for Wi-Fi debugging
ipconfig getifaddr en0 || ipconfig getifaddr en1
```

Report the IP address for manual device configuration if needed.

### 5. Restart Metro Fresh
```bash
npm start
```

Or if that fails:
```bash
npx expo start --dev-client --clear
```

### 6. If Still Failing - Nuclear Option
```bash
# Remove node_modules and reinstall
rm -rf node_modules
npm install

# Regenerate native projects
npm run prebuild:clean

# For Android specifically
cd android && ./gradlew clean && cd ..
```

## Diagnostic Checks
- Is Metro actually running? Check for process on port 8081
- Can device reach the bundler? Test http://localhost:8081/status
- Is ADB connected? `adb devices` should show device
- Same network? Compare device IP with computer IP

## Output
Report:
1. What processes were killed
2. What caches were cleared
3. Current device connection status
4. Metro status (running/not running)
5. Any remaining issues and manual steps needed
