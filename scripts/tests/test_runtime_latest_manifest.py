"""Guardrails for content/pro_audio/runtime/latest.json delivery contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "content" / "pro_audio" / "runtime" / "latest.json"


class RuntimeLatestManifestTests(unittest.TestCase):
    def test_no_remote_sound_assets_sound_arsenal_uses_bundled_mp3s(self) -> None:
        data = json.loads(LATEST.read_text(encoding="utf-8"))
        kinds = [a["kind"] for a in data.get("assets", [])]
        self.assertNotIn(
            "sound",
            kinds,
            "Sound Arsenal must play from app-bundled raw/Resources; remote pack "
            "previously shipped 20KB placeholder MP3s for most Pro sounds.",
        )
        self.assertIn(
            "voice",
            kinds,
            "Voice callouts should remain in the remote pack for Pro updates.",
        )


if __name__ == "__main__":
    unittest.main()
