from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


def test_ios_appiconset_has_no_extra_or_missing_pngs() -> None:
    appiconset = Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset")
    contents = json.loads((appiconset / "Contents.json").read_text(encoding="utf-8"))
    referenced = {img["filename"] for img in contents.get("images", []) if img.get("filename")}
    existing = {path.name for path in appiconset.glob("*.png")}

    missing = sorted(referenced - existing)
    extras = sorted(existing - referenced)

    assert not missing, f"Missing icon files referenced by Contents.json: {missing}"
    assert not extras, f"Unassigned icon files should be removed: {extras}"


def test_ios_marketing_icon_is_1024x1024() -> None:
    icon = Image.open(
        "native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png"
    )
    assert icon.size == (1024, 1024), (
        f"iOS marketing icon must be 1024x1024, got {icon.size}"
    )
