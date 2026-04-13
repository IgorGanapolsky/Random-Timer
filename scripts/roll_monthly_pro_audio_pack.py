#!/usr/bin/env python3
"""Create the next monthly Pro audio pack manifest entry deterministically."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"

THEMES = [
    {
        "slug": "fight_gym_rounds",
        "theme": "Fight gym rounds",
        "short": "Fight gym",
        "commands": [
            "Hands up. Work now.",
            "Angle out and reset.",
            "Fast feet. Sharp hands.",
            "Sprawl. Recover. Go.",
            "Pressure on. Keep moving.",
            "Breathe under fire.",
            "Win this exchange.",
            "Do not admire your work.",
            "Reset your stance.",
            "Explode on the cue.",
            "Keep your guard honest.",
            "Move your head.",
            "Level change now.",
            "Grip. Drive. Finish.",
            "Circle off the line.",
            "Strike and exit.",
            "Own the round.",
            "Scramble back to base.",
            "No lazy reps.",
            "Control the pace.",
            "Answer the bell.",
            "Stay dangerous.",
            "Recover fast.",
            "Finish clean.",
        ],
        "sound_prompt_suffix": "fight-gym clarity, clean transient, no crowd noise.",
    },
    {
        "slug": "tactical_reaction_lanes",
        "theme": "Tactical reaction lanes",
        "short": "Tactical lane",
        "commands": [
            "Scan. Move. Act.",
            "Get off the line.",
            "Fast decision. Clean movement.",
            "Reset your base.",
            "Control your breathing.",
            "Move with intent.",
            "Break contact and recover.",
            "Eyes up. Process now.",
            "Own the next second.",
            "No countdown. React.",
            "Change level and drive.",
            "Stay quiet. Stay fast.",
            "Pressure test the rep.",
            "Move before comfort.",
            "Keep working angles.",
            "Stabilize and continue.",
            "Hard reset. Go again.",
            "Make the cue matter.",
            "Simple. Fast. Accurate.",
            "Finish the lane.",
            "Stay in the problem.",
            "Recover your posture.",
            "Sharp response.",
            "Hold the standard.",
        ],
        "sound_prompt_suffix": "tactical training lane urgency, compact decay, no weapons.",
    },
    {
        "slug": "conditioning_pressure",
        "theme": "Conditioning pressure",
        "short": "Conditioning",
        "commands": [
            "Drive the pace.",
            "Pick it up now.",
            "Fast feet. Full effort.",
            "Do not coast.",
            "Breathe and push.",
            "Snap into the rep.",
            "Attack the next interval.",
            "Stay tall under fatigue.",
            "Recover while moving.",
            "Strong pace. Strong finish.",
            "Own your breathing.",
            "Keep the engine hot.",
            "Win the next ten.",
            "Move before you think.",
            "Hard work. Clean form.",
            "Pressure on the pedal.",
            "Explode and recover.",
            "Keep the tempo high.",
            "Finish this rep.",
            "Reset and attack.",
            "Fast start.",
            "Stay elastic.",
            "Do the simple thing hard.",
            "One more clean rep.",
        ],
        "sound_prompt_suffix": "conditioning-floor punch, loud enough for gym playback, no melody.",
    },
]

ELAPSED_SECONDS = [15, 30, 45, 60, 75, 90, 105, 120, 150, 180, 210, 240, 300, 420, 540, 600]
ELAPSED_LABELS = {
    15: "Fifteen seconds",
    30: "Thirty seconds",
    45: "Forty-five seconds",
    60: "One minute",
    75: "One minute fifteen",
    90: "One minute thirty",
    105: "One minute forty-five",
    120: "Two minutes",
    150: "Two minutes thirty",
    180: "Three minutes",
    210: "Three minutes thirty",
    240: "Four minutes",
    300: "Five minutes",
    420: "Seven minutes",
    540: "Nine minutes",
    600: "Ten minutes",
}


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", text).strip("_")


def _month_key(day: dt.date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _theme_for_month(month: str) -> dict[str, Any]:
    year, month_number = (int(part) for part in month.split("-", 1))
    return THEMES[(year * 12 + month_number) % len(THEMES)]


def _pack_id(month: str, theme: dict[str, Any]) -> str:
    return f"{month}_{theme['slug']}"


def _elapsed_cues(theme: dict[str, Any]) -> list[dict[str, Any]]:
    commands = theme["commands"]
    cues: list[dict[str, Any]] = []
    for index, second in enumerate(ELAPSED_SECONDS):
        cues.append(
            {
                "second": second,
                "filename": f"elapsed_{second}s",
                "text": f"{ELAPSED_LABELS[second]} elapsed. {commands[index % len(commands)]}",
            }
        )
    return cues


def _command_cues(theme: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "filename": f"cmd_{_slugify(text)}",
            "text": text,
        }
        for text in theme["commands"]
    ]


def build_pack(month: str, previous_pack: dict[str, Any]) -> dict[str, Any]:
    theme = _theme_for_month(month)
    command_cues = _command_cues(theme)
    fallback = command_cues[0]["filename"]
    sound_arsenal = deepcopy(previous_pack["soundArsenal"])
    for sound in sound_arsenal:
        prompt = str(sound.get("prompt") or "").rstrip(".")
        sound["prompt"] = f"{prompt}; {theme['sound_prompt_suffix']}"
    return {
        "id": _pack_id(month, theme),
        "releaseMonth": month,
        "theme": theme["theme"],
        "previewElapsed": {
            "filename": "preview_elapsed",
            "text": f"Thirty seconds elapsed. {theme['short']} pace. React now.",
        },
        "fallbackCommandFilename": fallback,
        "elapsedCues": _elapsed_cues(theme),
        "commandCues": command_cues,
        "soundArsenal": sound_arsenal,
    }


def roll_manifest(manifest: dict[str, Any], month: str) -> tuple[dict[str, Any], bool]:
    active_pack = next((pack for pack in manifest["packs"] if pack["id"] == manifest["activePackId"]), None)
    if active_pack is None:
        raise SystemExit(f"Active pack {manifest['activePackId']!r} is missing")
    if active_pack.get("releaseMonth") == month:
        return manifest, False

    target_theme = _theme_for_month(month)
    target_pack_id = _pack_id(month, target_theme)
    existing = next((pack for pack in manifest["packs"] if pack["id"] == target_pack_id), None)
    if existing is None:
        manifest["packs"].append(build_pack(month, active_pack))
    manifest["activePackId"] = target_pack_id
    return manifest, True


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll monthly Pro audio manifest to the requested month")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--month", default="", help="Target YYYY-MM. Defaults to current UTC month.")
    parser.add_argument("--today", default="", help="Optional YYYY-MM-DD test override.")
    parser.add_argument("--check", action="store_true", help="Do not write; exit non-zero if roll would be needed.")
    parser.add_argument("--json-stdout", action="store_true")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    month = args.month or _month_key(today)
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    updated, changed = roll_manifest(manifest, month)
    result = {
        "status": "roll_required" if changed else "current",
        "target_month": month,
        "activePackId": updated["activePackId"],
        "pack_count": len(updated["packs"]),
    }

    if args.check and changed:
        print(json.dumps(result, indent=2 if args.json_stdout else None))
        return 1
    if changed and not args.check:
        write_manifest(manifest_path, updated)
        result["status"] = "rolled"

    print(json.dumps(result, indent=2 if args.json_stdout else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
