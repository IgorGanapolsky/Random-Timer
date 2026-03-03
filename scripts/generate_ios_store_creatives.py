#!/usr/bin/env python3
"""Overhauled result-first App Store screenshot generator.

Transitions from generic templates to high-contrast tactical creatives
focused on outcome-first messaging and professional utility standards.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class CreativeText:
    title: str
    subtitle: str
    badge: str


CREATIVE_COPY: Dict[str, CreativeText] = {
    "1_setup.png": CreativeText(
        title="SHARPEN YOUR DRAW",
        subtitle="Randomized signals for dry-fire and target acquisition.",
        badge="REACTION SPEED",
    ),
    "2_active.png": CreativeText(
        title="STOP PREDICTING",
        subtitle="Unpredictable intervals ensure you stay honest under stress.",
        badge="ELIMINATE RHYTHM",
    ),
    "3_alarm.png": CreativeText(
        title="RANGE COMMANDS",
        subtitle="High-intensity audio arsenal designed for the noise of the gym.",
        badge="SIGNAL HIT",
    ),
    "4_running.png": CreativeText(
        title="BATTLE READY",
        subtitle="Non-stop automated rounds for boxing, MMA, and HIIT.",
        badge="RUN DRILLS",
    ),
    "5_ipad_setup.png": CreativeText(
        title="COACH VIEW",
        subtitle="Class-optimized controls for class-wide reaction stress tests.",
        badge="PRO UTILITY",
    ),
    "6_ipad_running.png": CreativeText(
        title="VISIBLE BATTLESPACE",
        subtitle="Large-scale UI ensures every athlete stays synchronized.",
        badge="MISSION READY",
    ),
    "7_ipad_stopped.png": CreativeText(
        title="RAPID RESET",
        subtitle="Zero friction between rounds. Adjust and execute immediately.",
        badge="GO AGAIN",
    ),
}

# Fixed SOURCE_MAP to avoid nested compositions.
SOURCE_MAP: Dict[str, str] = {
    "1_setup.png": "1_setup.png",
    "2_active.png": "2_active.png",
    "3_alarm.png": "3_alarm.png",
    "4_running.png": "4_running.png",
    "5_ipad_setup.png": "5_ipad_setup.png",
    "6_ipad_running.png": "6_ipad_running.png",
    "7_ipad_stopped.png": "7_ipad_stopped.png",
}


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next Condensed Heavy.ttf" if bold else "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_one(source: Image.Image, text: CreativeText) -> Image.Image:
    w, h = source.size
    
    # Background: Solid high-contrast Tactical Black
    base = Image.new("RGB", (w, h), (10, 12, 18))
    draw = ImageDraw.Draw(base)

    # Outcome-First Header Section
    title_font = _load_font(max(72, int(h * 0.045)), bold=True)
    subtitle_font = _load_font(max(32, int(h * 0.018)), bold=False)
    
    title_bbox = draw.textbbox((0, 0), text.title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    
    # Draw large headline
    draw.text(((w - title_w) // 2, int(h * 0.06)), text.title, font=title_font, fill=(255, 255, 255))
    
    # Draw outcome subtitle
    subtitle_bbox = draw.textbbox((0, 0), text.subtitle, font=subtitle_font)
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((w - subtitle_w) // 2, int(h * 0.12)), text.subtitle, font=subtitle_font, fill=(180, 190, 210))

    # Badge (Result)
    badge_font = _load_font(max(28, int(h * 0.015)), bold=True)
    badge_bbox = draw.textbbox((0, 0), text.badge, font=badge_font)
    bw, bh = badge_bbox[2] - badge_bbox[0], badge_bbox[3] - badge_bbox[1]
    
    pad_x, pad_y = 24, 12
    bx1 = (w - (bw + pad_x * 2)) // 2
    by1 = int(h * 0.165)
    bx2, by2 = bx1 + bw + pad_x * 2, by1 + bh + pad_y * 2
    
    # Tactical Red Badge
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=8, fill=(220, 38, 38))
    draw.text((bx1 + pad_x, by1 + pad_y - 2), text.badge, font=badge_font, fill=(255, 255, 255))

    # App UI Placement: Full-Bleed Offset (High Trust)
    # We crop the source to show the most relevant parts of the UI without muddy framing.
    ui_top = int(h * 0.24)
    ui_margin = int(w * 0.05)
    target_w = w - (ui_margin * 2)
    target_h = h - ui_top
    
    # Fit source into the remaining space
    ui_frame = ImageOps.fit(source, (target_w, target_h), method=Image.Resampling.LANCZOS)
    
    # Paste directly with sharp high-contrast border
    draw.rectangle((ui_margin - 2, ui_top - 2, w - ui_margin + 2, h + 2), outline=(40, 50, 70), width=2)
    base.paste(ui_frame, (ui_margin, ui_top))

    return base


def generate(repo_root: Path, locale: str) -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    written: list[str] = []

    for filename, text in CREATIVE_COPY.items():
        source_path = screenshots_dir / SOURCE_MAP.get(filename, filename)
        if not source_path.is_file():
            continue

        source = Image.open(source_path).convert("RGB")
        out = _render_one(source, text)
        
        target = screenshots_dir / filename
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    return {"status": "success", "files": written}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--locale", default="en-US")
    args = parser.parse_args()
    print(json.dumps(generate(Path(args.repo_root), args.locale), indent=2))
