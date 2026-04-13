import json
from pathlib import Path

from scripts.roll_monthly_pro_audio_pack import roll_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def _manifest_copy() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_roll_manifest_creates_new_current_month_pack() -> None:
    manifest = _manifest_copy()

    result = roll_manifest(manifest, "2026-05")

    assert result["changed"] is True
    assert result["releaseMonth"] == "2026-05"
    assert manifest["activePackId"] == result["activePackId"]
    pack = next(item for item in manifest["packs"] if item["id"] == result["activePackId"])
    assert pack["releaseMonth"] == "2026-05"
    assert len(pack["commandCues"]) == 24
    assert len(pack["elapsedCues"]) == 16
    assert len(pack["soundArsenal"]) == 10
    assert all("elapsed" in cue["text"].casefold() for cue in pack["elapsedCues"])
    assert pack["fallbackCommandFilename"] == pack["commandCues"][0]["filename"]
    drum_roll = next(sound for sound in pack["soundArsenal"] if sound["soundType"] == "drumRoll")
    assert "Military snare roll" in drum_roll["prompt"]


def test_roll_manifest_is_idempotent_for_existing_month() -> None:
    manifest = _manifest_copy()
    first = roll_manifest(manifest, "2026-06")
    count_after_first = len(manifest["packs"])

    second = roll_manifest(manifest, "2026-06")

    assert first["changed"] is True
    assert second["changed"] is False
    assert second["activePackId"] == first["activePackId"]
    assert len(manifest["packs"]) == count_after_first
