import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def run_report_with_mocked_posthog(report, scalar_rows, table_rows):
    scalar_results = iter(scalar_rows)
    table_results = iter(table_rows)

    def fake_posthog_query(_query: str, _api_key: str, _project_id: str, _errors):
        if "top_failure_reasons" in _query:
            return {"results": next(table_results)}
        if "failure_breakdown" in _query:
            return {"results": next(table_results)}
        if "product_funnel" in _query:
            return {"results": next(table_results)}
        if "product_catalog_failures" in _query:
            return {"results": next(table_results)}
        if "entry_point_funnel" in _query:
            return {"results": next(table_results)}
        if "settings_hotspots" in _query:
            return {"results": next(table_results)}
        return {"results": next(scalar_results)}

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        with mock.patch.dict(
            "os.environ",
            {"POSTHOG_PERSONAL_API_KEY": "phx", "POSTHOG_PROJECT_ID": "123"},
            clear=True,
        ), mock.patch.object(report, "posthog_query", side_effect=fake_posthog_query):
            return report.run(root, days=30)


class PaywallConversionReportTests(unittest.TestCase):
    def test_run_loads_repo_dotenv(self):
        from scripts import paywall_conversion_report as report

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(report, "load_repo_dotenv") as load_dotenv, mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "", "POSTHOG_PROJECT_ID": ""},
                clear=True,
            ):
                report.run(root, days=7)
            load_dotenv.assert_called_once_with(root)

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
            "failure_breakdown": [
                {
                    "platform": "ios",
                    "product_id": "com.iganapolsky.randomtimer.pro.monthly",
                    "reason": "user_cancelled",
                    "failures": 12,
                    "users": 8,
                },
            ],
            "product_funnel": [
                {
                    "platform": "ios",
                    "product_id": "com.iganapolsky.randomtimer.pro.monthly",
                    "offer_selects": 55,
                    "attempts": 21,
                    "successes": 3,
                    "select_to_attempt_rate": 0.3818,
                    "attempt_to_success_rate": 0.1429,
                },
            ],
            "product_catalog_failures": [
                {
                    "platform": "ios",
                    "product_id": "com.iganapolsky.randomtimer.pro.monthly",
                    "failures": 5,
                    "users": 3,
                },
            ],
            "entry_points": [
                {"entry_point": "setup_upgrade_cta", "views": 70, "attempts": 15, "successes": 2},
                {"entry_point": "unknown", "views": 25, "attempts": 0, "successes": 0},
            ],
            "leaky_entry_points": [
                {"entry_point": "unknown", "views": 25, "attempts": 0, "successes": 0},
            ],
            "settings_hotspots": [
                {"setting_name": "voice_callouts_enabled", "changes": 42, "users": 18},
            ],
            "data_quality_warnings": [
                "unknown paywall entry_point is still receiving meaningful traffic",
            ],
        }

        markdown = report.build_markdown(payload)

        self.assertIn("Paywall Conversion Report", markdown)
        self.assertIn("View -> Offer Select", markdown)
        self.assertIn("user_cancelled", markdown)
        self.assertIn("Failure Breakdown", markdown)
        self.assertIn("Product Funnel", markdown)
        self.assertIn("Product Catalog Failures", markdown)
        self.assertIn("com.iganapolsky.randomtimer.pro.monthly", markdown)
        self.assertIn("setup_upgrade_cta", markdown)
        self.assertIn("Leaky Entry Points", markdown)
        self.assertIn("voice_callouts_enabled", markdown)
        self.assertIn("Data Quality Warnings", markdown)

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

        result = run_report_with_mocked_posthog(
            report,
            [
                [[120]],  # views
                [[60]],   # offer selects
                [[24]],   # attempts
                [[6]],    # successes
            ],
            [
                [["user_cancelled", 10], ["network_error", 5]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", "user_cancelled", 10, 8]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", 42, 17, 4]],
                [],
                [["setup_upgrade_cta", 80, 16, 4], ["sound_gate", 40, 8, 2]],
                [["voice_callouts_enabled", 31, 14], ["repeat_enabled", 15, 9]],
            ],
        )

        self.assertEqual("ok", result["status"])
        self.assertEqual(120, result["funnel"]["views"])
        self.assertEqual(6, result["funnel"]["purchase_successes"])
        self.assertAlmostEqual(0.5, result["funnel"]["view_to_select_rate"], places=4)
        self.assertEqual("user_cancelled", result["top_failure_reasons"][0]["reason"])
        self.assertEqual("ios", result["failure_breakdown"][0]["platform"])
        self.assertEqual(17, result["product_funnel"][0]["attempts"])
        self.assertEqual("voice_callouts_enabled", result["settings_hotspots"][0]["setting_name"])
        self.assertEqual([], result["leaky_entry_points"])
        self.assertEqual([], result["data_quality_warnings"])

    def test_run_flags_entry_points_with_views_but_zero_attempts(self):
        from scripts import paywall_conversion_report as report

        result = run_report_with_mocked_posthog(
            report,
            [
                [[120]],
                [[60]],
                [[24]],
                [[6]],
            ],
            [
                [["user_cancelled", 10]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", "user_cancelled", 10, 8]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", 42, 17, 4]],
                [],
                [["setup_upgrade_cta", 90, 0, 0], ["sound_gate", 40, 8, 2]],
                [["voice_callouts_enabled", 31, 14]],
            ],
        )

        self.assertEqual("setup_upgrade_cta", result["leaky_entry_points"][0]["entry_point"])
        self.assertEqual(90, result["leaky_entry_points"][0]["views"])

    def test_run_flags_funnel_and_settings_data_quality_problems(self):
        from scripts import paywall_conversion_report as report

        result = run_report_with_mocked_posthog(
            report,
            [
                [[120]],
                [[60]],
                [[85]],
                [[1]],
            ],
            [
                [["user_cancelled", 10]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", "user_cancelled", 10, 8]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", 42, 17, 0]],
                [["ios", "com.iganapolsky.randomtimer.pro.monthly", 11, 7]],
                [["unknown", 159, 0, 0], ["sound_gate", 68, 44, 1]],
                [["unknown", 34847, 601]],
            ],
        )

        self.assertIn("purchase_attempts exceed offer_selects", result["data_quality_warnings"][0])
        self.assertTrue(
            any("unknown paywall entry_point" in warning for warning in result["data_quality_warnings"])
        )
        self.assertTrue(
            any("settings_changed is still dominated by unknown" in warning for warning in result["data_quality_warnings"])
        )
        self.assertTrue(
            any("purchase failures are dominated by user_cancelled" in warning for warning in result["data_quality_warnings"])
        )
        self.assertTrue(
            any("product catalog lookup failures" in warning for warning in result["data_quality_warnings"])
        )


if __name__ == "__main__":
    unittest.main()
