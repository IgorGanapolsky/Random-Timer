# Lock Screen Testing Guide

## Testing Checklist

### iOS Testing (Device Required)

**Prerequisites:**
- Physical iPhone running iOS 16.1+
- Xcode 15+ with development provisioning profile
- iPhone 14 Pro+ for Dynamic Island testing (optional)

**Test Scenarios:**

1. **Lock Screen Live Activity Display**
   - [ ] Start timer, lock iPhone
   - [ ] Verify Live Activity appears on Lock Screen
   - [ ] Verify timer icon animates (pulsing)
   - [ ] Verify circular progress ring updates
   - [ ] Verify status colors change (emerald → amber → rose)
   - [ ] Verify timer range shows correctly

2. **Dynamic Island (iPhone 14 Pro+)**
   - [ ] Start timer with screen unlocked
   - [ ] Verify compact view appears in Dynamic Island
   - [ ] Long-press Dynamic Island
   - [ ] Verify expanded view shows full timer info
   - [ ] Verify animations are smooth

3. **Alarm State**
   - [ ] Let timer reach alarm state
   - [ ] Verify bell icon bounces
   - [ ] Verify alarm notification appears
   - [ ] Verify Live Activity ends or updates

4. **Accessibility**
   - [ ] Enable VoiceOver (Settings → Accessibility → VoiceOver)
   - [ ] Navigate to Live Activity
   - [ ] Verify VoiceOver announces timer info correctly
   - [ ] Enable Dynamic Type large text
   - [ ] Verify text scales properly

5. **Battery Usage**
   - [ ] Run timer for 30+ minutes with screen locked
   - [ ] Check battery drain in Settings → Battery
   - [ ] Should be minimal (<5% per hour)

**Expected Results:**
- Lock Screen shows beautiful glassmorphic timer display
- Animations are smooth (60fps)
- Status colors update correctly
- Dynamic Island works on compatible devices
- VoiceOver provides clear feedback
- Battery usage is minimal

### Android Testing (Device Required)

**Prerequisites:**
- Physical Android device running Android 8.0+ (API 26)
- Android Studio with debug build installed
- Android 12+ recommended for best experience

**Test Scenarios:**

1. **Chronometer Countdown Display**
   - [ ] Start timer
   - [ ] Lock Android device
   - [ ] Verify notification appears on Lock Screen
   - [ ] Verify chronometer counts down in real-time (MM:SS format)
   - [ ] Verify countdown updates every 1 second
   - [ ] Verify chronometer hides when timer is paused

