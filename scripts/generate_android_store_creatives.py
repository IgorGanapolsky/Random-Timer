#!/usr/bin/env python3
"""Generate Google Play Android creatives from canonical app assets."""

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

SCREENSHOT_MAP = {
    "1_setup.png": "android-setup.png",
    "2_active.png": "android-active.png",
    "3_settings.png": "android-settings.png",
    "4_loop.png": "android-loop.png",
}

PLAY_SCREENSHOT_SIZE = (1344, 2992)
FEATURE_GRAPHIC_SIZE = (1024, 500)


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


def _render_play_screenshot(source: Image.Image) -> Image.Image:
    return ImageOps.fit(
        source.convert("RGB"),
        PLAY_SCREENSHOT_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.06),
    )


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
        (12, 12, icon_size + 6, icon_size + 6),
        radius=32,
        fill=(0, 0, 0, 110),
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

    card_one = _feature_card(screenshots[0], size=(188, 408), radius=24)
    card_two = _feature_card(screenshots[1], size=(188, 408), radius=24)
    card_three = _feature_card(screenshots[2], size=(188, 408), radius=24)

    shadow = Image.new("RGBA", FEATURE_GRAPHIC_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    for x, y in ((720, 56), (828, 86), (612, 112)):
        shadow_draw.rounded_rectangle((x + 10, y + 16, x + 198, y + 424), radius=28, fill=(0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.alpha_composite(card_one, (720, 56))
    canvas.alpha_composite(card_two, (828, 86))
    canvas.alpha_composite(card_three, (612, 112))

    return canvas.convert("RGB")


def generate(repo_root: Path) -> Dict[str, object]:
    raw_root = repo_root / "screenshots"
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

    backup_root = screenshots_dir / "_backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    for filename, raw_name in SCREENSHOT_MAP.items():
        raw_path = raw_root / raw_name
        if not raw_path.is_file():
            raise FileNotFoundError(f"Raw Android screenshot missing: {raw_path}")
        target_path = screenshots_dir / filename
        if target_path.is_file():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, backup_dir / filename)

        rendered = _render_play_screenshot(Image.open(raw_path))
        _write_png(target_path, rendered)
        rendered_screenshots.append(rendered)
        written_files.append(str(target_path))

    feature_graphic_path.parent.mkdir(parents=True, exist_ok=True)
    feature_graphic = _render_feature_graphic(icon_image, rendered_screenshots[:3])
    _write_png(feature_graphic_path, feature_graphic)
    written_files.append(str(feature_graphic_path))

    report = {
        "status": "success",
        "generated_at": _now_iso(),
        "source_icon": str(source_icon_path),
        "raw_screenshots": {name: str(raw_root / raw_name) for name, raw_name in SCREENSHOT_MAP.items()},
        "written_files": written_files,
        "backup_dir": str(backup_dir) if backup_dir.is_dir() else None,
    }
    report_path = metadata_root / "generation-report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Android Google Play creative assets.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    report = generate(Path(args.repo_root).resolve())
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
