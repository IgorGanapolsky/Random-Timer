import importlib.util
from pathlib import Path


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