2. **Material Design 3 Styling**
   - [ ] Check notification color (purple accent #8B5CF6)
   - [ ] Verify modern Material3 design
   - [ ] Compare with Google Clock timer notification

3. **Interactive Buttons from Lock Screen**
   - [ ] With timer running, tap "Pause" from Lock Screen notification
   - [ ] Verify timer pauses (chronometer disappears)
   - [ ] Tap "Resume" from notification
   - [ ] Verify timer resumes (chronometer reappears)
   - [ ] Tap "+5 Min" from notification
   - [ ] Verify 5 minutes added to timer
   - [ ] Tap "Stop" from notification
   - [ ] Verify timer stops and notification disappears

4. **Extend Timer Functionality**
   - [ ] Start 2-minute timer
   - [ ] Tap "+5 Min" three times
   - [ ] Verify timer now has 17 minutes (2 + 5 + 5 + 5)
   - [ ] Verify chronometer reflects new end time

5. **Smart Button Layout**
   - [ ] With timer running: Verify buttons are Pause | +5 Min | Stop
   - [ ] Pause timer: Verify buttons change to Resume | Reset | Stop
   - [ ] Test all button combinations

6. **Alarm Notification**
   - [ ] Let timer complete
   - [ ] Verify alarm notification appears
   - [ ] Verify "Stop" button works from Lock Screen
   - [ ] Verify alarm sound plays (if volume > 0)
   - [ ] Verify vibration (if enabled)

7. **Battery Usage**
   - [ ] Run timer for 30+ minutes with screen off
   - [ ] Check battery usage in Settings → Battery
   - [ ] Should show minimal drain (chronometer is system-managed)

8. **Device Compatibility**
   - [ ] Test on Android 12 device
   - [ ] Test on Android 13 device
   - [ ] Test on Android 14 device
   - [ ] Test on Android 15 device (if available)
   - [ ] Verify chronometer works on all versions

**Expected Results:**
- Chronometer counts down in real-time
- All buttons work from Lock Screen
- "+5 Min" extends timer correctly
- Material Design 3 styling matches system
- Battery usage is minimal
- Works on Android 8.0 through 15

### Cross-Platform Behavior Testing

**Test Scenarios:**

1. **Consistent Timer Logic**
   - [ ] Start identical timer on both platforms (e.g., 5-10 min range)
   - [ ] Verify both count down correctly
   - [ ] Verify pause/resume works identically
   - [ ] Verify stop works identically

2. **Hidden Mode**
   - [ ] Enable hidden mode on both platforms
   - [ ] iOS: Should show "Timer Running" without exact time
   - [ ] Android: Should show range (e.g., "5m - 10m") in notification
   - [ ] Verify mystery is preserved

3. **Repeat/Loop Mode**
   - [ ] Enable repeat on both platforms
   - [ ] Let timer complete and alarm play
   - [ ] Verify timer restarts automatically with NEW random duration
   - [ ] Verify Loop indicator shows in Lock screen display

4. **Alarm Handling**
   - [ ] Let timer alarm on both platforms
   - [ ] iOS: Verify Live Activity ends, alarm plays
   - [ ] Android: Verify alarm notification appears, sound plays
   - [ ] Verify Bluetooth media buttons can dismiss (if available)

### Regression Testing

**Critical Existing Features:**

1. **Timer Core Functionality**
   - [ ] Random duration generation works
   - [ ] Hidden mode works
   - [ ] Alarm duration works
   - [ ] Sound selection works
   - [ ] Volume control works
   - [ ] Vibration works

2. **Background Behavior**
   - [ ] App can be backgrounded/force-quit
   - [ ] Timer continues running
   - [ ] Alarm fires on time
   - [ ] State restores on app reopen

3. **In-App UI**
   - [ ] Main timer screen updates
   - [ ] Circular timer animation works
   - [ ] Settings screen works
   - [ ] All navigation works

### Known Limitations

**iOS:**
- **Button actions in Live Activity require App Intents** (iOS 16.4+)
  - Current implementation has UI ready but buttons need App Intent wiring
  - Documented in `native-ios/LIVE_ACTIVITY_IMPLEMENTATION.md`
  - Users can still control timer from app or notification

- **Dynamic Island only on iPhone 14 Pro or newer**
  - Older devices show standard Lock Screen Live Activity
  - Graceful fallback is automatic

**Android:**
- **Chronometer text-only display**
  - No circular progress ring in notification (would require custom layout)
  - Text countdown is standard Android pattern
  - Matches Google Clock design

- **Extend button fixed at +5 minutes**
  - Cannot be customized without adding preferences
  - Future enhancement: user-configurable extend amount

### Success Criteria

**Definition of Done:**

✅ **iOS:**
- [ ] Live Activity displays on Lock Screen with all timer info
- [ ] Animations are smooth and visually appealing
- [ ] Status colors change correctly (emerald, amber, rose)
- [ ] Dynamic Island works on compatible devices
- [ ] VoiceOver provides clear feedback
- [ ] Battery drain is < 5% per hour
- [ ] No crashes or memory leaks

✅ **Android:**
- [ ] Chronometer counts down in real-time
- [ ] All buttons work from Lock Screen
- [ ] "+5 Min" extends timer correctly
- [ ] Material Design 3 styling matches system
- [ ] Battery drain is < 5% per hour
- [ ] Works on Android 8.0 through 15
- [ ] No ANRs or crashes

✅ **Both Platforms:**
- [ ] Timer logic is consistent
- [ ] Hidden mode works as expected
- [ ] Repeat/loop mode works
- [ ] Alarm handling is correct
- [ ] No regressions in existing features
- [ ] Users say "wow" when they see the Lock screen display

### Bug Reporting Template

```markdown
**Platform:** iOS / Android

**Device:** [Model and OS version]

**Steps to Reproduce:**
1.
2.
3.

**Expected Behavior:**


**Actual Behavior:**


**Screenshots/Video:**


**Additional Context:**

```

### Performance Benchmarks

**iOS:**
- Live Activity updates: < 16ms per update (60fps)
- Memory usage: < 5 MB for Live Activity
- Battery drain: < 5% per hour with screen off

**Android:**
- Chronometer updates: System-managed (0% CPU overhead)
- Memory usage: < 2 MB for notification
- Battery drain: < 3% per hour with screen off

### Sign-Off

**iOS Implementation:**
- [ ] Tested by: _________________ Date: _______
- [ ] All tests passed
- [ ] No blocking bugs
- [ ] Approved for production

**Android Implementation:**
- [ ] Tested by: _________________ Date: _______
- [ ] All tests passed
- [ ] No blocking bugs
- [ ] Approved for production

---

## Need Help?

**iOS Issues:**
- Check `native-ios/LIVE_ACTIVITY_IMPLEMENTATION.md` for troubleshooting
- Verify provisioning profile includes Push Notifications capability
- Clean build folder: Product → Clean Build Folder (Cmd+Shift+K)

**Android Issues:**
- Check `native-android/NOTIFICATION_ENHANCEMENTS.md` for troubleshooting
- Check `native-android/TESTING_INSTRUCTIONS.md` for detailed scenarios
- Clean build: `./gradlew clean`
- Check logcat: `adb logcat | grep TimerService`

**General:**
- Review research documentation in parent directory
- Check CLAUDE.md for project-specific patterns
- Ask for help in team chat
