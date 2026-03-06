#!/usr/bin/env python3
"""Tactical-grade App Store screenshot generator.

Produces high-impact, outcome-focused creatives with:
- Linear gradient depth backgrounds
- Soft-drop shadows for UI elevation
- Standardized Pro Max and iPad Pro resolutions
- High-contrast typography and tactical badges
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter


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

# Standardized target resolutions
RESOLUTION_IPHONE = (1290, 2796)
RESOLUTION_IPAD = (2048, 2732)

# Source map pointing to originals to avoid nested framing
SOURCE_MAP: Dict[str, str] = {
    "1_setup.png": "originals/1_setup.png",
    "2_active.png": "originals/2_active.png",
    "3_alarm.png": "originals/3_alarm.png",
    "4_running.png": "originals/4_running.png",
    "5_ipad_setup.png": "originals/5_ipad_setup.png",
    "6_ipad_running.png": "originals/6_ipad_running.png",
    "7_ipad_stopped.png": "originals/7_ipad_stopped.png",
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


def _draw_gradient(draw: ImageDraw.Draw, size: Tuple[int, int], top_color: Color, bottom_color: Color):
    w, h = size
    for y in range(h):
        r = top_color[0] + (bottom_color[0] - top_color[0]) * y // h
        g = top_color[1] + (bottom_color[1] - top_color[1]) * y // h
        b = top_color[2] + (bottom_color[2] - top_color[2]) * y // h
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _render_one(source: Image.Image, text: CreativeText, is_ipad: bool = False) -> Image.Image:
    w, h = RESOLUTION_IPAD if is_ipad else RESOLUTION_IPHONE
    
    # Background: Deep Tactical Gradient
    base = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(base)
    _draw_gradient(draw, (w, h), (25, 30, 42), (10, 12, 18))

    # Outcome-First Header Section
    title_font = _load_font(max(72, int(h * 0.045)), bold=True)
    subtitle_font = _load_font(max(32, int(h * 0.018)), bold=False)
    
    title_bbox = draw.textbbox((0, 0), text.title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((w - title_w) // 2, int(h * 0.06)), text.title, font=title_font, fill=(255, 255, 255))
    
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
    
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=8, fill=(220, 38, 38))
    draw.text((bx1 + pad_x, by1 + pad_y - 2), text.badge, font=badge_font, fill=(255, 255, 255))

    # App UI Placement
    ui_top = int(h * 0.24)
    ui_margin = int(w * 0.06)
    target_w = w - (ui_margin * 2)
    target_h = h - ui_top + 100 # bleed off the bottom
    
    # Scale source to fit target_w while maintaining aspect ratio
    src_w, src_h = source.size
    scale = target_w / src_w
    render_w = int(src_w * scale)
    render_h = int(src_h * scale)
    
    ui_frame = source.resize((render_w, render_h), Image.Resampling.LANCZOS)
    
    # Create shadow
    shadow_offset = 20
    shadow_blur = 30
    shadow = Image.new("RGBA", (render_w + shadow_blur * 2, render_h + shadow_blur * 2), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (shadow_blur, shadow_blur, shadow_blur + render_w, shadow_blur + render_h),
        radius=int(20 * scale),
        fill=(0, 0, 0, 180)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    
    # Paste shadow then UI
    base_rgba = base.convert("RGBA")
    ui_x = (w - render_w) // 2
    base_rgba.alpha_composite(shadow, (ui_x - shadow_blur + 5, ui_top - shadow_blur + shadow_offset))
    
    # Paste UI (rounded corners)
    mask = Image.new("L", (render_w, render_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, render_w, render_h), radius=int(40 * scale), fill=255)
    
    base_rgba.paste(ui_frame, (ui_x, ui_top), mask=mask)

    return base_rgba.convert("RGB")


def generate(repo_root: Path, locale: str) -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    written: list[str] = []

    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"Screenshots directory not found: {screenshots_dir}")

    # Backup logic
    backup_root = screenshots_dir / "_backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp
    
    for filename, text in CREATIVE_COPY.items():
        source_path = screenshots_dir / SOURCE_MAP.get(filename, filename)
        if not source_path.is_file():
            # Fallback if originals don't exist for some reason
            source_path = screenshots_dir / filename
            if not source_path.is_file():
                print(f"⚠️ Source screenshot not found: {source_path}, skipping.")
                continue

        # If target file exists, move to backup
        target = screenshots_dir / filename
        if target.exists() and not str(target).endswith("originals/" + filename):
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_dir / filename)

        source = Image.open(source_path).convert("RGB")
        
        # Handle orientation for 3_alarm if it's landscape by mistake
        if source.width > source.height:
            source = source.rotate(90, expand=True)

        is_ipad = "ipad" in filename
        out = _render_one(source, text, is_ipad=is_ipad)
        
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    report = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "locale": locale,
        "written_files": written,
        "backup_dir": str(backup_dir) if written else None,
        "report_path": str(screenshots_dir / "report.json")
    }
    
    with open(report["report_path"], "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--locale", default="en-US")
    args = parser.parse_args()
    print(json.dumps(generate(Path(args.repo_root), args.locale), indent=2))
