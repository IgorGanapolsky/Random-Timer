from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

VOICE_CONTRACT = ROOT / "content/pro_audio/voice_personas.json"
IOS_AUDIO_DIR = ROOT / "native-ios/RandomTimer/Resources/Audio"
ANDROID_RAW_DIR = ROOT / "native-android/app/src/main/res/raw"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
ANDROID_VIEWMODEL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt"
ANDROID_PREVIEW_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/SoundPreviewManager.kt"
ANDROID_PREVIEW_IMPL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/SoundPreviewManagerImpl.kt"
ANDROID_VOICE_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
VOICE_VERIFY_SCRIPT = ROOT / "scripts/verify_elevenlabs_voices.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contract() -> dict:
    return json.loads(VOICE_CONTRACT.read_text(encoding="utf-8"))


def test_voice_contract_tracks_real_elevenlabs_personas() -> None:
    contract = _contract()

    assert contract["schemaVersion"] == 1
    assert contract["provider"] == "elevenlabs"
    assert contract["male"]["modelId"] == "eleven_multilingual_v2"
    assert contract["male"]["voiceId"] == "DGzg6RaUqxGRTHSBjfgF"
    assert contract["male"]["probeText"] == "Stay sharp."
    assert contract["female"]["primaryVoice"]["voiceName"] == "Domi"
    assert contract["female"]["primaryVoice"]["voiceId"] == "AZnzlk1XvdvUeBnXmlld"
    assert contract["female"]["primaryVoice"]["probeText"] == "Move with purpose."
    assert {voice["voiceName"] for voice in contract["female"]["fallbackVoices"]} == {"Anvi"}
    assert {voice["probeText"] for voice in contract["female"]["fallbackVoices"]} == {"Stay in the fight."}


def test_female_preview_samples_exist_on_both_platforms() -> None:
    contract = _contract()
    sample_filenames = {sample["filename"] for sample in contract["female"]["previewSamples"]}

    ios_files = {path.stem for path in IOS_AUDIO_DIR.glob("female_preview_*.mp3")}
    android_files = {path.stem for path in ANDROID_RAW_DIR.glob("female_preview_*.mp3")}

    assert ios_files == sample_filenames
    assert android_files == sample_filenames


def test_ios_free_preview_keeps_voice_selector_visible() -> None:
    setup = _read(IOS_SETUP)

    assert 'Text("PREVIEW")' in setup
    assert 'if config.voiceEnabled || !proManager.isPro {' in setup
    assert 'Text("Female").tag(VoiceGender.female)' in setup


def test_preview_calls_thread_selected_gender_on_both_platforms() -> None:
    ios_timer_manager = _read(IOS_TIMER_MANAGER)
    ios_voice_service = _read(IOS_VOICE_SERVICE)
    android_viewmodel = _read(ANDROID_VIEWMODEL)
    android_preview_manager = _read(ANDROID_PREVIEW_MANAGER)
    android_preview_impl = _read(ANDROID_PREVIEW_IMPL)

    assert "previewCommandCue(gender: config.voiceGender)" in ios_timer_manager
    assert "func previewCommandCue(gender: VoiceGender" in ios_voice_service
    assert "soundPreviewManager.previewCommandCue(config.value.voiceGender)" in android_viewmodel
    assert "fun previewCommandCue(gender: VoiceGender)" in android_preview_manager
    assert "voiceCalloutManager.previewCommandCue(gender)" in android_preview_impl


def test_android_voice_playback_stays_off_system_tts() -> None:
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)

    assert "TextToSpeech" not in android_voice_manager
    assert "SYSTEM_SYNTHESIZED" not in android_voice_manager
    assert "female_preview_move_with_a_purpose" in android_voice_manager


def test_ci_runs_static_and_live_voice_regression_guards() -> None:
    workflow = _read(CI_WORKFLOW)
    verify_script = _read(VOICE_VERIFY_SCRIPT)

    assert "Voice Provider Smoke" in workflow
    assert "scripts/verify_elevenlabs_voices.py" in workflow
    assert "ELEVENLABS_API_KEY" in workflow
    assert "Decide live smoke execution" in workflow
    assert 'steps.gate.outputs.run_live_smoke == \'true\'' in workflow
    assert "Record controlled skip" in workflow
    assert "content/pro_audio/voice_personas.json" in verify_script
    assert "/v1/text-to-speech/" in verify_script
    assert "verifiedProbes" in verify_script
