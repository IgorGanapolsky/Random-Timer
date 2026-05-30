from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import post_publish_revenue_gate as gate  # noqa: E402
from scripts import verify_public_store_versions as store_verify  # noqa: E402


class PostPublishRevenueGateTests(unittest.TestCase):
    def test_build_report_pass_when_stores_match(self):
        results = [
            store_verify.StoreVersionResult(
                platform="ios",
                passed=True,
                status="PUBLIC",
                url="https://example.com/ios",
                expected_version="1.3.43",
                observed_version="1.3.43",
                details="ok",
            ),
            store_verify.StoreVersionResult(
                platform="android",
                passed=True,
                status="PUBLIC",
                url="https://example.com/android",
                expected_version="1.3.43",
                observed_version="1.3.43",
                details="ok",
            ),
        ]

        with patch.object(
            store_verify,
            "resolve_expected_versions",
            return_value=("1.3.43", "1.3.43", "github_latest_release"),
        ), patch.object(store_verify, "poll_until_public", return_value=results):
            with tempfile.TemporaryDirectory() as tmp:
                report = gate.build_report(repo_root=Path(tmp), platform="both", timeout=5)

        self.assertTrue(report["store_public_pass"])
        self.assertEqual(len(report["stores"]), 2)

    def test_main_exits_zero_when_pass(self):
        with patch.object(
            gate,
            "build_report",
            return_value={"store_public_pass": True, "stores": []},
        ):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "gate.json"
                with patch(
                    "sys.argv",
                    [
                        "post_publish_revenue_gate.py",
                        "--json-out",
                        str(out),
                        "--repo-root",
                        tmp,
                    ],
                ):
                    self.assertEqual(gate.main(), 0)
                self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["store_public_pass"])


if __name__ == "__main__":
    unittest.main()
