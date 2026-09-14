"""Fleet assets: Dagster-style catalog + checks without Dagster+ spend."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "fleet_assets.py"


class FleetAssetsContractTest(unittest.TestCase):
    def test_script_exists(self) -> None:
        self.assertTrue(SCRIPT.is_file(), "scripts/fleet_assets.py must exist")

    def test_catalog_lists_core_assets_with_deps(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "catalog", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("assets", payload)
        keys = {a["key"] for a in payload["assets"]}
        for required in (
            "north_star",
            "wqtu_health",
            "executive_metrics",
            "post_publish_gate",
            "paywall_conversion",
        ):
            self.assertIn(required, keys)
        north = next(a for a in payload["assets"] if a["key"] == "north_star")
        self.assertIn("deps", north)
        self.assertTrue(isinstance(north["deps"], list))

    def test_check_fails_on_stale_generated_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "marketing" / "data"
            data.mkdir(parents=True)
            (data / "north_star.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2020-01-01T00:00:00Z",
                        "source": "test",
                        "north_star": {"wqtu": 0},
                    }
                ),
                encoding="utf-8",
            )
            # Minimal siblings so catalog resolve doesn't crash on missing optional
            for name in (
                "wqtu_health.json",
                "executive_metrics.json",
                "post_publish_gate.json",
                "paywall_conversion_report.json",
            ):
                (data / name).write_text(
                    json.dumps({"generated_at": "2020-01-01T00:00:00Z"}),
                    encoding="utf-8",
                )
            catalog = Path(tmp) / "marketing" / "data" / "fleet_asset_catalog.json"
            catalog.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "assets": [
                            {
                                "key": "north_star",
                                "path": "marketing/data/north_star.json",
                                "deps": [],
                                "checks": ["has_generated_at", "fresh_within_days"],
                                "freshness_days": 7,
                                "required_keys": ["generated_at", "north_star"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "check",
                    "--root",
                    tmp,
                    "--catalog",
                    str(catalog),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, "stale asset must fail checks")
            payload = json.loads(proc.stdout)
            self.assertFalse(payload["passed"])
            self.assertTrue(
                any(
                    c["check"] == "fresh_within_days" and not c["passed"]
                    for c in payload["results"]
                )
            )

    def test_check_passes_on_required_keys_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "marketing" / "data"
            data.mkdir(parents=True)
            (data / "north_star.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2099-01-01T00:00:00Z",
                        "source": "test",
                        "north_star": {"wqtu": 1},
                    }
                ),
                encoding="utf-8",
            )
            catalog = Path(tmp) / "catalog.json"
            catalog.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "assets": [
                            {
                                "key": "north_star",
                                "path": "marketing/data/north_star.json",
                                "deps": [],
                                "checks": ["has_generated_at", "required_keys"],
                                "required_keys": ["generated_at", "north_star", "source"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "check",
                    "--root",
                    tmp,
                    "--catalog",
                    str(catalog),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["passed"])


if __name__ == "__main__":
    unittest.main()
