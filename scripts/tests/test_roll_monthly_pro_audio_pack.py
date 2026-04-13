from __future__ import annotations

import json
from pathlib import Path

from scripts import roll_monthly_pro_audio_pack as roll


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def test_roll_manifest_creates_current_month_pack() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    updated, changed = roll.roll_manifest(manifest, "2026-04")

    assert changed is True
    assert updated["activePackId"] == "2026-04_tactical_reaction_lanes"
    active = next(pack for pack in updated["packs"] if pack["id"] == updated["activePackId"])
    assert active["releaseMonth"] == "2026-04"
    assert len(active["elapsedCues"]) >= 12
    assert len(active["commandCues"]) >= 20
    assert all("elapsed" in cue["text"].lower() for cue in active["elapsedCues"])


def test_roll_manifest_is_idempotent_after_pack_exists() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    updated, changed = roll.roll_manifest(manifest, "2026-04")
    assert changed is True

    again, changed_again = roll.roll_manifest(updated, "2026-04")

    assert changed_again is False
    assert again["activePackId"] == "2026-04_tactical_reaction_lanes"
