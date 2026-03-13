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
ANDROID_PRO_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/billing/ProManager.kt"
ANDROID_VOICE_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"
IOS_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_SETUP_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"
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

    assert "if (isPro) {" in android_setup
    assert "proManager.entitlementLevel.value.isPro" in android_service
    assert "if proManager.isPro {" in ios_setup


def test_hidden_debug_unlocks_are_debug_only_and_not_wired_in_release():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")
    android_navigation = ANDROID_NAVIGATION.read_text(encoding="utf-8")
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    android_pro_manager = ANDROID_PRO_MANAGER.read_text(encoding="utf-8")
    ios_paywall = IOS_PAYWALL.read_text(encoding="utf-8")
    ios_pro_manager = IOS_PRO_MANAGER.read_text(encoding="utf-8")

    assert re.search(r'Text\(\s*text = "Upgrade to Pro".*?holdForHiddenUnlock\(holdDurationMs = 8_000L', android_paywall, re.S)
    assert "onDebugUnlock: (() -> Unit)? = null" in android_paywall
    assert "onSecretUnlock: (() -> Unit)? = null" in android_setup
    assert "if (onSecretUnlock != null)" in android_setup
    assert "if (ProManager.canUseDebugUnlock(BuildConfig.DEBUG))" in android_navigation
    assert "isDebugBuild: Boolean = BuildConfig.DEBUG" in android_pro_manager
    assert "#if DEBUG" in ios_paywall
    assert "#if DEBUG" in ios_pro_manager


def test_android_hidden_debug_unlock_uses_full_width_hold_target():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")

    assert re.search(
        r'Text\(\s*text = "Upgrade to Pro".*?Modifier\s*\.\s*fillMaxWidth\(\)\s*\.\s*padding\(vertical = 8\.dp\)\s*\.\s*holdForHiddenUnlock',
        android_paywall,
        re.S,
    )


def test_subscription_legal_links_are_present_in_paywall_and_metadata():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")
    ios_paywall = IOS_PAYWALL.read_text(encoding="utf-8")
    ios_description = (ROOT / "native-ios/fastlane/metadata/en-US/description.txt").read_text(encoding="utf-8")

    assert "Terms of Use" in android_paywall
    assert "Privacy Policy" in android_paywall
    assert 'Link("Terms of Use"' in ios_paywall
    assert 'Link("Privacy Policy"' in ios_paywall
    assert "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/" in ios_description


def test_voice_preview_actions_and_copy_match_across_mobile_platforms():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    for snippet in [
        "Voice Callouts",
        "Countdown",
        "Focus",
    ]:
        assert snippet in android_setup, f"Missing '{snippet}' in Android setup screen"
        assert snippet in ios_setup, f"Missing '{snippet}' in iOS setup screen"


def test_voice_runtime_callouts_are_elapsed_only_on_both_platforms():
    android_voice_service = ANDROID_VOICE_SERVICE.read_text(encoding="utf-8")
    ios_voice_service = IOS_VOICE_SERVICE.read_text(encoding="utf-8")

    assert "runtimeVoiceCueForElapsedSecond" in android_voice_service
    assert "shouldFireCommandCue" not in android_voice_service
    assert "Random.nextInt(" not in android_voice_service
    assert "PREVIEW_COMMAND_CUE" in android_voice_service

    assert "runtimeVoiceCue(for elapsedSeconds:" in ios_voice_service
    assert "shouldFireCommandCue" not in ios_voice_service
    assert "secureRandomInt" not in ios_voice_service
    assert "previewCommandVoiceCue" in ios_voice_service


def test_voice_profile_configured_on_both_platforms():
    android_voice_service = ANDROID_VOICE_SERVICE.read_text(encoding="utf-8")
    ios_voice_service = IOS_VOICE_SERVICE.read_text(encoding="utf-8")

    assert "preferredVoiceNames" in android_voice_service
    assert "voiceResIdOrFallback" in android_voice_service
    assert "TextToSpeech" not in android_voice_service
    assert "voiceFilenameOrFallback" in ios_voice_service
    assert "AVSpeechSynthesizer" not in ios_voice_service
