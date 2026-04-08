"""stackoverflow_digest_tag_groups.txt must list at least one tag group."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG_FILE = ROOT / "marketing" / "data" / "stackoverflow_digest_tag_groups.txt"


def test_digest_tag_groups_has_active_lines() -> None:
    text = TAG_FILE.read_text(encoding="utf-8")
    active = [
        line.split("#", 1)[0].strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active, "expected at least one non-comment tag group line"
    assert any("swift" in g.lower() or "android" in g.lower() or "jetpack" in g.lower() for g in active)
