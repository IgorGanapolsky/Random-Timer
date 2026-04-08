"""Regression test: every Pro feature must show a consistent lock indicator on both platforms.

If this test fails, a Pro lock was removed, hidden behind a condition,
or styled differently from the standard pattern.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"

# Pro features that MUST have lock indicators on both platforms
PRO_FEATURES = [
    "extended_range",   # Timer Range PRO: 1H
    "voice_callouts",   # Voice Callouts PRO lock
    "pro_sounds",       # Sound Arsenal PRO lock
]


class ProLockParityTest(unittest.TestCase):

    def test_android_has_pro_lock_for_all_features(self):
        src = ANDROID_SETUP.read_text()
        for feature in PRO_FEATURES:
            with self.subTest(feature=feature):
                self.assertIn(
                    feature,
                    src,
                    f"Android setup screen missing feature gate for '{feature}'",
                )

    def test_ios_has_pro_lock_for_all_features(self):
        src = IOS_SETUP.read_text()
        # iOS uses presentPaywall with entryPoint
        self.assertIn("presentPaywall", src, "iOS missing paywall presentation")
        self.assertIn("soundGate", src, "iOS missing soundGate paywall entry")
        self.assertIn("rangeGate", src, "iOS missing rangeGate paywall entry")

    def test_android_lock_icons_not_gated_behind_first_timer(self):
        src = ANDROID_SETUP.read_text()
        # Lock indicators should never be hidden behind hasCompletedFirstTimer
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and ("lock" in line.lower() or "🔒" in line):
                self.fail(
                    f"Android line {i+1}: lock icon gated behind hasCompletedFirstTimer — "
                    f"free users must always see Pro locks"
                )

    def test_ios_lock_icons_not_gated_behind_first_timer(self):
        src = IOS_SETUP.read_text()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and ("lock" in line.lower() or "🔒" in line):
                self.fail(
                    f"iOS line {i+1}: lock icon gated behind hasCompletedFirstTimer — "
                    f"free users must always see Pro locks"
                )

    def test_ios_paywall_not_gated_behind_first_timer(self):
        src = IOS_SETUP.read_text()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and "presentPaywall" in lines[i+1] if i+1 < len(lines) else False:
                self.fail(
                    f"iOS line {i+1}: paywall gated behind hasCompletedFirstTimer — "
                    f"free users must always be able to upgrade"
                )

    def test_both_platforms_have_sound_arsenal_section(self):
        android_src = ANDROID_SETUP.read_text()
        ios_src = IOS_SETUP.read_text()
        self.assertIn("Sound Arsenal", android_src, "Android missing Sound Arsenal section")
        self.assertIn("SOUND ARSENAL", ios_src, "iOS missing Sound Arsenal section")


if __name__ == "__main__":
    unittest.main()
