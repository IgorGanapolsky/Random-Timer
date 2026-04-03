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
        for idx, filename in enumerate(creatives.CREATIVE_COPY.keys(), start=1):
            img = Image.new("RGB", size, (10 * idx, 20 * idx, 30 * idx))
            img.save(shots_dir / filename, format="PNG")
        return shots_dir

    def test_generate_writes_report_and_preserves_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo, size=(300, 600))
            original_bytes = (shots_dir / "1_setup.png").read_bytes()

            report = creatives.generate(repo, "en-US")

            report_path = Path(report["report_path"])
            self.assertTrue(report_path.is_file())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["locale"], "en-US")
            self.assertEqual(len(payload["written_files"]), len(creatives.CREATIVE_COPY))

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

    def test_generate_fails_when_required_source_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo)
            (shots_dir / "7_ipad_stopped.png").unlink()

            with self.assertRaises(FileNotFoundError):
                creatives.generate(repo, "en-US")

    def test_generate_prefers_originals_before_current_files(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo, size=(300, 600))
            originals_dir = shots_dir / "originals"
            originals_dir.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (300, 600), (220, 30, 30)).save(originals_dir / "1_setup.png", format="PNG")

            report = creatives.generate(repo, "en-US")

            assert report["source_files"]["1_setup.png"].endswith("originals/1_setup.png")

    def test_generate_prefers_recovered_raw_iphone_sources_when_available(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._seed_screenshots(repo, size=(300, 600))
            raw_dir = repo / "native-ios" / "fastlane" / "screenshots" / "en-US" / "originals" / "_backup" / "20260317_085115"
            raw_dir.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (320, 640), (30, 220, 30)).save(raw_dir / "iphone_setup_raw.png", format="PNG")

            report = creatives.generate(repo, "en-US")

            assert report["source_files"]["1_setup.png"].endswith("iphone_setup_raw.png")


if __name__ == "__main__":
    unittest.main()
