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

    def test_generate_writes_report_and_renders_to_target_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo, size=(300, 600))

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

            # iPhone screenshots render to RESOLUTION_IPHONE
            out = Image.open(shots_dir / "1_setup.png")
            self.assertEqual(out.size, creatives.RESOLUTION_IPHONE)

            # iPad screenshots render to RESOLUTION_IPAD
            out_ipad = Image.open(shots_dir / "5_ipad_setup.png")
            self.assertEqual(out_ipad.size, creatives.RESOLUTION_IPAD)

    def test_generate_skips_missing_source(self):
        """Script skips missing sources instead of raising."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots_dir = self._seed_screenshots(repo)
            (shots_dir / "7_ipad_stopped.png").unlink()

            report = creatives.generate(repo, "en-US")

            # Should succeed but with one fewer file written
            self.assertEqual(
                len(report["written_files"]),
                len(creatives.CREATIVE_COPY) - 1,
            )


if __name__ == "__main__":
    unittest.main()
