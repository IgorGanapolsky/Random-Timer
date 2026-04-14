import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class PaywallConversionReportTests(unittest.TestCase):
    def test_build_markdown_includes_funnel_and_failure_reasons(self):
        from scripts import paywall_conversion_report as report

        payload = {
            "window_days": 30,
            "funnel": {
                "views": 100,
                "offer_selects": 55,
                "purchase_attempts": 21,
                "purchase_successes": 3,
                "view_to_select_rate": 0.55,
                "select_to_attempt_rate": 0.3818,
                "attempt_to_success_rate": 0.1429,
            },
            "top_failure_reasons": [
                {"reason": "user_cancelled", "count": 12},
                {"reason": "network_error", "count": 4},
            ],
            "entry_points": [
                {"entry_point": "setup_upgrade_cta", "views": 70, "attempts": 15, "successes": 2},
            ],
        }

        markdown = report.build_markdown(payload)

        self.assertIn("Paywall Conversion Report", markdown)
        self.assertIn("View -> Offer Select", markdown)
        self.assertIn("user_cancelled", markdown)
        self.assertIn("setup_upgrade_cta", markdown)

    def test_run_writes_reports_when_credentials_missing(self):
        from scripts import paywall_conversion_report as report

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ):
                result = report.run(root, days=14)

            self.assertEqual("skipped", result["status"])
            json_path = root / "marketing" / "data" / "paywall_conversion_report.json"
            md_path = root / "marketing" / "data" / "paywall_conversion_report.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual("skipped", payload["status"])
            self.assertIn("missing POSTHOG", payload["reason"])

    def test_run_populates_funnel_from_posthog_queries(self):
        from scripts import paywall_conversion_report as report

        scalar_results = iter(
            [
                [[120]],  # views
                [[60]],   # offer selects
                [[24]],   # attempts
                [[6]],    # successes
            ]
        )
        table_results = iter(
            [
                [["user_cancelled", 10], ["network_error", 3]],
                [["setup_upgrade_cta", 80, 16, 4], ["sound_gate", 40, 8, 2]],
            ]
        )

        def fake_posthog_query(_query: str, _api_key: str, _project_id: str, _errors):
            if "top_failure_reasons" in _query:
                return {"results": next(table_results)}
            if "entry_point_funnel" in _query:
                return {"results": next(table_results)}
            return {"results": next(scalar_results)}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "phx", "POSTHOG_PROJECT_ID": "123"},
                clear=True,
            ), mock.patch.object(report, "posthog_query", side_effect=fake_posthog_query):
                result = report.run(root, days=30)

            self.assertEqual("ok", result["status"])
            self.assertEqual(120, result["funnel"]["views"])
            self.assertEqual(6, result["funnel"]["purchase_successes"])
            self.assertAlmostEqual(0.5, result["funnel"]["view_to_select_rate"], places=4)
            self.assertEqual("user_cancelled", result["top_failure_reasons"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
