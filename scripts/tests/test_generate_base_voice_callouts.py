"""Tests for base voice callout generation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import generate_base_voice_callouts as gbvc

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "native-android/app/src/main/assets/voice_callouts.json"


def test_all_male_cue_lines_includes_preview_elapsed_and_commands() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    lines = gbvc._all_male_cue_lines(catalog)
    filenames = {stem for stem, _ in lines}
    assert "preview_elapsed" in filenames
    assert "elapsed_60s" in filenames
    assert "cmd_move_with_a_purpose" in filenames
    assert len(lines) == 1 + len(catalog["elapsedCues"]) + len(catalog["commandCues"])


def test_default_male_voice_id_matches_approved_clyde_contract() -> None:
    assert gbvc._default_male_voice_id() == "2EiwWnXFnvU5JabPnv8n"
    assert gbvc._default_male_voice_id() != gbvc.FORBIDDEN_MALE_VOICE_ID
