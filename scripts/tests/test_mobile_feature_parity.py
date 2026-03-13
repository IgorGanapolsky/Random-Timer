from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ANDROID_TIMER_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_PAYWALL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/PaywallSheet.kt"
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
ANDROID_VIEWMODEL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt"
ANDROID_SOUND_PREVIEW = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/SoundPreviewManager.kt"
ANDROID_SOUND_PREVIEW_IMPL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/SoundPreviewManagerImpl.kt"
ANDROID_NAV = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"

IOS_TIMER_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_default_timer_range_is_zero_to_thirty_on_both_platforms():
    android_source = _read(ANDROID_TIMER_CONFIG)
    ios_source = _read(IOS_TIMER_MODELS)

    assert re.search(r"minSeconds\s*=\s*0", android_source)
    assert re.search(r"maxSeconds\s*=\s*30", android_source)
    assert re.search(r"minSeconds:\s*Int\s*=\s*0", ios_source)
    assert re.search(r"maxSeconds:\s*Int\s*=\s*30", ios_source)


def test_time_range_limits_and_gap_match_between_platforms():
    android_source = _read(ANDROID_TIMER_CONFIG)
    ios_source = _read(IOS_TIMER_MODELS)

    assert "MAX_SECONDS_PRO = 3600" in android_source
    assert "maxSecondsPro = 3600" in ios_source
    assert "defaultMaxSecondsLimit = 3600" in ios_source
    assert "defaultMinGapSeconds = 1" in ios_source
    assert "Swift.max(1, newValue)" in _read(IOS_SETUP)


def test_paywall_hidden_unlock_is_on_title_and_unlocks_pro_not_elite():
    android_source = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)
    ios_pro_manager = _read(IOS_PRO_MANAGER)

    assert re.search(
        r'Text\(\s*text = "Upgrade to Pro".*?holdForHiddenUnlock',
        android_source,
        re.S,
    )
    assert not re.search(
        r'PrimaryButton\([\s\S]*?holdForHiddenUnlock',
        android_source,
        re.S,
    )

    assert re.search(
        r'Text\("Upgrade to Pro"\)[\s\S]*?onLongPressGesture\(minimumDuration:\s*8\.0\)',
        ios_paywall,
        re.S,
    )
    assert "unlockProForDebug()" in ios_paywall
    assert "unlockEliteForDebug()" not in ios_paywall
    assert "func unlockEliteForDebug()" not in ios_pro_manager


def test_voice_callouts_present_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)
    android_timer_config = _read(ANDROID_TIMER_CONFIG)
    ios_timer_models = _read(IOS_TIMER_MODELS)

    for source in (android_setup, ios_setup):
        assert "Voice Callouts" in source
        assert "Countdown" in source
        assert "Focus" in source

    assert "voiceCalloutsEnabled" in android_timer_config
    assert "voiceCalloutsEnabled" in ios_timer_models


def test_voice_callouts_use_toggle_when_pro_and_runtime_respects_setting():
    android_setup = _read(ANDROID_SETUP)
    android_service = _read(ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt")
    ios_setup = _read(IOS_SETUP)
    ios_timer_manager = _read(IOS_TIMER_MANAGER)

    assert "checked = config.voiceCalloutsEnabled" in android_setup
    assert "updateConfig(voiceCalloutsEnabled = enabled)" in android_setup
    assert "proManager.entitlementLevel.value.isPro && state.config.voiceCalloutsEnabled" in android_service

    assert "config.voiceCalloutsEnabled" in ios_setup
    assert "updateConfig(voiceCalloutsEnabled: enabled)" in ios_setup
    assert "ProManager.shared.isPro && state.config.voiceCalloutsEnabled" in ios_timer_manager


def test_voice_preview_supports_command_cues_on_both_platforms():
    android_preview = _read(ANDROID_SOUND_PREVIEW)
    android_preview_impl = _read(ANDROID_SOUND_PREVIEW_IMPL)
    android_viewmodel = _read(ANDROID_VIEWMODEL)
    android_nav = _read(ANDROID_NAV)
    ios_timer_manager = _read(IOS_TIMER_MANAGER)
    ios_voice_service = _read(IOS_VOICE_SERVICE)

    assert "fun previewCommandCue()" in android_preview
    assert "previewCommandCue()" in android_preview_impl
    assert "fun previewCommandCue()" in android_viewmodel
    assert "onCommandCuePreview = viewModel::previewCommandCue" in android_nav

    assert "func previewCommandCue()" in ios_timer_manager
    assert "func previewCommandCue()" in ios_voice_service
    assert "func previewCountdownCue()" in ios_voice_service
