from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import admob_metrics_snapshot as mod  # noqa: E402


class AdmobMetricsSnapshotTests(unittest.TestCase):
    def test_build_snapshot_all_pass(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(True, "ok")):
            payload = mod.build_snapshot(also_play_path=False, include_api=False, access_token=None)
        self.assertTrue(payload["app_ads"]["all_pass"])
        self.assertEqual(len(payload["app_ads"]["checks"]), 1)
        self.assertIsNone(payload["api"])
        self.assertIsNotNone(payload["rewarded_rollout"])
        self.assertFalse(payload["rewarded_rollout"]["ready_for_internal_flag_test"])

    def test_write_snapshot_creates_json(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(True, "ok")):
            payload = mod.build_snapshot(also_play_path=False, include_api=False, access_token=None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = mod.write_snapshot(root, payload)
            data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["source"], "admob_metrics_snapshot")
        self.assertTrue(data["app_ads"]["all_pass"])

    def test_exit_code_one_when_hosting_fails(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(False, "HTTP 404")):
            payload = mod.build_snapshot(also_play_path=False, include_api=False, access_token=None)
        self.assertFalse(payload["app_ads"]["all_pass"])

    def test_rewarded_rollout_ready_when_approved_and_hosting_pass(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(True, "ok")):
            payload = mod.build_snapshot(also_play_path=False, include_api=False, access_token=None)
        payload["api"] = {
            "skipped": False,
            "apps": [{"platform": "ANDROID", "appApprovalState": "APPROVED"}],
        }
        rollout = mod._rewarded_rollout_readiness(payload)
        self.assertTrue(rollout["ready_for_internal_flag_test"])
        self.assertFalse(rollout["ready_for_production_rewarded"])


if __name__ == "__main__":
    unittest.main()
