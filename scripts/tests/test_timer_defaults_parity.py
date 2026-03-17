import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_REPOSITORY = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt"
ANDROID_RANGE_ADJUSTER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimeRangeAdjuster.kt"
ANDROID_SETUP_SCREEN = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
ANDROID_FOREGROUND_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt"
ANDROID_PAYWALL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/PaywallSheet.kt"
ANDROID_NAVIGATION = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
ANDROID_VOICE_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"
IOS_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_SETUP_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _extract_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def test_timer_defaults_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    android_repository = ANDROID_REPOSITORY.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "minSeconds = 0" in android_config
    assert "maxSeconds = 30" in android_config
    assert android_repository.count("maxSeconds = preferences[KEY_MAX_SECONDS] ?: 30") == 2
    assert re.search(r"minSeconds: Int = 0,\n\s*maxSeconds: Int = 30,", ios_models)
    assert "defaultValue: 30" in ios_models


def test_timer_limits_and_gap_rules_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    android_range_adjuster = ANDROID_RANGE_ADJUSTER.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")
    ios_setup_screen = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    assert "const val MAX_SECONDS_FREE = 300" in android_config
    assert "const val MAX_SECONDS_PRO = 3600" in android_config
    assert "public static let maxSecondsFree = 300" in ios_models
    assert "public static let maxSecondsPro = 3600" in ios_models

    assert "const val DEFAULT_MIN_SECONDS = 0" in android_range_adjuster
    assert "const val DEFAULT_MAX_SECONDS = 3600" in android_range_adjuster
    assert "const val DEFAULT_MIN_GAP_SECONDS = 1" in android_range_adjuster
    assert "static let defaultMinSecondsLimit = 0" in ios_models
    assert "static let defaultMaxSecondsLimit = 3600" in ios_models
    assert "static let defaultMinGapSeconds = 1" in ios_models
    assert "newMaxSeconds: Swift.max(1, newValue)" in ios_setup_screen


def test_sound_catalog_matches_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")
    android_sound_block = _extract_block(android_config, "enum class SoundType", "companion object")
    ios_sound_block = _extract_block(ios_models, "public enum SoundType", "// MARK: - Timer Configuration")

    android_sounds = {
        _normalize_name(name)
        for name in re.findall(r"^\s+([A-Z_]+)(?:\(|,)", android_sound_block, re.MULTILINE)
        if name not in {"FREE", "PRO"}
    }
    ios_sounds = {
        _normalize_name(name)
        for name in re.findall(r"^\s*case\s+([a-zA-Z][a-zA-Z0-9]*)$", ios_sound_block, re.MULTILINE)
    }

    assert android_sounds == ios_sounds
    assert {_normalize_name("INTENSE"), _normalize_name("GENTLE")} <= android_sounds


def test_alarm_duration_options_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    android_match = re.search(r"ALARM_DURATION_OPTIONS = listOf\(([^)]+)\)", android_config)
    ios_match = re.search(r"alarmDurationOptions = \[([^\]]+)\]", ios_models)

    assert android_match is not None
    assert ios_match is not None
    assert android_match.group(1).replace(" ", "") == ios_match.group(1).replace(" ", "")


def test_voice_callouts_are_gated_as_pro_on_both_platforms():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    android_service = ANDROID_FOREGROUND_SERVICE.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_timer_manager = (ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift").read_text(encoding="utf-8")
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "voiceCalloutsEnabled" in android_config
    assert "public let voiceCalloutsEnabled: Bool" in ios_models
    assert "checked = config.voiceCalloutsEnabled" in android_setup
    assert "config.voiceCalloutsEnabled" in ios_setup
    assert "proManager.entitlementLevel.value.isPro && state.config.voiceCalloutsEnabled" in android_service
    assert "ProManager.shared.isPro && state.config.voiceCalloutsEnabled" in ios_timer_manager


def test_hidden_debug_unlock_holds_for_8_seconds_and_unlocks_pro():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")
    android_navigation = ANDROID_NAVIGATION.read_text(encoding="utf-8")
    ios_paywall = IOS_PAYWALL.read_text(encoding="utf-8")

    assert re.search(r'Text\(\s*text = "Upgrade to Pro".*?holdForHiddenUnlock\(holdDurationMs = 8_000L', android_paywall, re.S)
    assert re.search(r'Text\("Upgrade to Pro"\).*?\.onLongPressGesture\(minimumDuration: 8\.0\)', ios_paywall, re.S)
    assert "unlockProForDebug(paywallEntryPoint)" in android_navigation
    assert "proManager.unlockProForDebug()" in ios_paywall


def test_voice_preview_actions_and_copy_match_across_mobile_platforms():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    # Both platforms must expose Voice Callouts toggle with Countdown and Commands preview buttons
    for snippet in [
        "Voice Callouts",
        "Countdown",
        "Commands",
    ]:
        assert snippet in android_setup, f"Missing '{snippet}' in Android setup screen"
        assert snippet in ios_setup, f"Missing '{snippet}' in iOS setup screen"

    assert "timed callouts during training" in android_setup.lower()
    assert "timed callouts during training" in ios_setup.lower()


def test_sound_arsenal_is_expanded_by_default_for_free_users():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    assert "var showArsenal by remember { mutableStateOf(!isPro) }" in android_setup
    assert "@State private var showArsenal = true" in ios_setup
    assert "showArsenal = true" in android_setup
    assert 'Text("Sound Arsenal")' in ios_setup
    assert 'text = "Sound Arsenal"' in android_setup


def test_voice_profile_configured_on_both_platforms():
    android_voice_service = ANDROID_VOICE_SERVICE.read_text(encoding="utf-8")
    ios_voice_service = IOS_VOICE_SERVICE.read_text(encoding="utf-8")

    # Android: preferred voice list and TTS configuration present
    assert "preferredVoiceNames" in android_voice_service
    # iOS: pitch and rate configured for tactical delivery
    assert "pitchMultiplier" in ios_voice_service
    assert "utterance.rate" in ios_voice_service
