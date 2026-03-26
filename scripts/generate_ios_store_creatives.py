#!/usr/bin/env python3
"""Overhauled result-first App Store screenshot generator.

Transitions from generic templates to high-contrast tactical creatives
focused on outcome-first messaging and professional utility standards.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class CreativeText:
    eyebrow: str
    title: str
    subtitle: str
    badge: str


CREATIVE_COPY: Dict[str, CreativeText] = {
    "1_setup.png": CreativeText(
        eyebrow="CONTROL THE DRILL",
        title="REACT UNDER STRESS",
        subtitle="Set a live range and let randomness punish lazy rhythm.",
        badge="DRY FIRE • MMA • HIIT",
    ),
    "2_active.png": CreativeText(
        eyebrow="STAY HONEST",
        title="NO COUNTDOWN TO CHEAT",
        subtitle="Unpredictable start cues stop anticipation before it starts.",
        badge="PURE REACTION WORK",
    ),
    "3_voice.png": CreativeText(
        eyebrow="CUT THROUGH CHAOS",
        title="LOUD. CLEAR. COMMANDING.",
        subtitle="Aggressive alarms and voice prompts stay readable in noisy rooms.",
        badge="PRO VOICE CALLOUTS",
    ),
    "4_loop.png": CreativeText(
        eyebrow="BUILD DISCIPLINE",
        title="REACT ON THE BEEP",
        subtitle="Train explosive response when your heart rate is already up.",
        badge="SPEED UNDER STRESS",
    ),
    "5_ipad_setup.png": CreativeText(
        eyebrow="COACH MODE",
        title="RUN THE WHOLE ROOM",
        subtitle="Big-screen controls make partner and class drills easy to manage.",
        badge="IPAD-READY",
    ),
    "6_ipad_running.png": CreativeText(
        eyebrow="VISIBLE AT DISTANCE",
        title="SEE IT ACROSS THE MAT",
        subtitle="High-contrast timer views stay legible from the floor, bag, or line.",
        badge="NO SQUINTING",
    ),
    "7_ipad_stopped.png": CreativeText(
        eyebrow="BETWEEN ROUNDS",
        title="RESET. ADJUST. GO AGAIN.",
        subtitle="Change settings in seconds and get right back to work.",
        badge="ZERO FRICTION",
    ),
}

# Fixed SOURCE_MAP to avoid nested compositions.
SOURCE_MAP: Dict[str, str] = {
    "1_setup.png": "1_setup.png",
    "2_active.png": "2_active.png",
    "3_voice.png": "3_voice.png",
    "4_loop.png": "4_loop.png",
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


def _mix_color(start: Color, end: Color, ratio: float) -> Color:
    return tuple(
        int(round(start[idx] + ((end[idx] - start[idx]) * ratio)))
        for idx in range(3)
    )


def _wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join([*current, word]).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and (bbox[2] - bbox[0]) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        lines.append(" ".join(current))
    return lines


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    *,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: Color,
    line_spacing: int,
) -> int:
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, current_y), line, font=font)
        current_y = bbox[3] + line_spacing
    return current_y


def _resolve_source_path(screenshots_dir: Path, filename: str) -> Path:
    def candidate_matches_device(path: Path) -> bool:
        if not path.is_file():
            return False
        width, _height = Image.open(path).size
        is_ipad = filename.startswith(("5_", "6_", "7_"))
        return width >= 1600 if is_ipad else width < 1600

    candidates = [screenshots_dir / "originals" / filename]

    backup_root = screenshots_dir / "_backup"
    if backup_root.is_dir():
        for backup_dir in sorted(path for path in backup_root.iterdir() if path.is_dir()):
            candidates.append(backup_dir / filename)

    candidates.append(screenshots_dir / filename)

    for candidate in candidates:
        if candidate_matches_device(candidate):
            return candidate

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"Source screenshot not found for {filename} in {screenshots_dir}")


def _render_one(source: Image.Image, text: CreativeText) -> Image.Image:
    w, h = source.size
    base = Image.new("RGBA", (w, h), (9, 11, 16, 255))

    background = ImageDraw.Draw(base)
    top_color = (15, 18, 26)
    bottom_color = (29, 10, 13)
    for y in range(h):
        ratio = y / max(1, h - 1)
        background.line([(0, y), (w, y)], fill=_mix_color(top_color, bottom_color, ratio))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = ImageDraw.Draw(overlay)
    glow.ellipse(
        (
            int(w * 0.42),
            int(h * -0.02),
            int(w * 1.12),
            int(h * 0.52),
        ),
        fill=(235, 72, 50, 62),
    )
    glow.ellipse(
        (
            int(w * -0.18),
            int(h * 0.56),
            int(w * 0.62),
            int(h * 1.18),
        ),
        fill=(255, 122, 69, 28),
    )

    grid_color = (255, 255, 255, 14)
    grid_step = max(40, int(min(w, h) * 0.055))
    for x in range(grid_step, w, grid_step):
        glow.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y in range(grid_step, h, grid_step):
        glow.line([(0, y), (w, y)], fill=grid_color, width=1)

    glow.rounded_rectangle(
        (int(w * 0.06), int(h * 0.05), int(w * 0.94), int(h * 0.056)),
        radius=4,
        fill=(229, 57, 53, 255),
    )
    base = Image.alpha_composite(base, overlay)

    draw = ImageDraw.Draw(base)
    content_left = int(w * 0.08)
    content_width = int(w * 0.8)

    eyebrow_font = _load_font(max(28, int(h * 0.014)), bold=True)
    title_font = _load_font(max(78, int(h * 0.05)), bold=True)
    subtitle_font = _load_font(max(32, int(h * 0.018)), bold=False)
    badge_font = _load_font(max(28, int(h * 0.014)), bold=True)

    current_y = int(h * 0.08)
    draw.text((content_left, current_y), text.eyebrow, font=eyebrow_font, fill=(255, 143, 107))
    current_y += int(h * 0.038)

    title_lines = _wrapped_lines(draw, text.title, title_font, content_width)
    current_y = _draw_multiline(
        draw,
        title_lines,
        x=content_left,
        y=current_y,
        font=title_font,
        fill=(248, 250, 252),
        line_spacing=max(6, int(h * 0.004)),
    )

    current_y += int(h * 0.006)
    subtitle_lines = _wrapped_lines(draw, text.subtitle, subtitle_font, content_width)
    current_y = _draw_multiline(
        draw,
        subtitle_lines,
        x=content_left,
        y=current_y,
        font=subtitle_font,
        fill=(203, 213, 225),
        line_spacing=max(4, int(h * 0.003)),
    )

    badge_bbox = draw.textbbox((0, 0), text.badge, font=badge_font)
    badge_width = (badge_bbox[2] - badge_bbox[0]) + 48
    badge_height = (badge_bbox[3] - badge_bbox[1]) + 26
    badge_y = current_y + int(h * 0.02)
    draw.rounded_rectangle(
        (content_left, badge_y, content_left + badge_width, badge_y + badge_height),
        radius=16,
        fill=(220, 38, 38),
    )
    draw.text((content_left + 24, badge_y + 10), text.badge, font=badge_font, fill=(255, 255, 255))

    panel_top = int(h * 0.34)
    panel_left = int(w * 0.05)
    panel_right = int(w * 0.95)
    panel_bottom = int(h * 0.965)
    panel_radius = max(28, int(w * 0.03))

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (panel_left + 10, panel_top + 18, panel_right + 4, panel_bottom + 12),
        radius=panel_radius,
        fill=(0, 0, 0, 120),
    )
    base = Image.alpha_composite(base, shadow)
    draw = ImageDraw.Draw(base)

    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=panel_radius,
        fill=(13, 16, 22),
        outline=(82, 35, 35),
        width=3,
    )

    inner_margin = int(w * 0.018)
    target_w = (panel_right - panel_left) - (inner_margin * 2)
    target_h = (panel_bottom - panel_top) - (inner_margin * 2)
    ui_frame = ImageOps.fit(
        source,
        (target_w, target_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.06),
    )

    mask = Image.new("L", (target_w, target_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, target_w, target_h),
        radius=max(20, int(panel_radius * 0.75)),
        fill=255,
    )
    base.paste(ui_frame, (panel_left + inner_margin, panel_top + inner_margin), mask)
    return base.convert("RGB")


def generate(repo_root: Path, locale: str) -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    written: list[str] = []

    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"Screenshots directory not found: {screenshots_dir}")

    # Backup logic
    backup_root = screenshots_dir / "_backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp
    source_files: dict[str, str] = {}
    
    for filename, text in CREATIVE_COPY.items():
        source_path = _resolve_source_path(screenshots_dir, SOURCE_MAP.get(filename, filename))
        source_files[filename] = str(source_path)

        # If target file exists, move to backup
        target = screenshots_dir / filename
        if target.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_dir / filename)

        source = Image.open(source_path).convert("RGB")
        out = _render_one(source, text)
        
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    report = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "locale": locale,
        "written_files": written,
        "source_files": source_files,
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
