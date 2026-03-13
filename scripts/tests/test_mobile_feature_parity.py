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
ANDROID_PRO_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/billing/ProManager.kt"

IOS_TIMER_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_store_range_limits_are_defined_on_both_platforms():
    android_source = _read(ANDROID_TIMER_CONFIG)
    ios_source = _read(IOS_TIMER_MODELS)

    assert "MAX_SECONDS_PRO = 3600" in android_source
    assert "maxSecondsPro = 3600" in ios_source
    assert re.search(r"minSeconds\s*:\s*Int\s*=\s*0", ios_source)
    assert re.search(r"minSeconds\s*=\s*0", android_source)


def test_release_builds_gate_hidden_unlocks_and_show_required_legal_links():
    android_source = _read(ANDROID_PAYWALL)
    android_setup = _read(ANDROID_SETUP)
    android_nav = _read(ANDROID_NAV)
    android_pro_manager = _read(ANDROID_PRO_MANAGER)
    ios_paywall = _read(IOS_PAYWALL)
    ios_pro_manager = _read(IOS_PRO_MANAGER)

    assert re.search(r'Text\(\s*text = "Upgrade to Pro".*?holdForHiddenUnlock', android_source, re.S)
    assert "onDebugUnlock: (() -> Unit)? = null" in android_source
    assert "onSecretUnlock: (() -> Unit)? = null" in android_setup
    assert "if (onSecretUnlock != null)" in android_setup
    assert "if (ProManager.canUseDebugUnlock(BuildConfig.DEBUG))" in android_nav
    assert "isDebugBuild: Boolean = BuildConfig.DEBUG" in android_pro_manager
    assert "Terms of Use" in android_source
    assert "Privacy Policy" in android_source

    assert "#if DEBUG" in ios_paywall
    assert 'Link("Terms of Use"' in ios_paywall
    assert 'Link("Privacy Policy"' in ios_paywall
    assert re.search(r"func unlockProForDebug\(\)\s*\{\s*#if DEBUG", ios_pro_manager, re.S)
    assert re.search(r"func unlockEliteForDebug\(\)\s*\{\s*#if DEBUG", ios_pro_manager, re.S)
    assert "unlockEliteForDebug()" not in ios_paywall


def test_voice_callouts_present_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)

    for source in (android_setup, ios_setup):
        assert "Voice Callouts" in source


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
