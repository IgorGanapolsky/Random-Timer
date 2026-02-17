// PhoneClaw ClawScript: Lock screen alarm visual verification
// Requires: PhoneClaw app with Accessibility service enabled, Moondream API access
//
// Run: Load this script in PhoneClaw app on the test device.
// Prereq: Device should be locked with Random Timer alarm actively firing.

delay(3000);

// Check if lock screen shows the alarm full-screen intent
var lockCheck = magicScraper(
  "Is there a full-screen alarm display or timer notification visible on the screen? Does it show Time's Up or timer alarm controls?"
);

if (lockCheck.toLowerCase().indexOf("yes") !== -1) {
  speakText("PASS: Lock screen alarm visual check");

  // Try to dismiss from lock screen
  magicClicker("the Stop button or dismiss button on the alarm display");
  delay(2000);

  // Verify alarm dismissed
  var afterDismiss = magicScraper(
    "Is the alarm still showing? Or has the screen returned to the lock screen or home screen?"
  );

  if (afterDismiss.toLowerCase().indexOf("no") !== -1 ||
      afterDismiss.toLowerCase().indexOf("lock") !== -1 ||
      afterDismiss.toLowerCase().indexOf("home") !== -1) {
    speakText("PASS: Alarm dismissed from lock screen");
  } else {
    speakText("WARN: Dismiss result unclear: " + afterDismiss);
  }
} else {
  speakText("FAIL: No alarm visible on lock screen. Got: " + lockCheck);
}
