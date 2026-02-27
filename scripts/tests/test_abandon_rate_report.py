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
        purchase_success_query = scalar_mock.call_args_list[5].args[0]
        self.assertEqual(payload["abandon_metrics"]["timer_started_30d"], 100)
        self.assertEqual(payload["abandon_metrics"]["timer_completed_30d"], 40)
        self.assertEqual(payload["abandon_metrics"]["abandon_rate_percent"], 60.0)
        self.assertEqual(payload["monetization_metrics"]["paywall_viewed_30d"], 12)
        self.assertEqual(payload["monetization_metrics"]["paywall_purchase_success_30d"], 3)
        self.assertEqual(payload["monetization_metrics"]["paywall_view_to_purchase_rate_percent"], 25.0)
        self.assertEqual(payload["build_audience_breakdown_30d"][0]["build_audience"], "live")
        self.assertIn("properties.result", purchase_success_query)
        self.assertIn("toString(properties.success)", purchase_success_query)


if __name__ == "__main__":
    unittest.main()
