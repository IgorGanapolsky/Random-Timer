import tempfile
import unittest
from pathlib import Path
from unittest import mock


class AttributionFeedbackTests(unittest.TestCase):
    def test_fetch_onboarding_funnel_uses_fallback_events(self):
        from scripts import attribution_feedback as af

        # First three calls are lifecycle events (all zero),
        # next three are fallback event queries.
        with mock.patch.object(
            af,
            "query_scalar",
            side_effect=[0, 0, 0, 129, 60, 32],
        ):
            funnel = af.fetch_onboarding_funnel("k", "p", 30)

        self.assertEqual(funnel["first_open"], 129)
        self.assertEqual(funnel["first_timer_configured"], 60)
        self.assertEqual(funnel["first_timer_completed"], 32)
        self.assertAlmostEqual(funnel["open_to_configured_rate"], 60 / 129, places=4)
        self.assertAlmostEqual(funnel["configured_to_completed_rate"], 32 / 60, places=4)
        self.assertAlmostEqual(funnel["open_to_completed_rate"], 32 / 129, places=4)

    def test_run_missing_credentials_still_writes_report(self):
        from scripts import attribution_feedback as af

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "posthog_api_key": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ):
                result = af.run(root, days=30, dry_run=False)

            self.assertEqual(result.get("status"), "skipped")
            report = root / "marketing" / "data" / "attribution-report.md"
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("No PostHog query data available", text)


if __name__ == "__main__":
    unittest.main()
