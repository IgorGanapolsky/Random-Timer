from __future__ import annotations

import json
import hashlib
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
RUNTIME_LATEST = ROOT / "content/pro_audio/runtime/latest.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(source: str, start_marker: str, end_marker: str) -> str:
    return source.split(start_marker, 1)[1].split(end_marker, 1)[0]


def _contract() -> dict:
    return json.loads(VOICE_CONTRACT.read_text(encoding="utf-8"))


def _runtime_voice_asset_map() -> dict[str, Path]:
    manifest = json.loads(RUNTIME_LATEST.read_text(encoding="utf-8"))
    voice_assets: dict[str, Path] = {}
    for asset in manifest["assets"]:
        if asset["kind"] != "voice":
            continue
        voice_assets[asset["filename"]] = ROOT / "content/pro_audio/runtime" / asset["relativePath"]
    return voice_assets


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_voice_contract_tracks_real_elevenlabs_personas() -> None:
    contract = _contract()

    assert contract["schemaVersion"] == 1
    assert contract["provider"] == "elevenlabs"
    assert contract["male"]["modelId"] == "eleven_multilingual_v2"
    assert contract["male"]["voiceId"] == "DGzg6RaUqxGRTHSBjfgF"
    assert contract["male"]["probeText"] == "Stay sharp."
    assert contract["female"]["persona"] == "Young HIIT Coach / Drill Sergeant"
    assert contract["female"]["modelId"] == "eleven_turbo_v2"
    assert contract["female"]["primaryVoice"]["voiceName"] == "Sarah"
    assert contract["female"]["primaryVoice"]["voiceId"] == "EXAVITQu4vr4xnSDxMaL"
    assert contract["female"]["primaryVoice"]["probeText"] == "Move with purpose."
    assert {voice["voiceName"] for voice in contract["female"]["fallbackVoices"]} == {"Anvi"}
    assert {voice["probeText"] for voice in contract["female"]["fallbackVoices"]} == {"Stay in the fight."}
    assert contract["female"]["voiceSettings"] == {
        "stability": 0.65,
        "similarity_boost": 0.85,
        "style": 0.55,
        "use_speaker_boost": True,
    }
    assert contract["female"]["generationConfig"] == {"speed": 0.75}


def test_female_preview_samples_exist_on_both_platforms() -> None:
    contract = _contract()
    preview_contract = contract["female"]["previewSamples"]
    android_command_filenames = set(preview_contract["androidCommandFilenames"])
    android_elapsed_filename = preview_contract["androidElapsedFilename"]
    ios_command_filenames = set(preview_contract["iosCommandFilenames"])
    ios_elapsed_filename = preview_contract["iosElapsedFilename"]

    android_files = {path.stem for path in ANDROID_RAW_DIR.glob("female_*.mp3")}
    ios_files = {
        str(path.relative_to(IOS_AUDIO_DIR).with_suffix(""))
        for path in IOS_AUDIO_DIR.rglob("female/*.mp3")
    }

    assert android_command_filenames.issubset(android_files)
    assert android_elapsed_filename in android_files
    assert ios_command_filenames.issubset(ios_files)
    assert ios_elapsed_filename in ios_files


def test_ios_female_catalog_metadata_matches_contract() -> None:
    contract = _contract()["female"]
    catalog = json.loads((IOS_AUDIO_DIR / "female" / "voice_callouts.json").read_text(encoding="utf-8"))

    assert catalog["voiceGender"] == "female"
    assert catalog["voiceId"] == contract["primaryVoice"]["voiceId"]
    assert catalog["voiceName"] == contract["primaryVoice"]["voiceName"]
    assert catalog["modelId"] == contract["modelId"]


def test_android_male_preview_samples_exist() -> None:
    contract = _contract()
    preview_contract = contract["male"]["previewSamples"]
    android_command_filenames = set(preview_contract["androidCommandFilenames"])
    android_elapsed_filename = preview_contract["androidElapsedFilename"]
    android_files = {path.stem for path in ANDROID_RAW_DIR.glob("cmd_*.mp3")}

    assert android_command_filenames.issubset(android_files)
    assert (ANDROID_RAW_DIR / f"{android_elapsed_filename}.mp3").exists()


def test_male_preview_samples_match_canonical_marine_runtime_pack() -> None:
    contract = _contract()
    preview_contract = contract["male"]["previewSamples"]
    runtime_assets = _runtime_voice_asset_map()
    male_preview_filenames = set(preview_contract["iosCommandFilenames"]) | {preview_contract["iosElapsedFilename"]}

    for filename in male_preview_filenames:
        runtime_path = runtime_assets[filename]
        assert runtime_path.exists(), f"Missing canonical runtime asset for {filename}"
        assert _sha256(IOS_AUDIO_DIR / f"{filename}.mp3") == _sha256(runtime_path)
        assert _sha256(ANDROID_RAW_DIR / f"{filename}.mp3") == _sha256(runtime_path)


def test_ios_free_preview_keeps_voice_selector_visible() -> None:
    setup = _read(IOS_SETUP)

    assert 'Text("PREVIEW")' in setup
    assert 'if config.voiceEnabled || !proManager.isPro {' in setup
    assert 'Text("Female").tag(VoiceGender.female)' in setup


