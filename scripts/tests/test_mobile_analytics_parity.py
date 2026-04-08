import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_ANALYTICS = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/analytics/AnalyticsService.kt"
ANDROID_NAV = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
IOS_ANALYTICS = ROOT / "native-ios/RandomTimer/Sources/Services/AnalyticsService.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_SETUP_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_ACTIVE_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift"
ANDROID_TIMER_VM = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt"
ANDROID_TIMER_SERVICE = (
    ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt"
)


def _extract_block(source: str, marker: str) -> str:
    pattern = re.compile(rf"{re.escape(marker)}\s*\{{(?P<body>.*?)\n\}}", re.S)
    match = pattern.search(source)
    if not match:
        raise AssertionError(f"Could not find block: {marker}")
    return match.group("body")


def _extract_string_constants(block: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, block))


class MobileAnalyticsParityTests(unittest.TestCase):
    def test_event_names_match_between_ios_and_android(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")

        android_events = _extract_string_constants(
            _extract_block(android_source, "object AnalyticsEvents"),
            r'const val \w+\s*=\s*"([^"]+)"',
        )
        ios_events = _extract_string_constants(
            _extract_block(ios_source, "enum AnalyticsEvents"),
            r'static let \w+\s*=\s*"([^"]+)"',
        )
        self.assertEqual(android_events, ios_events)

    def test_screen_names_match_between_ios_and_android(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")

        android_screens = _extract_string_constants(
            _extract_block(android_source, "object AnalyticsScreens"),
            r'const val \w+\s*=\s*"([^"]+)"',
        )
        ios_screens = _extract_string_constants(
            _extract_block(ios_source, "enum AnalyticsScreens"),
            r'static let \w+\s*=\s*"([^"]+)"',
        )
        self.assertEqual(android_screens, ios_screens)

    def test_ios_screens_emit_screen_view_events(self):
        setup_source = IOS_SETUP_SCREEN.read_text(encoding="utf-8")
        active_source = IOS_ACTIVE_SCREEN.read_text(encoding="utf-8")

        self.assertIn("AnalyticsService.shared.screen(AnalyticsScreens.timerSetup)", setup_source)
        self.assertIn("AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)", active_source)

    def test_android_navigation_emits_screen_view_events(self):
        source = ANDROID_NAV.read_text(encoding="utf-8")
        self.assertIn("viewModel.trackScreen(AnalyticsScreens.TIMER_SETUP)", source)
        self.assertIn("viewModel.trackScreen(AnalyticsScreens.ACTIVE_TIMER)", source)

    def test_result_property_is_defined_on_both_platforms(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
        self.assertIn('const val RESULT = "result"', android_source)
        self.assertIn('static let result = "result"', ios_source)

    def test_distribution_channel_property_matches_between_platforms(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
        self.assertIn('const val DISTRIBUTION_CHANNEL = "distribution_channel"', android_source)
        self.assertIn('static let distributionChannel = "distribution_channel"', ios_source)

    def test_lifecycle_autocapture_disabled_on_both_platforms(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
        self.assertIn("captureApplicationLifecycleEvents = false", android_source)
        self.assertIn("config.captureApplicationLifecycleEvents = false", ios_source)

    def test_manual_lifecycle_events_tracked_on_initialize(self):
        android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
        ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
        self.assertIn("trackApplicationLifecycleEvents()", android_source)
        self.assertIn("trackApplicationLifecycleEvents()", ios_source)
        self.assertIn('const val APPLICATION_INSTALLED = "Application Installed"', android_source)
        self.assertIn('const val APPLICATION_OPENED = "Application Opened"', android_source)
        self.assertIn('static let applicationInstalled = "Application Installed"', ios_source)
        self.assertIn('static let applicationOpened = "Application Opened"', ios_source)

    def test_timer_completed_emission_site_counts_match_documentation(self):
        """Keep in sync with docs/POSTHOG_ANALYTICS.md § timer_completed emission paths."""
        ios_tm = IOS_TIMER_MANAGER.read_text(encoding="utf-8")
        ios_hits = ios_tm.count(
            "AnalyticsService.shared.track(AnalyticsEvents.timerCompleted",
        )
        self.assertEqual(ios_hits, 6)

        vm = ANDROID_TIMER_VM.read_text(encoding="utf-8")
        svc = ANDROID_TIMER_SERVICE.read_text(encoding="utf-8")
        kt_pattern = re.compile(
            r"analyticsService\.track\(\s*\n\s*AnalyticsEvents\.TIMER_COMPLETED",
        )
        self.assertEqual(len(kt_pattern.findall(vm)), 1)
        self.assertEqual(len(kt_pattern.findall(svc)), 1)


if __name__ == "__main__":
    unittest.main()
