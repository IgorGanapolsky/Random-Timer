import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts import generate_ios_store_creatives as creatives


class GenerateIosStoreCreativesTests(unittest.TestCase):
    def _seed_screenshots(self, root: Path, size: tuple[int, int] = (300, 600)) -> Path:
        shots_dir = root / "native-ios" / "fastlane" / "screenshots" / "en-US"
        shots_dir.mkdir(parents=True, exist_ok=True)
        originals_dir = shots_dir / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)
        for idx, spec in enumerate(creatives.CREATIVE_SPECS.values(), start=1):
            img = Image.new("RGB", size, (10 * idx, 20 * idx, 30 * idx))
            img.save(originals_dir / spec.source, format="PNG")
        for idx, filename in enumerate(creatives.CREATIVE_SPECS.keys(), start=1):
            img = Image.new("RGB", size, (5 * idx, 9 * idx, 13 * idx))
            img.save(shots_dir / filename, format="PNG")
        return shots_dir

    def test_generate_writes_report_and_preserves_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo, size=(300, 600))
            originals_dir = shots_dir / "originals"
            original_bytes = (shots_dir / "1_setup.png").read_bytes()
            raw_bytes = (originals_dir / "iphone_setup_raw.png").read_bytes()

            report = creatives.generate(repo, "en-US")

            report_path = Path(report["report_path"])
            self.assertTrue(report_path.is_file())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["locale"], "en-US")
            self.assertEqual(payload["source_dir"], str(originals_dir))
            self.assertEqual(len(payload["written_files"]), len(creatives.CREATIVE_SPECS))

            backup_root = shots_dir / "_backup"
            backup_dirs = sorted(backup_root.iterdir())
            self.assertEqual(len(backup_dirs), 1)
            backup_dir = backup_dirs[0]
            self.assertEqual(payload["backup_dir"], str(backup_dir))
            self.assertTrue(backup_dir.is_dir())
            self.assertTrue((backup_dir / "1_setup.png").is_file())

            out = Image.open(shots_dir / "1_setup.png")
            self.assertEqual(out.size, (300, 600))
            self.assertNotEqual(original_bytes, (shots_dir / "1_setup.png").read_bytes())
            self.assertEqual(raw_bytes, (originals_dir / "iphone_setup_raw.png").read_bytes())

    def test_generate_fails_when_required_source_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo)
            (shots_dir / "originals" / "ipad_sound_raw.png").unlink()

            with self.assertRaises(FileNotFoundError):
                creatives.generate(repo, "en-US")


if __name__ == "__main__":
    unittest.main()
