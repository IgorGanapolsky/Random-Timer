#!/usr/bin/env python3
"""Create or activate the current monthly Pro audio pack."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"

ELAPSED_SECONDS = (15, 30, 45, 60, 75, 90, 105, 120, 150, 180, 210, 240, 300, 420, 540, 600)

MONTHLY_THEMES: tuple[dict[str, Any], ...] = (
    {
        "slug": "combat_sports_cadence",
        "theme": "Combat sports cadence",
        "sound_style": "Dry gym acoustics, fight-night urgency, clean transient attack",
        "commands": (
            "Hands up. Move.",
            "Circle off the line.",
            "Sharp feet. Sharp eyes.",
            "Reset your stance.",
            "Breathe and fire back.",
            "Win the next exchange.",
            "Cut the angle.",
            "Stay loose. Stay dangerous.",
            "Pressure forward.",
            "Defend and return.",
            "Do not admire the work.",
            "Snap back to guard.",
            "Own the center.",
            "Change levels.",
            "Eyes on target.",
            "Fast exit. Fast reset.",
            "Keep your base.",
            "Hands return home.",
            "Punch out. Move out.",
            "Footwork first.",
            "Make the next rep clean.",
            "Drive through the bell.",
            "Stay in the pocket.",
            "Finish disciplined.",
        ),
        "elapsed": (
            "Keep your guard high.",
            "Stay on rhythm.",
            "Do not square up.",
            "Breathe under pressure.",
            "Win the next beat.",
            "Keep working angles.",
        ),
    },
    {
        "slug": "tactical_range_discipline",
        "theme": "Tactical range discipline",
        "sound_style": "Outdoor range clarity, command-post pressure, no musical tail",
        "commands": (
            "Scan and move.",
            "Muzzle discipline.",
            "Find cover.",
            "Control your breathing.",
            "Move with intent.",
            "Eyes up.",
            "Stay accountable.",
            "Check your sector.",
            "Smooth is fast.",
            "Hold the line.",
            "Pressure test your plan.",
            "No wasted motion.",
            "Reset and assess.",
            "Stay behind cover.",
            "Communicate clearly.",
            "Keep your footing.",
            "Own your lane.",
            "Move on command.",
            "Maintain spacing.",
            "Work the problem.",
            "Precision first.",
            "Keep your head on a swivel.",
            "Recover and reengage.",
            "Finish the drill clean.",
        ),
        "elapsed": (
            "Assess and move.",
            "Keep the plan simple.",
            "Stay deliberate.",
            "Control the tempo.",
            "Work from cover.",
            "Maintain discipline.",
        ),
    },
    {
        "slug": "hiit_power_rounds",
        "theme": "HIIT power rounds",
        "sound_style": "Training-floor punch, bright alarm edge, high-energy but not musical",
        "commands": (
            "Explode now.",
            "Drive your knees.",
            "Stay tall.",
            "Push the floor away.",
            "Fast hands.",
            "Keep the engine hot.",
            "Brace and move.",
            "No dead reps.",
            "Attack the interval.",
            "Own your breathing.",
            "Stay springy.",
            "Keep your hips under you.",
            "Find another gear.",
            "Recover in motion.",
            "Make it crisp.",
            "Stay light.",
            "Punch the clock.",
            "Work with purpose.",
            "Keep tension.",
            "Move clean.",
            "Power through.",
            "Do not drift.",
            "Hold form.",
            "Finish loud.",
        ),
        "elapsed": (
            "Stay explosive.",
            "Keep form tight.",
            "Breathe and drive.",
            "Hold the pace.",
            "Make every rep count.",
            "Stay under control.",
        ),
    },
    {
        "slug": "defensive_tactics_pressure",
        "theme": "Defensive tactics pressure",
        "sound_style": "Close-quarters training intensity, clipped alert tones, no voice",
        "commands": (
            "Create space.",
            "Protect your base.",
            "Frame and move.",
            "Hands active.",
            "Clear the line.",
            "Control the tie.",
            "Stay off the wall.",
            "Move your feet.",
            "Break contact.",
            "Own the underhook.",
            "Turn the corner.",
            "Keep posture.",
            "Stand up strong.",
            "Get back to stance.",
            "Do not freeze.",
            "Win inside position.",
            "Pressure and angle.",
            "Hips back.",
            "Eyes forward.",
            "Recover your balance.",
            "Fight the grip.",
            "Reset the distance.",
            "Stay technical.",
            "Finish safe.",
        ),
        "elapsed": (
            "Protect your posture.",
            "Keep your base alive.",
            "Make space now.",
            "Stay technical.",
            "Control the position.",
            "Recover your stance.",
        ),
    },
)

SOUND_BASES: dict[str, str] = {
    "intense": "Command-post emergency tone, clipped attack, clear loop point",
    "gentle": "Clean single training chime with soft tail, subtle but clear",
    "klaxon": "Forceful midrange klaxon, loopable, urgent and controlled",
    "whistle": "Coach whistle blast, crisp onset, realistic air pressure",
    "buzzer": "Gym timer buzzer, square attack, short decay",
    "gong": "Focused metal gong strike, controlled resonance, clean tail",
    "airhorn": "Stadium air horn burst, authoritative and short",
    "drumRoll": "Military snare roll, tight cadence, decisive final accent",
    "siren": "Compact training siren sweep, urgent but not harsh",
    "bell": "Boxing round bell, bright strike, fast room decay",
}


def _month_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _validate_month(value: str) -> str:
    candidate = value.strip()
    if not re.fullmatch(r"\d{4}-\d{2}", candidate):
        raise SystemExit(f"Expected --month as YYYY-MM, got {value!r}")
    year, month = candidate.split("-")
    if not 1 <= int(month) <= 12:
        raise SystemExit(f"Expected --month between 01 and 12, got {value!r}")
    return f"{int(year):04d}-{int(month):02d}"


def _theme_for_month(month: str) -> dict[str, Any]:
    year, month_number = (int(part) for part in month.split("-"))
    index = (year * 12 + month_number - 1) % len(MONTHLY_THEMES)
    return MONTHLY_THEMES[index]


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return normalized or "monthly_audio"


def _spoken_time(seconds: int) -> str:
    labels = {
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
    return labels.get(seconds, f"{seconds} seconds")


def _load_manifest() -> dict[str, Any]:
    return json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))


def _write_manifest(manifest: dict[str, Any]) -> None:
    DEFAULT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _existing_pack_for_month(manifest: dict[str, Any], month: str) -> dict[str, Any] | None:
    return next((pack for pack in manifest.get("packs", []) if pack.get("releaseMonth") == month), None)


def _active_pack(manifest: dict[str, Any]) -> dict[str, Any]:
    active_pack_id = manifest.get("activePackId")
    for pack in manifest.get("packs", []):
        if pack.get("id") == active_pack_id:
            return pack
    raise SystemExit(f"Active Pro audio pack {active_pack_id!r} is missing from manifest.")


def _sound_prompt(sound: dict[str, Any], theme: dict[str, Any]) -> str:
    sound_type = str(sound.get("soundType") or sound.get("filename") or "").strip()
    base = SOUND_BASES.get(sound_type, str(sound.get("prompt") or "Training alert sound").rstrip("."))
    return f"{base}. {theme['sound_style']}. Loopable, no voice."


def build_pack(month: str, base_pack: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    pack = deepcopy(base_pack)
    commands = list(theme["commands"])
    elapsed = list(theme["elapsed"])
    pack["id"] = f"{month}_{theme['slug']}"
    pack["releaseMonth"] = month
    pack["theme"] = f"{theme['theme']} ({month} content window)"
    pack["previewElapsed"] = {
        "filename": "preview_elapsed",
        "text": f"Thirty seconds elapsed. {elapsed[0]}",
    }
    pack["fallbackCommandFilename"] = _slugify(commands[0])
    pack["commandCues"] = [
        {"filename": _slugify(command), "text": command}
        for command in commands
    ]
    pack["elapsedCues"] = [
        {
            "second": second,
            "filename": f"elapsed_{second}s",
            "text": f"{_spoken_time(second)} elapsed. {elapsed[index % len(elapsed)]}",
        }
        for index, second in enumerate(ELAPSED_SECONDS)
    ]
    pack["soundArsenal"] = [
        {
            **sound,
            "prompt": _sound_prompt(sound, theme),
        }
        for sound in base_pack.get("soundArsenal", [])
    ]
    return pack


def roll_manifest(manifest: dict[str, Any], month: str) -> dict[str, Any]:
    existing = _existing_pack_for_month(manifest, month)
    if existing is not None:
        manifest["activePackId"] = existing["id"]
        return {
            "changed": False,
            "activePackId": existing["id"],
            "releaseMonth": month,
            "theme": existing.get("theme", ""),
        }

    base_pack = _active_pack(manifest)
    theme = _theme_for_month(month)
    pack = build_pack(month, base_pack, theme)
    manifest.setdefault("packs", []).append(pack)
    manifest["activePackId"] = pack["id"]
    return {
        "changed": True,
        "activePackId": pack["id"],
        "releaseMonth": month,
        "theme": pack["theme"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", default="", help="Target release month as YYYY-MM. Defaults to current UTC month.")
    parser.add_argument("--json-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    month = _validate_month(args.month or _month_key())
    manifest = _load_manifest()
    result = roll_manifest(manifest, month)
    _write_manifest(manifest)
    payload = {"status": "ok", **result}
    print(json.dumps(payload, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
