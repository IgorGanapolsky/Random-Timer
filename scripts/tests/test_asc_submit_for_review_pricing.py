import unittest
import contextlib
import io

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyPricingTests(unittest.TestCase):
    def test_verify_pricing_accepts_app_price_schedules(self):
        from scripts.asc.asc_submit_for_review import verify_pricing

        client = RouterClient(
            {
                ("GET", "/apps/app1/prices"): RuntimeError("404"),
                ("GET", "/apps/app1/appPriceSchedule"): RuntimeError("404"),
                ("GET", "/appPriceSchedules"): {"data": [{"id": "sched1", "type": "appPriceSchedules"}]},
                ("GET", "/appPriceSchedules/sched1/manualPrices"): {"data": [{"id": "mp1", "type": "appPrices"}]},
            }
        )
        verify_pricing(client, "app1")
        self.assertEqual(
            [c["path"] for c in client.calls],
            ["/apps/app1/prices", "/apps/app1/appPriceSchedule", "/appPriceSchedules", "/appPriceSchedules/sched1/manualPrices"],
        )

    def test_verify_pricing_falls_back_to_singular_schedule_endpoint(self):
        from scripts.asc.asc_submit_for_review import verify_pricing

        client = RouterClient(
            {
                ("GET", "/apps/app1/prices"): RuntimeError("404"),
                ("GET", "/apps/app1/appPriceSchedule"): {"data": {"id": "sched1", "type": "appPriceSchedules"}},
                ("GET", "/appPriceSchedules/sched1/manualPrices"): {"data": [{"id": "mp1", "type": "appPrices"}]},
            }
        )
        verify_pricing(client, "app1")
        self.assertEqual(
            [c["path"] for c in client.calls],
            ["/apps/app1/prices", "/apps/app1/appPriceSchedule", "/appPriceSchedules/sched1/manualPrices"],
        )

    def test_verify_pricing_creates_free_schedule_when_missing(self):
        from scripts.asc.asc_submit_for_review import verify_pricing

        client = RouterClient(
            {
                ("GET", "/appPriceSchedules"): {"data": []},
                ("GET", "/apps/app1/appPriceSchedule"): RuntimeError("404"),
                ("GET", "/apps/app1/prices"): RuntimeError("404"),
                (
                    "GET",
                    "/apps/app1/appPricePoints",
                ): {
                    "data": [
                        {"id": "pp1", "type": "appPricePoints", "attributes": {"customerPrice": "0.00"}},
                        {"id": "pp2", "type": "appPricePoints", "attributes": {"customerPrice": "0.99"}},
                    ]
                },
                ("POST", "/appPriceSchedules"): {"data": {"id": "sched1", "type": "appPriceSchedules"}},
                ("GET", "/appPriceSchedules/sched1"): {"data": {"id": "sched1", "type": "appPriceSchedules"}},
            }
        )

        with contextlib.redirect_stdout(io.StringIO()):
            verify_pricing(client, "app1")

        paths = [c["path"] for c in client.calls]
        self.assertIn("/appPriceSchedules", paths)
        self.assertIn("/apps/app1/appPricePoints", paths)
        self.assertIn("/appPriceSchedules/sched1", paths)
        post = next((c for c in client.calls if c["method"] == "POST" and c["path"] == "/appPriceSchedules"), None)
        self.assertIsNotNone(post)
        payload = (post or {}).get("payload") or {}
        included = payload.get("included") or []
        self.assertTrue(included and isinstance(included[0], dict))
        local_id = (included[0].get("id") or "")
        self.assertTrue(isinstance(local_id, str) and local_id.startswith("${") and local_id.endswith("}"))
        rel_id = (
            (((payload.get("data") or {}).get("relationships") or {}).get("manualPrices") or {}).get("data") or [{}]
        )[0].get("id")
        self.assertEqual(rel_id, local_id)


if __name__ == "__main__":
    unittest.main()
