import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_ANALYTICS = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/analytics/AnalyticsService.kt"
ANDROID_NAV = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
IOS_ANALYTICS = ROOT / "native-ios/RandomTimer/Sources/Services/AnalyticsService.swift"
IOS_SETUP_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_ACTIVE_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift"


def _extract_block(source: str, marker: str) -> str:
    pattern = re.compile(rf"{re.escape(marker)}\s*\{{(?P<body>.*?)\n\}}", re.S)
    match = pattern.search(source)
    if not match:
        raise AssertionError(f"Could not find block: {marker}")
    return match.group("body")


def _extract_string_constants(block: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, block))


def test_event_names_match_between_ios_and_android() -> None:
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
    assert android_events == ios_events


def test_screen_names_match_between_ios_and_android() -> None:
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
    assert android_screens == ios_screens


def test_ios_screens_emit_screen_view_events() -> None:
    setup_source = IOS_SETUP_SCREEN.read_text(encoding="utf-8")
    active_source = IOS_ACTIVE_SCREEN.read_text(encoding="utf-8")

    assert "AnalyticsService.shared.screen(AnalyticsScreens.timerSetup)" in setup_source
    assert "AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)" in active_source


def test_android_navigation_emits_screen_view_events() -> None:
    source = ANDROID_NAV.read_text(encoding="utf-8")
    assert "viewModel.trackScreen(AnalyticsScreens.TIMER_SETUP)" in source
    assert "viewModel.trackScreen(AnalyticsScreens.ACTIVE_TIMER)" in source


def test_result_property_is_defined_on_both_platforms() -> None:
    android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
    ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
    assert 'const val RESULT = "result"' in android_source
    assert 'static let result = "result"' in ios_source


def test_lifecycle_autocapture_disabled_on_both_platforms() -> None:
    android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
    ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
    assert "captureApplicationLifecycleEvents = false" in android_source
    assert "config.captureApplicationLifecycleEvents = false" in ios_source


def test_manual_lifecycle_events_tracked_on_initialize() -> None:
    android_source = ANDROID_ANALYTICS.read_text(encoding="utf-8")
    ios_source = IOS_ANALYTICS.read_text(encoding="utf-8")
    assert "trackApplicationLifecycleEvents()" in android_source
    assert "trackApplicationLifecycleEvents()" in ios_source
    assert 'const val APPLICATION_INSTALLED = "Application Installed"' in android_source
    assert 'const val APPLICATION_OPENED = "Application Opened"' in android_source
    assert 'static let applicationInstalled = "Application Installed"' in ios_source
    assert 'static let applicationOpened = "Application Opened"' in ios_source
