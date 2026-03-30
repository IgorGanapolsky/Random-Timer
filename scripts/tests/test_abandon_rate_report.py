import json
import unittest
from io import StringIO
from unittest import mock


class AbandonRateReportTests(unittest.TestCase):
    def test_run_outputs_abandon_and_monetization_metrics(self):
        from scripts import abandon_rate_report as arr

        # Scalar call order: started, completed, unique_users,
        #   first_open, first_configured, first_completed,
        #   paywall_viewed, canonical_attempts, canonical_success,
        #   paywall_restore
        # (canonical_success > 0 so no fallback path)
        scalar_values = [100, 40, 30, 50, 30, 10, 12, 9, 3, 4]

        # Rows call order: abandon_reasons, screens, top_events, build_audience
        rows_values = [
            [["user_cancelled", "timer_controls", 20, 15], ["stale_restore", "state_restore", 10, 8]],
            [["Timer Setup", 120], ["Active Timer", 80]],
            [["timer_started", 100], ["timer_completed", 40]],
            [["live", 1000], ["dev", 250]],
        ]

        with mock.patch.dict(
            "os.environ",
            {"POSTHOG_PERSONAL_API_KEY": "phx_test", "POSTHOG_PROJECT_ID": "299775"},
            clear=True,
        ):
            with mock.patch.object(
                arr, "query_scalar", side_effect=scalar_values,
            ), mock.patch.object(
                arr, "query_rows", side_effect=rows_values,
            ):
                out = StringIO()
                with mock.patch("sys.stdout", new=out):
                    arr.run()

        payload = json.loads(out.getvalue())
        self.assertEqual(payload["abandon_metrics"]["timer_started_30d"], 100)
        self.assertEqual(payload["abandon_metrics"]["timer_completed_30d"], 40)
        self.assertIn("abandon_reasons", payload["abandon_metrics"])
        self.assertEqual(len(payload["abandon_metrics"]["abandon_reasons"]), 2)
        self.assertIn("onboarding_funnel_30d", payload)
        self.assertEqual(payload["onboarding_funnel_30d"]["first_open_users"], 50)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_success_30d"], 3)

    def test_run_falls_back_to_purchase_result_when_canonical_stream_absent(self):
        from scripts import abandon_rate_report as arr

        # Scalar call order: started, completed, unique_users,
        #   first_open, first_configured, first_completed,
        #   paywall_viewed, canonical_attempts=0, canonical_success=0,
        #   fallback_attempts, fallback_success,
        #   paywall_restore
        scalar_values = [100, 40, 30, 40, 20, 5, 12, 0, 0, 5, 2, 4]

        rows_values = [
            [],  # empty abandon reasons
            [["Timer Setup", 120], ["Active Timer", 80]],
            [["timer_started", 100], ["timer_completed", 40]],
            [["live", 1000], ["dev", 250]],
        ]

        with mock.patch.dict(
            "os.environ",
            {"POSTHOG_PERSONAL_API_KEY": "phx_test", "POSTHOG_PROJECT_ID": "299775"},
            clear=True,
        ):
            with mock.patch.object(
                arr, "query_scalar", side_effect=scalar_values,
            ), mock.patch.object(
                arr, "query_rows", side_effect=rows_values,
            ):
                out = StringIO()
                with mock.patch("sys.stdout", new=out):
                    arr.run()

        payload = json.loads(out.getvalue())
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_metrics_source"], "paywall_purchase_result_fallback")
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_success_30d"], 2)
        self.assertIn("onboarding_funnel_30d", payload)


if __name__ == "__main__":
    unittest.main()
