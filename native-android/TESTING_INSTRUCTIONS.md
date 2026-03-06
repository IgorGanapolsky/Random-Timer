# Testing Instructions - Android Notification Enhancements

## Overview
Manual testing guide for chronometer countdown and Material Design 3 notification enhancements.

## Prerequisites

**Build and install APK**:
```bash
cd native-android
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**Or install via Android Studio**:
1. Open `native-android` project
2. Run app on device/emulator
3. Grant notification permission when prompted

## Test Scenarios

### Test 1: Chronometer Countdown (Running Timer)

**Steps**:
1. Open Random Timer app
2. Configure timer:
   - Min: 30 seconds
   - Max: 2 minutes
3. Start timer
4. **Immediately pull down notification shade**

**Expected Results**:
- ✅ Notification shows "Timer Running"
- ✅ Chronometer displays countdown (e.g., "1:32", "1:31", "1:30"...)
- ✅ Countdown updates every 1 second
- ✅ Shows configured range: "30s - 2m"
- ✅ Three action buttons visible: "Pause", "+5 Min", "Stop"
- ✅ Purple accent color on notification icon/text

**Screenshots needed**:
- Notification shade (expanded view)
- Lock screen notification

---

### Test 2: Chronometer on Lock Screen

**Steps**:
1. Start timer (from Test 1)
2. **Lock device** (press power button)
3. **Wake device** (press power button, don't unlock)

**Expected Results**:
- ✅ Notification visible on lock screen
- ✅ Chronometer counting down
- ✅ Action buttons accessible without unlocking
- ✅ Tapping notification opens app

**Screenshots needed**:
- Lock screen with notification

---

### Test 3: Pause/Resume Timer

**Steps**:
1. Start timer
2. Tap "Pause" button in notification

**Expected Results (Paused)**:
- ✅ Notification title changes to "Timer Paused"
- ✅ Chronometer HIDDEN (no countdown displayed)
- ✅ Action buttons change: "Resume", "Reset", "Stop"
- ✅ Range text still shown: "30s - 2m"

**Steps (Resume)**:
3. Tap "Resume" button in notification

**Expected Results (Resumed)**:
- ✅ Notification title changes to "Timer Running"
- ✅ Chronometer REAPPEARS and continues countdown
- ✅ Action buttons change: "Pause", "+5 Min", "Stop"

**Screenshots needed**:
- Paused state (no chronometer)
- Resumed state (chronometer visible)

---

### Test 4: Extend Timer (+5 Minutes)

**Steps**:
1. Start timer with 1 minute duration
2. Wait for chronometer to show ~30 seconds remaining
3. Tap "+5 Min" button in notification

**Expected Results**:
- ✅ Chronometer immediately jumps to ~5:30 (5 minutes + 30 seconds remaining)
- ✅ Timer continues running without pause
- ✅ Notification does NOT dismiss or recreate
- ✅ No visual glitch or flash
- ✅ Can tap "+5 Min" multiple times (10 min, 15 min, etc.)

**Screenshots needed**:
- Before extend (0:30 remaining)
- After extend (5:30 remaining)

---

### Test 5: Reset Timer

**Steps**:
1. Start timer with 2 minute duration
2. Wait ~30 seconds
3. Pause timer (button in notification)
4. Tap "Reset" button in notification

**Expected Results**:
- ✅ Timer restarts from beginning (2 minutes)
- ✅ Timer automatically RESUMES (not paused)
- ✅ Chronometer shows full duration (2:00)
- ✅ Action buttons change to: "Pause", "+5 Min", "Stop"

**Screenshots needed**:
- Before reset (paused at 1:30)
- After reset (running at 2:00)

---

### Test 6: Stop Timer

**Steps**:
1. Start timer
2. Tap "Stop" button in notification

**Expected Results**:
- ✅ Notification immediately dismisses
- ✅ Service stops (no foreground notification)
- ✅ App returns to setup screen (if open)
- ✅ No residual notification or sound

---

### Test 7: Timer Completion (Alarm)

**Steps**:
1. Start timer with 10 second duration
2. Wait for timer to complete
3. Observe chronometer countdown to 0:00

**Expected Results**:
- ✅ Chronometer counts down: 0:10, 0:09, 0:08... 0:01, 0:00
- ✅ At 0:00, notification changes to "Time's Up!" (alarm notification)
- ✅ Alarm sound plays
- ✅ Vibration starts (if enabled)
- ✅ Chronometer replaced with "Stop" button
- ✅ High-priority alarm notification shown

**Screenshots needed**:
- Chronometer at 0:01
- Alarm notification

---

### Test 8: Hidden Mode (Edge Case)

**Steps**:
1. Enable "Hidden Mode" toggle in app
2. Start timer

**Expected Results**:
- ✅ Notification subtitle shows "Hidden Mode"
- ⚠️ **KNOWN ISSUE**: Chronometer still reveals countdown time
  - This is expected behavior (documented in NOTIFICATION_ENHANCEMENTS.md)
  - Future enhancement: hide chronometer in hidden mode

**Screenshots needed**:
- Hidden mode notification with chronometer (documents current behavior)

---

### Test 9: Multiple Quick Actions (Stress Test)

**Steps**:
1. Start timer
2. Rapidly tap:
   - Pause → Resume → Pause → Resume (4 taps)
   - Then: +5 Min → +5 Min → +5 Min (3 taps)

**Expected Results**:
- ✅ No crashes or ANRs
- ✅ Buttons respond to each tap
- ✅ Final state: Timer running with +15 minutes added
- ✅ Chronometer updates correctly
- ✅ No duplicate notifications

---

### Test 10: App in Background vs Foreground

**Steps**:
1. Start timer
2. **Test A**: Keep app open, observe notification
3. **Test B**: Press Home, observe notification
4. **Test C**: Open another app, observe notification

**Expected Results (all scenarios)**:
- ✅ Notification always visible (app foreground or background)
- ✅ Chronometer continues counting (no pause)
- ✅ Action buttons work in all scenarios

**Note**: This tests the removal of "only show when background" logic.

---

### Test 11: Battery Optimization (Long Timer)

**Steps**:
1. Start timer with 30 minute duration
2. Lock device
3. Wait 5 minutes
4. Unlock and check notification

**Expected Results**:
- ✅ Chronometer shows correct remaining time (e.g., 25:00)
- ✅ No drift or time jump
- ✅ Battery usage minimal in Settings > Battery > Random Timer

**To check battery**:
1. Settings > Battery
2. Find "Random Timer"
3. Should show "Background: Low" or "Optimized"

---

### Test 12: Material Design 3 Visual Check

**Steps**:
1. Start timer
2. Expand notification (pull down to show full view)

**Visual Inspection**:
- ✅ Icon tinted with purple accent (#8B5CF6)
- ✅ Text readable on dark notification background
- ✅ Action buttons use Material3 ripple effects
- ✅ Consistent spacing and padding
- ✅ Timer icon (clock) visible

**Compare to**:
- Google Clock timer notification
- System alarm notifications

---

### Test 13: Android Auto / Bluetooth (Optional)

**Prerequisites**:
- Android Auto connected OR Bluetooth headphones with media controls

**Steps**:
1. Start timer
2. Connect to Android Auto / Bluetooth device
3. Use media control buttons (play/pause/stop)

**Expected Results**:
- ✅ Media controls work when alarm is ringing
- ✅ Play/Pause/Stop buttons dismiss alarm
- ✅ Controls do NOT affect timer when running (only alarm)

**Note**: Media session only activated during alarm (not during timer countdown).

---

## Test Matrix (Device Coverage)

| Android Version | Device Type | Tester | Date | Status |
|-----------------|-------------|--------|------|--------|
| 12 (API 31)     | Pixel 5     |        |      | ⬜️ Pending |
| 13 (API 33)     | Samsung S21 |        |      | ⬜️ Pending |
| 14 (API 34)     | Pixel 7     |        |      | ⬜️ Pending |
| 15 (API 35)     | Emulator    |        |      | ⬜️ Pending |

**Priority**: Test on Android 14/15 first (most restrictive).

---

## Regression Testing

**Existing features to verify**:
- [ ] Sound plays at alarm (both INTENSE and GENTLE)
- [ ] Vibration works (if enabled in settings)
- [ ] Volume slider affects alarm volume
- [ ] Repeat mode loops timer after alarm
- [ ] Full-screen alarm opens when tapped
- [ ] Firebase Crashlytics logging works

---

## Performance Benchmarks

**Expected metrics**:
- APK size increase: +2 KB (new icon + code)
- Memory increase: 0 KB (no new allocations)
- Battery drain: 0% increase (chronometer is system-managed)
- Notification update frequency: 1 second (unchanged)

**How to measure**:
1. Android Studio Profiler
2. Settings > Battery > App usage
3. APK Analyzer (Build > Analyze APK)

---

## Bug Reporting Template

If you find issues, report with:

```
**Test**: [Test number/name]
**Device**: [Make/Model]
**Android Version**: [e.g., Android 14, API 34]
**Steps to Reproduce**:
1.
2.
3.

