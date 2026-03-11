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

            # First run — writes to device subdirs
            report = creatives.generate(repo, "en-US")

            report_path = Path(report["report_path"])
            self.assertTrue(report_path.is_file())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["locale"], "en-US")
            self.assertEqual(len(payload["written_files"]), len(creatives.CREATIVE_COPY))

            # Second run — existing targets get backed up
            report2 = creatives.generate(repo, "en-US")
            payload2 = json.loads(Path(report2["report_path"]).read_text(encoding="utf-8"))

            backup_root = shots_dir / "_backup"
            self.assertTrue(backup_root.is_dir(), "Backup dir should exist after second run")
            backup_dirs = sorted(backup_root.iterdir())
            self.assertEqual(len(backup_dirs), 1)
            backup_dir = backup_dirs[0]
            self.assertEqual(payload2["backup_dir"], str(backup_dir))
            self.assertTrue(backup_dir.is_dir())
            self.assertTrue((backup_dir / "1_setup.png").is_file())

            iphone_dir = shots_dir / creatives.IPHONE_SUBDIR
            out = Image.open(iphone_dir / "1_setup.png")
            self.assertEqual(out.size, creatives.RESOLUTION_IPHONE)
            self.assertNotEqual(original_bytes, (iphone_dir / "1_setup.png").read_bytes())

    def test_generate_skips_when_source_missing(self):
        """Missing source files are warned and skipped, not treated as fatal."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo)
            (shots_dir / "7_ipad_stopped.png").unlink()

            report = creatives.generate(repo, "en-US")

            payload = json.loads(Path(report["report_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(payload["written_files"]), len(creatives.CREATIVE_COPY) - 1)
            written_names = [Path(p).name for p in payload["written_files"]]
            self.assertNotIn("7_ipad_stopped.png", written_names)


if __name__ == "__main__":
    unittest.main()
