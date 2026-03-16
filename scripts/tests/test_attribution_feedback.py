import tempfile
import json
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

    def test_run_preserves_previous_content_feedback_when_queries_degrade(self):
        from scripts import attribution_feedback as af

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content_path = root / "marketing" / "data" / "content_feedback.json"
            content_path.parent.mkdir(parents=True, exist_ok=True)
            content_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-03-15T10:00:00+00:00",
                        "status": "ok",
                        "onboarding_funnel": {
                            "first_open": 20,
                            "first_timer_configured": 10,
                            "first_timer_completed": 5,
                            "open_to_completed_rate": 0.25,
                        },
                        "top_campaigns_by_activation": [{"campaign": "asa_brand", "activation_rate": 0.5}],
                    }
                ),
                encoding="utf-8",
            )
            keyword_path = root / "marketing" / "keywords" / "posthog_feedback.json"
            keyword_path.parent.mkdir(parents=True, exist_ok=True)
            keyword_path.write_text(
                json.dumps({"generated_at": "2026-03-15T10:00:00+00:00", "keyword_installs": {"hiit": 3}}),
                encoding="utf-8",
            )
            report = root / "marketing" / "data" / "attribution-report.md"
            report.write_text("# Attribution Feedback Report\n\nold\n", encoding="utf-8")

            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ), mock.patch.object(af, "fetch_utm_attribution", side_effect=lambda *_args, **_kwargs: af.QUERY_ERRORS.append("http_504") or []), mock.patch.object(
                af, "fetch_onboarding_funnel", return_value={"first_open": 0, "first_timer_configured": 0, "first_timer_completed": 0}
            ), mock.patch.object(
                af, "fetch_campaign_installs", return_value=[]
            ):
                result = af.run(root, days=30, dry_run=False)

            self.assertEqual(result["status"], "degraded")
            self.assertTrue(result["preserved_previous_metrics"])
            payload = json.loads(content_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["onboarding_funnel"]["first_open"], 20)
            self.assertTrue(payload["data_quality"]["is_stale"])
            self.assertEqual(payload["data_quality"]["last_good_generated_at"], "2026-03-15T10:00:00+00:00")
            self.assertEqual(report.read_text(encoding="utf-8"), "# Attribution Feedback Report\n\nold\n")


if __name__ == "__main__":
    unittest.main()
