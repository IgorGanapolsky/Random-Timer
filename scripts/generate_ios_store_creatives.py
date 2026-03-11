#!/usr/bin/env python3
"""Tactical-grade App Store screenshot generator.

Produces high-impact, outcome-focused creatives with:
- Linear gradient depth backgrounds
- Soft-drop shadows for UI elevation
- Standardized Pro Max and iPad Pro resolutions
- High-contrast typography and tactical badges
- Fastlane-compatible device subdirectory output (APP_IPHONE_67, APP_IPAD_PRO_3GEN_129)
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont


Color = Tuple[int, int, int]

# Fastlane device subdir names (must match exactly for `deliver` to pick them up)
IPHONE_SUBDIR = "APP_IPHONE_67"
IPAD_SUBDIR = "APP_IPAD_PRO_3GEN_129"

# Standardized target resolutions (App Store requirements)
RESOLUTION_IPHONE = (1290, 2796)   # iPhone 15 Pro Max 6.7"
RESOLUTION_IPAD = (2048, 2732)     # iPad Pro 12.9" 3rd gen


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

# Source originals to avoid nested re-processing
SOURCE_MAP: Dict[str, str] = {
    "1_setup.png": "originals/1_setup.png",
    "2_active.png": "originals/2_active.png",
    "3_alarm.png": "originals/3_alarm.png",
    "4_running.png": "originals/4_running.png",
    "5_ipad_setup.png": "originals/5_ipad_setup.png",
    "6_ipad_running.png": "originals/6_ipad_running.png",
    "7_ipad_stopped.png": "originals/7_ipad_stopped.png",
}

# Which Fastlane device subdir each screenshot belongs to
DEVICE_SUBDIR: Dict[str, str] = {
    "1_setup.png": IPHONE_SUBDIR,
    "2_active.png": IPHONE_SUBDIR,
    "3_alarm.png": IPHONE_SUBDIR,
    "4_running.png": IPHONE_SUBDIR,
    "5_ipad_setup.png": IPAD_SUBDIR,
    "6_ipad_running.png": IPAD_SUBDIR,
    "7_ipad_stopped.png": IPAD_SUBDIR,
}


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        ("/System/Library/Fonts/Avenir Next.ttc", 13 if bold else 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0),
        ("/System/Library/Fonts/Supplemental/Avenir Next Condensed Heavy.ttf" if bold
         else "/System/Library/Fonts/Supplemental/Avenir Next.ttc", 0),
    ]
    for path, index in font_candidates:
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_text_wrapped(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    canvas_w: int,
    y: int,
    fill: tuple,
    margin: int = 60,
) -> int:
    """Draw word-wrapped centered text. Returns y coordinate after last line."""
    max_w = canvas_w - margin * 2
    lines = _wrap_text(text, font, max_w)
    line_spacing = int(font.size * 1.2) if hasattr(font, "size") else 40
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        draw.text(((canvas_w - lw) // 2, y), line, font=font, fill=fill)
        y += line_spacing
    return y


def _draw_gradient(draw: ImageDraw.Draw, size: Tuple[int, int], top_color: Color, bottom_color: Color) -> None:
    w, h = size
    for y in range(h):
        ratio = (y / h) ** 1.2
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _render_one(source: Image.Image, text: CreativeText, is_ipad: bool = False) -> Image.Image:
    w, h = RESOLUTION_IPAD if is_ipad else RESOLUTION_IPHONE

    # Background: Tactical Abyss (Deep Grey to True Black)
    base = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(base)
    _draw_gradient(draw, (w, h), (18, 18, 22), (2, 2, 4))

    # Subtle tactical red glow at top
    glow_h = int(h * 0.3)
    glow = Image.new("RGBA", (w, glow_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for y in range(glow_h):
        alpha = int(40 * (1 - (y / glow_h)))
        glow_draw.line([(0, y), (w, y)], fill=(220, 38, 38, alpha))

    # Header text — flow-based layout so wrapping never causes overlap
    title_size = max(84, int(h * 0.052))
    subtitle_size = max(36, int(h * 0.020))
    title_font = _load_font(title_size, bold=True)
    subtitle_font = _load_font(subtitle_size, bold=False)
    badge_font = _load_font(max(30, int(h * 0.015)), bold=True)

    y = int(h * 0.06)
    y = _draw_text_wrapped(draw, text.title, title_font, w, y, (255, 255, 255))
    y += int(h * 0.012)
    y = _draw_text_wrapped(draw, text.subtitle, subtitle_font, w, y, (161, 161, 170))
    y += int(h * 0.018)

    # Tactical Red Badge
    badge_bbox = draw.textbbox((0, 0), text.badge, font=badge_font)
    bw, bh = badge_bbox[2] - badge_bbox[0], badge_bbox[3] - badge_bbox[1]
    pad_x, pad_y = 32, 14
    bx1 = (w - (bw + pad_x * 2)) // 2
    by1 = y
    bx2, by2 = bx1 + bw + pad_x * 2, by1 + bh + pad_y * 2
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=12, fill=(220, 38, 38))
    draw.text((bx1 + pad_x, by1 + pad_y - 2), text.badge, font=badge_font, fill=(255, 255, 255))
    y = by2 + int(h * 0.02)

    # App UI Placement: fit source into available space below header WITHOUT clipping
    ui_top = y
    ui_margin = int(w * 0.06)
    target_w = w - (ui_margin * 2)
    available_h = h - ui_top - int(h * 0.02)  # 2% bottom padding

    src_w, src_h = source.size

    # Compute scale bounded by BOTH width and available height
    scale_w = target_w / src_w
    scale_h = available_h / src_h
    scale = min(scale_w, scale_h)

    render_w = int(src_w * scale)
    render_h = int(src_h * scale)

    # Center horizontally within the margin area
    ui_x = (w - render_w) // 2

    ui_frame = source.resize((render_w, render_h), Image.Resampling.LANCZOS)

    # Elevation shadow
    shadow_blur = 50
    shadow = Image.new("RGBA", (render_w + shadow_blur * 2, render_h + shadow_blur * 2), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (shadow_blur, shadow_blur, shadow_blur + render_w, shadow_blur + render_h),
        radius=int(40 * scale),
        fill=(0, 0, 0, 180),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))

    # Compose
    base_rgba = base.convert("RGBA")
    base_rgba.alpha_composite(glow, (0, 0))
    base_rgba.alpha_composite(shadow, (ui_x - shadow_blur, ui_top - shadow_blur + 20))

    # Rounded mask for UI frame
    mask = Image.new("L", (render_w, render_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, render_w, render_h), radius=int(55 * scale), fill=255)
    base_rgba.paste(ui_frame, (ui_x, ui_top), mask=mask)

    return base_rgba.convert("RGB")


def generate(repo_root: Path, locale: str) -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    written: List[str] = []

    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"Screenshots directory not found: {screenshots_dir}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = screenshots_dir / "_backup" / timestamp

    for filename, text in CREATIVE_COPY.items():
        # Resolve source: prefer originals/ to avoid re-processing composites
        source_rel = SOURCE_MAP.get(filename, filename)
        source_path = screenshots_dir / source_rel
        if not source_path.is_file():
            # Fallback: try root-level file
            source_path = screenshots_dir / filename
            if not source_path.is_file():
                print(f"WARNING: source not found for {filename}, skipping.")
                continue

        # Determine Fastlane device subdir
        subdir_name = DEVICE_SUBDIR[filename]
        device_dir = screenshots_dir / subdir_name
        device_dir.mkdir(parents=True, exist_ok=True)

        target = device_dir / filename

        # Backup existing target if present
        if target.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_dir / filename)

        source = Image.open(source_path).convert("RGB")

        # Handle accidental landscape orientation
        if source.width > source.height:
            source = source.rotate(90, expand=True)

        is_ipad = "ipad" in filename
        out = _render_one(source, text, is_ipad=is_ipad)
        out.save(target, format="PNG", optimize=True)
        written.append(str(target.relative_to(repo_root)))

    report = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "locale": locale,
        "written_files": written,
        "backup_dir": str(backup_dir) if written else None,
        "fastlane_iphone_dir": str((screenshots_dir / IPHONE_SUBDIR).relative_to(repo_root)),
        "fastlane_ipad_dir": str((screenshots_dir / IPAD_SUBDIR).relative_to(repo_root)),
        "report_path": str(screenshots_dir / "report.json"),
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