def test_android_free_preview_keeps_voice_selector_visible() -> None:
    setup = _read(ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt")

    assert 'text = "PREVIEW"' in setup
    assert "Time checks and command cues that keep you sharp under pressure" in setup
    assert "VoiceGender.entries.forEach" in setup
    assert "VoiceGender.MALE" in setup
    assert "if (config.voiceEnabled || !isPro)" in setup
    assert "onCommandCuePreview(config.voiceGender)" in setup
    assert "if (config.voiceEnabled) {" not in setup
    assert setup.index('text = "PREVIEW"') < setup.index("VoiceGender.entries.forEach")


def test_preview_calls_thread_selected_gender_on_both_platforms() -> None:
    ios_timer_manager = _read(IOS_TIMER_MANAGER)
    ios_voice_service = _read(IOS_VOICE_SERVICE)
    android_setup = _read(ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt")
    android_viewmodel = _read(ANDROID_VIEWMODEL)
    android_preview_manager = _read(ANDROID_PREVIEW_MANAGER)
    android_preview_impl = _read(ANDROID_PREVIEW_IMPL)

    assert "previewCommandCue(gender: config.voiceGender)" in ios_timer_manager
    assert "func previewCommandCue(gender: VoiceGender" in ios_voice_service
    assert "onCommandCuePreview(config.voiceGender)" in android_setup
    assert "fun previewCommandCue(gender: VoiceGender)" in android_viewmodel
    assert "soundPreviewManager.previewCommandCue(gender)" in android_viewmodel
    assert "fun previewCommandCue(gender: VoiceGender)" in android_preview_manager
    assert "voiceCalloutManager.previewCommandCue(gender)" in android_preview_impl


def test_android_voice_playback_stays_off_system_tts() -> None:
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)
    ios_voice_service = _read(IOS_VOICE_SERVICE)
    command_preview = _section(android_voice_manager, "fun previewCommandCue", "fun previewCountdownCue")
    countdown_preview = _section(android_voice_manager, "fun previewCountdownCue", "fun beginSession")
    ios_command_preview = _section(ios_voice_service, "func previewCommandCue", "func previewCountdownCue")
    ios_countdown_preview = _section(ios_voice_service, "func previewCountdownCue", "func beginSession")

    assert "TextToSpeech" not in android_voice_manager
    assert "SYSTEM_SYNTHESIZED" not in android_voice_manager
    assert "VoicePreviewSampleCatalog.femaleCommandFilenames" in command_preview
    assert "VoicePreviewSampleCatalog.maleCommandFilenames" in command_preview
    assert "nextPreviewCueFilename(" in android_voice_manager
    assert "speak(" not in command_preview
    assert "packStore.voiceCatalog()" not in command_preview
    assert "VoicePreviewSampleCatalog.femaleElapsedFilename" in countdown_preview
    assert "VoicePreviewSampleCatalog.maleElapsedFilename" in countdown_preview
    assert "speak(" not in countdown_preview
    assert "packStore.voiceCatalog()" not in countdown_preview
    assert "female_preview_thirty_seconds_elapsed_stay_locked_in" not in android_voice_manager
    assert "VoicePreviewSampleCatalog.femaleCommandFilenames" in ios_command_preview
    assert "VoicePreviewSampleCatalog.maleCommandFilenames" in ios_command_preview
    assert "nextPreviewFilename(" in ios_voice_service
    assert "speak(" not in ios_command_preview
    assert "randomCommandCue()" not in ios_command_preview
    assert "VoicePreviewSampleCatalog.femaleElapsedFilename" in ios_countdown_preview
    assert "VoicePreviewSampleCatalog.maleElapsedFilename" in ios_countdown_preview
    assert "speak(" not in ios_countdown_preview
    assert "packStore.voiceCatalog(bundle: bundle)" not in ios_countdown_preview
    assert "female_preview_thirty_seconds_elapsed_stay_locked_in" not in ios_voice_service


def test_ci_runs_static_and_live_voice_regression_guards() -> None:
    workflow = _read(CI_WORKFLOW)
    verify_script = _read(VOICE_VERIFY_SCRIPT)

    assert "Voice Provider Smoke" in workflow
    assert "scripts/verify_elevenlabs_voices.py" in workflow
    assert "ELEVENLABS_API_KEY" in workflow
    assert "Decide live smoke execution" in workflow
    assert 'steps.gate.outputs.run_live_smoke == \'true\'' in workflow
    assert "Record controlled skip" in workflow
    assert 'grep -q "quota_exceeded"' in workflow
    assert "no remaining credits" in workflow
    assert "content/pro_audio/voice_personas.json" in verify_script
    assert "/v1/text-to-speech/" in verify_script
    assert "verifiedProbes" in verify_script


def test_female_voice_pack_workflow_uses_contract_driven_human_profile() -> None:
    workflow = _read(ROOT / ".github/workflows/generate-female-voice-pack.yml")

    assert 'contract = json.load(open("content/pro_audio/voice_personas.json"))' in workflow
    assert 'VOICE_ID = female["primaryVoice"]["voiceId"]' in workflow
    assert 'MODEL_ID = female["modelId"]' in workflow
    assert 'SETTINGS = female.get("voiceSettings", {})' in workflow
    assert 'GENERATION_CONFIG = female.get("generationConfig", {})' in workflow
    assert 'payload["generation_config"] = GENERATION_CONFIG' in workflow
    assert 'voiceName"] = female["primaryVoice"]["voiceName"]' in workflow
    assert "Domi" not in workflow
    assert 'feat/female-voice-pack-${GITHUB_RUN_ID}' in workflow
