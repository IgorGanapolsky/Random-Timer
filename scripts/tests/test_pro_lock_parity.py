"""Regression tests: Pro locks, audio quality, icon consistency, feature parity.

Every test here exists because a specific bug reached production.
Do not remove tests without CEO approval.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"

PRO_FEATURES = ["extended_range", "voice_callouts", "pro_sounds"]


class ProLockParityTest(unittest.TestCase):

    def test_android_has_pro_lock_for_all_features(self):
        src = ANDROID_SETUP.read_text()
        for feature in PRO_FEATURES:
            with self.subTest(feature=feature):
                self.assertIn(feature, src, f"Android missing feature gate for '{feature}'")

    def test_ios_has_pro_lock_for_all_features(self):
        src = IOS_SETUP.read_text()
        self.assertIn("presentPaywall", src, "iOS missing paywall presentation")
        self.assertIn("soundGate", src, "iOS missing soundGate paywall entry")
        self.assertIn("rangeGate", src, "iOS missing rangeGate paywall entry")

    def test_android_lock_icons_not_gated_behind_first_timer(self):
        src = ANDROID_SETUP.read_text()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and ("lock" in line.lower() or "\uD83D\uDD12" in line):
                self.fail(f"Android line {i+1}: lock gated behind hasCompletedFirstTimer")

    def test_ios_lock_icons_not_gated_behind_first_timer(self):
        src = IOS_SETUP.read_text()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and ("lock" in line.lower() or "\uD83D\uDD12" in line):
                self.fail(f"iOS line {i+1}: lock gated behind hasCompletedFirstTimer")

    def test_ios_paywall_not_gated_behind_first_timer(self):
        src = IOS_SETUP.read_text()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "hasCompletedFirstTimer" in line and i + 1 < len(lines) and "presentPaywall" in lines[i + 1]:
                self.fail(f"iOS line {i+1}: paywall gated behind hasCompletedFirstTimer")

    def test_both_platforms_have_sound_arsenal_section(self):
        self.assertIn("Sound Arsenal", ANDROID_SETUP.read_text())
        self.assertIn("SOUND ARSENAL", IOS_SETUP.read_text())


class AudioRegressionTest(unittest.TestCase):

    def test_female_voice_is_ivanna_not_domi(self):
        persona = ROOT / "content/pro_audio/voice_personas.json"
        data = json.loads(persona.read_text())
        name = data["female"]["primaryVoice"]["voiceName"]
        self.assertEqual(name, "Sarah", f"Female voice must be Sarah, not {name}")

    def test_female_voice_uses_turbo_model(self):
        persona = ROOT / "content/pro_audio/voice_personas.json"
        data = json.loads(persona.read_text())
        model = data["female"]["modelId"]
        self.assertIn("turbo", model, f"Female model must be turbo, not {model}")

    def test_gentle_icon_not_lightning_bolt_android(self):
        src = ANDROID_SETUP.read_text()
        self.assertNotIn("\u26A1 Gentle", src, "Android Gentle icon must not be lightning bolt")
        self.assertNotIn(
            "\\uD83D\\uDD25 Gentle",
            src,
            "Android Gentle must not reuse the fire-alarm emoji escape",
        )
        self.assertIn(
            "\\uD83D\\uDCA7 Gentle",
            src,
            "Android Gentle must use water-drop emoji escape (semantic iconography)",
        )

    def test_gentle_icon_not_lightning_bolt_ios(self):
        src = IOS_SETUP.read_text()
        self.assertNotIn('"bolt.fill"', src, "iOS Gentle icon must not be bolt.fill")
        gentle_idx = src.find('label: "Gentle"')
        self.assertGreaterEqual(gentle_idx, 0, "Gentle sound row must exist")
        window = src[gentle_idx : gentle_idx + 220]
        self.assertIn(
            'systemImage: "drop.fill"',
            window,
            "iOS Gentle must use drop.fill (distinct from flame.fill / bolt)",
        )

    def test_alarm_sound_not_ai_generated(self):
        alarm = ROOT / "native-android/app/src/main/res/raw/alarm.mp3"
        size = alarm.stat().st_size
        self.assertGreater(size, 100000, f"alarm.mp3 is {size} bytes — restore original (271KB)")


if __name__ == "__main__":
    unittest.main()
