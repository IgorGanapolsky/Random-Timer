from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from scripts import sync_ios_icon_from_source as syncer


def test_parse_pixels() -> None:
    assert syncer._parse_pixels({"size": "20x20", "scale": "3x"}) == 60
    assert syncer._parse_pixels({"size": "83.5x83.5", "scale": "2x"}) == 167
    assert syncer._parse_pixels({"size": "1024x1024", "scale": "1x"}) == 1024


def test_run_generates_files(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (512, 512), color=(1, 2, 3, 255)).save(source)

    appiconset = tmp_path / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)
    contents = {
        "images": [
            {"size": "20x20", "scale": "2x", "filename": "icon-20@2x.png"},
            {"size": "60x60", "scale": "3x", "filename": "icon-60@3x.png"},
            {"size": "1024x1024", "scale": "1x", "filename": "icon-1024.png"},
        ],
        "info": {"version": 1, "author": "xcode"},
    }
    (appiconset / "Contents.json").write_text(json.dumps(contents), encoding="utf-8")

    result = syncer.run(source, appiconset)
    assert result["status"] == "ok"
    assert result["written_count"] == 3

    generated = {
        "icon-20@2x.png": (40, 40),
        "icon-60@3x.png": (180, 180),
        "icon-1024.png": (1024, 1024),
    }
    for name, expected_size in generated.items():
        path = appiconset / name
        assert path.exists()
        img = Image.open(path)
        assert img.size == expected_size
