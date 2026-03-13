import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_PAYWALL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/PaywallSheet.kt"
ANDROID_NAVIGATION = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
ANDROID_PRO_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/billing/ProManager.kt"
IOS_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _extract_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def test_minimum_defaults_are_non_negative_on_both_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "minSeconds = 0" in android_config
    assert re.search(r"minSeconds\s*:\s*Int\s*=\s*0", ios_models)


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


def test_hidden_debug_unlocks_are_debug_only_and_not_wired_in_release():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")
    android_navigation = ANDROID_NAVIGATION.read_text(encoding="utf-8")
    android_pro_manager = ANDROID_PRO_MANAGER.read_text(encoding="utf-8")
    ios_paywall = IOS_PAYWALL.read_text(encoding="utf-8")
    ios_pro_manager = IOS_PRO_MANAGER.read_text(encoding="utf-8")

    assert re.search(r'Text\(\s*text = "Upgrade to Pro".*?holdForHiddenUnlock\(holdDurationMs = 8_000L', android_paywall, re.S)
    assert "onDebugUnlock: (() -> Unit)? = null" in android_paywall
    assert "if (ProManager.canUseDebugUnlock(BuildConfig.DEBUG))" in android_navigation
    assert "isDebugBuild: Boolean = BuildConfig.DEBUG" in android_pro_manager
    assert "#if DEBUG" in ios_paywall
    assert re.search(r"func unlockProForDebug\(\)\s*\{\s*#if DEBUG", ios_pro_manager, re.S)
    assert re.search(r"func unlockEliteForDebug\(\)\s*\{\s*#if DEBUG", ios_pro_manager, re.S)


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
