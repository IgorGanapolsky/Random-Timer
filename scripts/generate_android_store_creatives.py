#!/usr/bin/env python3
"""Generate Google Play Android creatives with marketing overlays.

Matches the iOS creative pipeline: gradient backgrounds, marketing
headlines, device panel framing, badges. Ensures store listing parity.
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

PLAY_SCREENSHOT_SIZE = (1080, 2400)  # Standard Android phone (Pixel 7 class)
FEATURE_GRAPHIC_SIZE = (1024, 500)


@dataclass(frozen=True)
class CreativeSpec:
    eyebrow: str
    title: str
    subtitle: str
    badge: str
    centering: Tuple[float, float] = (0.5, 0.08)


CREATIVE_COPY: Dict[str, CreativeSpec] = {
    "1_setup.png": CreativeSpec(
        eyebrow="SET THE WINDOW",
        title="RANDOMIZE EVERY REP",
        subtitle="Choose the range. The app chooses the moment. Your job is to react.",
        badge="DRY FIRE \u2022 STRIKING \u2022 HIIT",
        centering=(0.5, 0.16),
    ),
    "2_active.png": CreativeSpec(
        eyebrow="KILL ANTICIPATION",
        title="NO COUNTDOWN TO CHEAT",
        subtitle="Unpredictable start cues stop rhythm gaming and force a real reaction.",
        badge="PURE REACTION WORK",
        centering=(0.5, 0.18),
    ),
    "3_settings.png": CreativeSpec(
        eyebrow="CUT THROUGH FATIGUE",
        title="VOICE CUES THAT PUSH BACK",
        subtitle="Sharp alarms and command cues keep pressure on when the round gets ugly.",
        badge="VOICE + SOUND ARSENAL",
        centering=(0.5, 0.42),
    ),
    "3_voice.png": CreativeSpec(
        eyebrow="COMMAND THE SESSION",
        title="HEAR IT. REACT.",
        subtitle="Timed voice callouts keep you sharp when fatigue clouds your focus.",
        badge="PRO VOICE ENGINE",
        centering=(0.5, 0.20),
    ),
    "4_loop.png": CreativeSpec(
        eyebrow="BETWEEN ROUNDS",
        title="RESET FAST. GO AGAIN.",
        subtitle="Pause, resume, and loop rounds without breaking the flow of the drill.",
        badge="ROUND CONTROL",
        centering=(0.5, 0.20),
    ),
}


@dataclass(frozen=True)
class FeatureGraphicCopy:
    eyebrow: str
    title: str
    subtitle: str


FEATURE_COPY = FeatureGraphicCopy(
    eyebrow="TRAIN REACTION, NOT RHYTHM",
    title="Random Tactical Timer",
    subtitle="Unpredictable cues for dry fire, combat sports, and interval drills.",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next Condensed Heavy.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
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


def _write_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


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


def _render_play_screenshot(source: Image.Image, spec: CreativeSpec) -> Image.Image:
    """Render a Play Store screenshot with marketing overlay matching iOS style."""
    w, h = PLAY_SCREENSHOT_SIZE
    base = Image.new("RGBA", (w, h), (9, 11, 16, 255))

    # Gradient background
    background = ImageDraw.Draw(base)
    top_color = (15, 18, 26)
    bottom_color = (29, 10, 13)
    for y in range(h):
        ratio = y / max(1, h - 1)
        background.line([(0, y), (w, y)], fill=_mix_color(top_color, bottom_color, ratio))

    # Glow overlays
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = ImageDraw.Draw(overlay)
    glow.ellipse(
        (int(w * 0.42), int(h * -0.02), int(w * 1.12), int(h * 0.52)),
        fill=(235, 72, 50, 62),
    )
    glow.ellipse(
        (int(w * -0.18), int(h * 0.56), int(w * 0.62), int(h * 1.18)),
        fill=(255, 122, 69, 28),
    )

    # Grid
    grid_color = (255, 255, 255, 14)
    grid_step = max(40, int(min(w, h) * 0.055))
    for x in range(grid_step, w, grid_step):
        glow.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y_pos in range(grid_step, h, grid_step):
        glow.line([(0, y_pos), (w, y_pos)], fill=grid_color, width=1)

    # Header bar
    glow.rounded_rectangle(
        (int(w * 0.06), int(h * 0.05), int(w * 0.94), int(h * 0.056)),
        radius=4,
        fill=(229, 57, 53, 255),
    )
    base = Image.alpha_composite(base, overlay)

    draw = ImageDraw.Draw(base)
    content_left = int(w * 0.08)
    content_width = int(w * 0.8)

    # Typography
    eyebrow_font = _load_font(max(24, int(h * 0.012)), bold=True)
    title_font = _load_font(max(64, int(h * 0.042)), bold=True)
    subtitle_font = _load_font(max(26, int(h * 0.015)), bold=False)
    badge_font = _load_font(max(22, int(h * 0.011)), bold=True)

    # Eyebrow
    current_y = int(h * 0.08)
    draw.text((content_left, current_y), spec.eyebrow, font=eyebrow_font, fill=(255, 143, 107))
    current_y += int(h * 0.035)

    # Title
    title_lines = _wrapped_lines(draw, spec.title, title_font, content_width)
    current_y = _draw_multiline(
        draw, title_lines, x=content_left, y=current_y,
        font=title_font, fill=(248, 250, 252),
        line_spacing=max(6, int(h * 0.004)),
    )

    # Subtitle
    current_y += int(h * 0.006)
    subtitle_lines = _wrapped_lines(draw, spec.subtitle, subtitle_font, content_width)
    current_y = _draw_multiline(
        draw, subtitle_lines, x=content_left, y=current_y,
        font=subtitle_font, fill=(203, 213, 225),
        line_spacing=max(4, int(h * 0.003)),
    )

    # Badge
    badge_bbox = draw.textbbox((0, 0), spec.badge, font=badge_font)
    badge_width = (badge_bbox[2] - badge_bbox[0]) + 48
    badge_height = (badge_bbox[3] - badge_bbox[1]) + 26
    badge_y = current_y + int(h * 0.018)
    draw.rounded_rectangle(
        (content_left, badge_y, content_left + badge_width, badge_y + badge_height),
        radius=16,
        fill=(220, 38, 38),
    )
    draw.text((content_left + 24, badge_y + 10), spec.badge, font=badge_font, fill=(255, 255, 255))

    # Device panel
    panel_top = int(h * 0.36)
    panel_left = int(w * 0.05)
    panel_right = int(w * 0.95)
    panel_bottom = int(h * 0.965)
    panel_radius = max(28, int(w * 0.03))

    # Panel shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (panel_left + 10, panel_top + 18, panel_right + 4, panel_bottom + 12),
        radius=panel_radius,
        fill=(0, 0, 0, 120),
    )
    base = Image.alpha_composite(base, shadow)
    draw = ImageDraw.Draw(base)

    # Panel border
    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=panel_radius,
        fill=(13, 16, 22),
        outline=(82, 35, 35),
        width=3,
    )

    # Fit source screenshot into panel
    inner_margin = int(w * 0.018)
    target_w = (panel_right - panel_left) - (inner_margin * 2)
    target_h = (panel_bottom - panel_top) - (inner_margin * 2)
    ui_frame = ImageOps.fit(
        source, (target_w, target_h),
        method=Image.Resampling.LANCZOS,
        centering=spec.centering,
    )
    mask = Image.new("L", (target_w, target_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, target_w, target_h),
        radius=max(20, int(panel_radius * 0.75)),
        fill=255,
    )
    base.paste(ui_frame, (panel_left + inner_margin, panel_top + inner_margin), mask)
    return base.convert("RGB")


def _feature_card(source: Image.Image, *, size: tuple[int, int], radius: int) -> Image.Image:
    fitted = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.05))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    card = Image.new("RGBA", size, (0, 0, 0, 0))
    card.paste(fitted, (0, 0), mask)
    return card


def _render_feature_graphic(icon: Image.Image, screenshots: list[Image.Image]) -> Image.Image:
    width, height = FEATURE_GRAPHIC_SIZE
    canvas = Image.new("RGBA", FEATURE_GRAPHIC_SIZE, (8, 12, 18, 255))
    draw = ImageDraw.Draw(canvas)

    top = (10, 16, 24)
    bottom = (92, 20, 18)
    for y in range(height):
        draw.line([(0, y), (width, y)], fill=_mix_color(top, bottom, y / max(1, height - 1)))

    glow = Image.new("RGBA", FEATURE_GRAPHIC_SIZE, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((540, -90, 1080, 360), fill=(243, 82, 45, 90))
    glow_draw.ellipse((-180, 250, 480, 760), fill=(255, 122, 69, 32))
    canvas = Image.alpha_composite(canvas, glow)

    eyebrow_font = _load_font(20, bold=True)
    title_font = _load_font(46, bold=True)
    subtitle_font = _load_font(22, bold=False)

    icon_size = 118
    icon_render = ImageOps.fit(icon.convert("RGB"), (icon_size, icon_size), method=Image.Resampling.LANCZOS)
    icon_mask = Image.new("L", (icon_size, icon_size), 0)
    ImageDraw.Draw(icon_mask).rounded_rectangle((0, 0, icon_size, icon_size), radius=28, fill=255)
    icon_shadow = Image.new("RGBA", (icon_size + 18, icon_size + 18), (0, 0, 0, 0))
    ImageDraw.Draw(icon_shadow).rounded_rectangle(
        (12, 12, icon_size + 6, icon_size + 6), radius=32, fill=(0, 0, 0, 110),
    )
    canvas.alpha_composite(icon_shadow, (54, 56))
    icon_rgba = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    icon_rgba.paste(icon_render, (0, 0), icon_mask)
    canvas.alpha_composite(icon_rgba, (48, 48))

    draw = ImageDraw.Draw(canvas)
    text_x = 192
    draw.text((text_x, 60), FEATURE_COPY.eyebrow, font=eyebrow_font, fill=(255, 153, 120))
    draw.text((text_x, 96), FEATURE_COPY.title, font=title_font, fill=(247, 250, 252))
    draw.text((text_x, 152), FEATURE_COPY.subtitle, font=subtitle_font, fill=(203, 213, 225))

    cards = [_feature_card(s, size=(188, 408), radius=24) for s in screenshots[:3]]
    shadow = Image.new("RGBA", FEATURE_GRAPHIC_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    for x, y in ((720, 56), (828, 86), (612, 112)):
        shadow_draw.rounded_rectangle((x + 10, y + 16, x + 198, y + 424), radius=28, fill=(0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, shadow)
    for (x, y), card in zip(((720, 56), (828, 86), (612, 112)), cards):
        canvas.alpha_composite(card, (x, y))

    return canvas.convert("RGB")


def generate(repo_root: Path) -> Dict[str, object]:
    metadata_root = repo_root / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "images"
    screenshots_dir = metadata_root / "phoneScreenshots"
    feature_graphic_path = metadata_root / "featureGraphic" / "feature-graphic.png"
    play_icon_path = metadata_root / "icon.png"
    source_icon_path = repo_root / "branding" / "app-icon-source.png"

    if not source_icon_path.is_file():
        raise FileNotFoundError(f"Canonical icon source missing: {source_icon_path}")

    raw_icon = Image.open(source_icon_path)
    icon_image = raw_icon.convert("RGB")
    if raw_icon.size == (1024, 1024):
        play_icon_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_icon_path, play_icon_path)
    else:
        icon_image = ImageOps.fit(icon_image, (1024, 1024), method=Image.Resampling.LANCZOS)
        _write_png(play_icon_path, icon_image)

    written_files: list[str] = [str(play_icon_path)]
    rendered_screenshots: list[Image.Image] = []

    # Backup existing screenshots
    backup_root = screenshots_dir / "_backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    for filename, spec in CREATIVE_COPY.items():
        source_path = screenshots_dir / filename
        if not source_path.is_file():
            print(f"Warning: source screenshot missing, skipping: {source_path}")
            continue

        # Backup original
        if source_path.is_file():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_dir / filename)

        raw_source = Image.open(source_path).convert("RGB")
        rendered = _render_play_screenshot(raw_source, spec)
        _write_png(source_path, rendered)
        rendered_screenshots.append(rendered)
        written_files.append(str(source_path))

    # Feature graphic
    feature_graphic_path.parent.mkdir(parents=True, exist_ok=True)
    feature_graphic = _render_feature_graphic(icon_image, rendered_screenshots[:3])
    _write_png(feature_graphic_path, feature_graphic)
    written_files.append(str(feature_graphic_path))

    report = {
        "status": "success",
        "generated_at": _now_iso(),
        "source_icon": str(source_icon_path),
        "written_files": written_files,
        "backup_dir": str(backup_dir) if backup_dir.is_dir() else None,
    }
    report_path = metadata_root / "generation-report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Android Google Play creative assets with marketing overlays.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    report = generate(Path(args.repo_root).resolve())
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