**Expected**: [What should happen]
**Actual**: [What actually happened]
**Screenshot**: [Attach if applicable]
**Logs**: [Logcat output, if available]
```

---

## Known Issues

1. **Chronometer reveals time in Hidden Mode**
   - Status: Expected behavior (documented)
   - Fix: Future enhancement to hide chronometer

2. **Chronometer shows "0:00" briefly before alarm**
   - Status: Normal (system limitation)
   - Impact: Visual only, <1 second flash

3. **Some OEMs limit action buttons to 2 on lock screen**
   - Status: Device limitation (Samsung, OnePlus)
   - Workaround: Prioritized buttons (Pause/Resume always shown)

---

## Success Criteria

**All tests pass if**:
- ✅ No crashes or ANRs
- ✅ Chronometer counts down in real-time
- ✅ All action buttons work from lock screen
- ✅ No battery drain increase
- ✅ Material Design 3 colors applied
- ✅ Regression tests pass (existing features work)

**Ship-blocking issues**:
- Crashes during extend/pause/resume
- Chronometer not updating
- Timer stops unexpectedly
- Notification not showing on lock screen

---

## Testing Sign-off

**Tester Name**: _______________
**Date**: _______________
**Build Version**: _______________
**Total Tests Passed**: _____ / 13
**Blocker Issues Found**: _____

**Approved for Release**: ⬜️ Yes  ⬜️ No

**Notes**:
```
[Additional observations or feedback]
```

---

## Automated Testing

**Run unit tests**:
```bash
./gradlew :app:testDebugUnitTest
```

**Expected output**:
```
> Task :app:testDebugUnitTest
BUILD SUCCESSFUL in 10s
```

**Test coverage**:
- Extension calculation
- Chronometer base time
- Action constants
- State transitions

**Note**: Full notification testing requires instrumented tests or manual verification due to Android framework dependencies.
