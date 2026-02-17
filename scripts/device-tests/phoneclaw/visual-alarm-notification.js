// PhoneClaw ClawScript: Visual verification of alarm notification
// Requires: PhoneClaw app with Accessibility service enabled, Moondream API access
//
// Run: Load this script in PhoneClaw app on the test device.
// Prereq: Random Timer alarm must be actively firing before running.

delay(3000);

// Check if alarm notification is visually present
var notifCheck = magicScraper(
  "Is there a notification with the text Time's Up that has Silence and Stop buttons?"
);

if (notifCheck.toLowerCase().indexOf("yes") !== -1) {
  speakText("PASS: Alarm notification visual check");

  // Tap the Silence button via vision
  magicClicker("the Silence button on the Timer notification");
  delay(2000);

  // Verify notification updated after silence
  var afterSilence = magicScraper(
    "Is the alarm notification still showing the Time's Up text? Has the notification changed?"
  );
  speakText("After silence: " + afterSilence);

  // Check that sound stopped (screen should show Timer Complete state)
  var screenState = magicScraper(
    "Does the screen show a timer that says Complete or Timer complete?"
  );
  if (screenState.toLowerCase().indexOf("yes") !== -1) {
    speakText("PASS: Timer in complete state after silence");
  } else {
    speakText("WARN: Could not confirm complete state: " + screenState);
  }
} else {
  speakText("FAIL: Alarm notification not visible. Got: " + notifCheck);
}
