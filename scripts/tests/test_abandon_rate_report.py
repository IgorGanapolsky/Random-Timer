import json
import unittest
from io import StringIO
from unittest import mock


class AbandonRateReportTests(unittest.TestCase):
    def test_run_outputs_abandon_and_monetization_metrics(self):
        from scripts import abandon_rate_report as arr

        with mock.patch.dict(
            "os.environ",
            {
                "POSTHOG_PERSONAL_API_KEY": "phx_test",
                "POSTHOG_PROJECT_ID": "299775",
            },
            clear=True,
        ):
            with mock.patch.object(
                arr,
                "query_scalar",
                side_effect=[100, 40, 30, 12, 9, 3, 4],
            ) as scalar_mock, mock.patch.object(
                arr,
                "query_rows",
                side_effect=[
                    [["Timer Setup", 120], ["Active Timer", 80]],
                    [["timer_started", 100], ["timer_completed", 40]],
                    [["live", 1000], ["dev", 250]],
                ],
            ):
                out = StringIO()
                with mock.patch("sys.stdout", new=out):
                    arr.run()

        payload = json.loads(out.getvalue())
        canonical_success_query = scalar_mock.call_args_list[5].args[0]
        issued_queries = "\n".join(call.args[0] for call in scalar_mock.call_args_list)
        self.assertEqual(payload["abandon_metrics"]["timer_started_30d"], 100)
        self.assertEqual(payload["abandon_metrics"]["timer_completed_30d"], 40)
        self.assertEqual(payload["abandon_metrics"]["abandon_rate_percent"], 60.0)
        self.assertEqual(payload["monetization_metrics"]["paywall_viewed_30d"], 12)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_success_30d"], 3)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_metrics_source"], "canonical_events")
        self.assertEqual(payload["monetization_metrics"]["paywall_view_to_purchase_rate_percent"], 25.0)
        self.assertEqual(payload["build_audience_breakdown_30d"][0]["build_audience"], "live")
        self.assertIn("event = 'paywall_purchase_success'", canonical_success_query)
        self.assertNotIn("event = 'paywall_purchase_result'", issued_queries)

    def test_run_falls_back_to_purchase_result_when_canonical_stream_absent(self):
        from scripts import abandon_rate_report as arr

        with mock.patch.dict(
            "os.environ",
            {
                "POSTHOG_PERSONAL_API_KEY": "phx_test",
                "POSTHOG_PROJECT_ID": "299775",
            },
            clear=True,
        ):
            with mock.patch.object(
                arr,
                "query_scalar",
                side_effect=[100, 40, 30, 12, 0, 0, 5, 2, 4],
            ) as scalar_mock, mock.patch.object(
                arr,
                "query_rows",
                side_effect=[
                    [["Timer Setup", 120], ["Active Timer", 80]],
                    [["timer_started", 100], ["timer_completed", 40]],
                    [["live", 1000], ["dev", 250]],
                ],
            ):
                out = StringIO()
                with mock.patch("sys.stdout", new=out):
                    arr.run()

        payload = json.loads(out.getvalue())
        fallback_success_query = scalar_mock.call_args_list[7].args[0]
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_attempts_30d"], 5)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_success_30d"], 2)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_metrics_source"], "paywall_purchase_result_fallback")
        self.assertIn("properties.result", fallback_success_query)
        self.assertIn("toString(properties.success)", fallback_success_query)


if __name__ == "__main__":
    unittest.main()
