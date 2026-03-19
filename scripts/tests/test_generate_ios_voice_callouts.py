import importlib.util
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "generate_ios_voice_callouts.py"
CATALOG_PATH = ROOT / "native-ios" / "RandomTimer" / "Resources" / "Audio" / "voice_callouts.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_ios_voice_callouts", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_catalog_lines_cover_preview_elapsed_and_command_cues():
    module = _load_module()
    catalog = module._load_catalog(CATALOG_PATH)

    lines = module._catalog_lines(catalog)

    expected_count = 1 + len(catalog["elapsedCues"]) + len(catalog["commandCues"])
    assert len(lines) == expected_count
    assert lines[0] == (
        catalog["previewElapsed"]["filename"],
        catalog["previewElapsed"]["text"],
    )


def test_resolve_voice_prefers_custom_voice_category():
    module = _load_module()
    voices = [
        {"name": "Marine Drill Voice", "voice_id": "premade-id", "category": "premade"},
        {"name": "Marine Drill Voice", "voice_id": "cloned-id", "category": "cloned"},
        {"name": "Something Else", "voice_id": "other-id", "category": "generated"},
    ]

    resolved = module._resolve_voice(voices, None, "marine")

    assert resolved["voice_id"] == "cloned-id"


def test_resolve_voice_reports_available_voices_when_pattern_misses():
    module = _load_module()
    voices = [
        {"name": "Adam", "voice_id": "adam-id", "category": "premade"},
        {"name": "Bella", "voice_id": "bella-id", "category": "premade"},
    ]

    try:
        module._resolve_voice(voices, None, "marine")
    except SystemExit as error:
        message = str(error)
    else:
        raise AssertionError("Expected _resolve_voice to exit when no voice matches.")

    assert "Available voices" in message
    assert "Adam" in message
    assert "Bella" in message


def test_configured_voice_skips_voice_library_lookup():
    module = _load_module()

    configured = module._configured_voice("DGzg6RaUqxGRTHSBjfgF")

    assert configured == {
        "name": "Configured custom drill instructor voice",
        "voice_id": "DGzg6RaUqxGRTHSBjfgF",
        "category": "configured",
    }


def test_load_voice_settings_falls_back_when_settings_are_not_readable():
    module = _load_module()

    def failing_request(_path, _api_key):
        raise SystemExit("missing voices_read")

    module._request_json = failing_request

    settings = module._load_voice_settings("ignored", "DGzg6RaUqxGRTHSBjfgF")

    assert settings == {
        "stability": 0.4,
        "similarity_boost": 0.8,
        "style": 0.65,
        "use_speaker_boost": True,
        "speed": 0.95,
    }


def test_remove_stale_assets_keeps_only_manifest_backed_files():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        (output_dir / "keep_me.mp3").write_bytes(b"keep")
        (output_dir / "delete_me.mp3").write_bytes(b"delete")

        module._remove_stale_assets([("keep_me", "Keep me.")], output_dir)

        assert (output_dir / "keep_me.mp3").exists()
        assert not (output_dir / "delete_me.mp3").exists()
