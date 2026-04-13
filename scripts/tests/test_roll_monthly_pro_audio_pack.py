from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import roll_monthly_pro_audio_pack as roll


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def _manifest_before_current_month_roll() -> dict:
    manifest = copy.deepcopy(json.loads(MANIFEST.read_text(encoding="utf-8")))
    active = next(pack for pack in manifest["packs"] if pack["id"] == manifest["activePackId"])
    active["releaseMonth"] = "2026-03"
    manifest["packs"] = [
        pack for pack in manifest["packs"]
        if pack["id"] != "2026-04_tactical_reaction_lanes"
    ]
    return manifest


def test_roll_manifest_creates_current_month_pack() -> None:
    manifest = _manifest_before_current_month_roll()

    updated, changed = roll.roll_manifest(manifest, "2026-04")

    assert changed is True
    assert updated["activePackId"] == "2026-04_tactical_reaction_lanes"
    active = next(pack for pack in updated["packs"] if pack["id"] == updated["activePackId"])
    assert active["releaseMonth"] == "2026-04"
    assert len(active["elapsedCues"]) >= 12
    assert len(active["commandCues"]) >= 20
    assert all("elapsed" in cue["text"].lower() for cue in active["elapsedCues"])


def test_roll_manifest_is_idempotent_after_pack_exists() -> None:
    manifest = _manifest_before_current_month_roll()
    updated, changed = roll.roll_manifest(manifest, "2026-04")
    assert changed is True

    again, changed_again = roll.roll_manifest(updated, "2026-04")

    assert changed_again is False
    assert again["activePackId"] == "2026-04_tactical_reaction_lanes"


def test_roll_manifest_corrects_current_month_with_wrong_active_pack_id() -> None:
    manifest = _manifest_before_current_month_roll()
    active = next(pack for pack in manifest["packs"] if pack["id"] == manifest["activePackId"])
    active["releaseMonth"] = "2026-04"

    updated, changed = roll.roll_manifest(manifest, "2026-04")

    assert changed is True
    assert updated["activePackId"] == "2026-04_tactical_reaction_lanes"


def test_build_pack_tolerates_missing_previous_sound_arsenal() -> None:
    manifest = _manifest_before_current_month_roll()
    previous = next(pack for pack in manifest["packs"] if pack["id"] == manifest["activePackId"])
    previous.pop("soundArsenal")

    pack = roll.build_pack("2026-04", previous)

    assert pack["soundArsenal"] == []
