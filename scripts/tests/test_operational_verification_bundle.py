from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from scripts import operational_verification_bundle as bundle


class OperationalVerificationBundleTests(unittest.TestCase):
    def test_check_result_to_dict_includes_semantics(self):
        check = bundle.CheckResult(
            check_id="github_latest_release",
            tier="repo",
            status="pass",
            metric_field_id="github_release_tag_semver_v1",
            ground_truth=False,
            semantics="Latest GitHub Release tag (not store ledger).",
            command="gh release view --json tagName",
            evidence={"tag": "v1.3.41", "version": "1.3.41"},
        )
        payload = check.to_dict()
        self.assertEqual(payload["check_id"], "github_latest_release")
        self.assertFalse(payload["ground_truth"])
        self.assertIn("semantics", payload)

    def test_staleness_flags_old_snapshot(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=50)).strftime("%Y-%m-%dT%H:%M:%SZ")
        stale, age_h = bundle.snapshot_age_hours(old, max_age_hours=24.0)
        self.assertTrue(stale)
        self.assertGreater(age_h, 24.0)

    def test_staleness_accepts_fresh_snapshot(self):
        fresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        stale, _ = bundle.snapshot_age_hours(fresh, max_age_hours=24.0)
        self.assertFalse(stale)

    def test_bundle_schema_has_required_top_level_keys(self):
        required = {
            "generated_at",
            "bundle_id",
            "reliability_contract_doc",
            "summary",
            "checks",
            "revenue_goal",
            "definitions",
        }
        with patch.object(bundle, "run_all_checks", return_value=[]):
            with patch.object(bundle, "build_revenue_goal_section", return_value={}):
                payload = bundle.build_bundle(bundle.REPO_ROOT)
        self.assertTrue(required.issubset(payload.keys()))
        self.assertEqual(payload["bundle_id"], bundle.BUNDLE_ID)

    def test_summary_counts_statuses(self):
        checks = [
            bundle.CheckResult("a", "repo", "pass", "m1", False, "", "", {}),
            bundle.CheckResult("b", "repo", "fail", "m2", False, "", "", {}),
            bundle.CheckResult("c", "repo", "skip", "m3", False, "", "", {}),
            bundle.CheckResult("d", "tier2", "advisory_fail", "m4", False, "", "", {}),
        ]
        summary = bundle.summarize_checks(checks)
        self.assertEqual(summary["pass"], 1)
        self.assertEqual(summary["fail"], 1)
        self.assertEqual(summary["skip"], 1)
        self.assertEqual(summary["advisory_fail"], 1)


if __name__ == "__main__":
    unittest.main()
