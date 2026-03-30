#!/usr/bin/env python3
"""Tests for scripts/engagement_dashboard.py."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import engagement_dashboard


class TestEngagementDashboardImports(unittest.TestCase):
    """Verify that the module structure is correct."""

    def test_module_has_run_function(self):
        """The module exposes a run() callable."""
        self.assertTrue(callable(getattr(engagement_dashboard, "run", None)))

    def test_module_has_all_compute_functions(self):
        """All eight section compute functions exist."""
        expected = [
            "compute_onboarding_funnel",
            "compute_timer_interactions",
            "compute_abandon_reasons",
            "compute_alarm_engagement",
            "compute_paywall_funnel",
            "compute_review_funnel",
            "compute_settings_preferences",
            "compute_dau_trend",
        ]
        for fn_name in expected:
            self.assertTrue(
                callable(getattr(engagement_dashboard, fn_name, None)),
                f"Missing compute function: {fn_name}",
            )


class TestMissingCredentials(unittest.TestCase):
    """When PostHog credentials are absent, the script should write a skipped status."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_creds_writes_skipped_json(self):
        """With no POSTHOG env vars, run() writes a JSON file with status=skipped."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            result = engagement_dashboard.run(repo_root, days=7)

        self.assertEqual(result["status"], "skipped")
        self.assertIn("missing POSTHOG credentials", result.get("reason", ""))

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_creds_creates_output_file(self):
        """With no creds, the output JSON file is still created."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            engagement_dashboard.run(repo_root, days=7)

            output = repo_root / "marketing" / "data" / "engagement_dashboard.json"
            self.assertTrue(output.exists(), "Output file should be created even when skipped")

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
