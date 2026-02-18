import unittest
import contextlib
import io


class _RouterClient:
    def __init__(self, routes):
        self._routes = routes
        self.calls = []

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
        key = (method, path)
        if key not in self._routes:
            raise RuntimeError(f"unhandled route {method} {path}")
        value = self._routes[key]
        if isinstance(value, Exception):
            raise value
        # Allow dynamic responses by call count.
        if callable(value):
            return value()
        return value


class AscSubmitForReviewVerifyPricingTests(unittest.TestCase):
    def test_verify_pricing_accepts_app_price_schedules(self):
        from scripts.asc_submit_for_review import verify_pricing

        client = _RouterClient(
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
        from scripts.asc_submit_for_review import verify_pricing

        client = _RouterClient(
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
        from scripts.asc_submit_for_review import verify_pricing

        get_after_create = {"n": 0}

        def _get_schedules():
            # First call: empty. Second call: present (after POST).
            get_after_create["n"] += 1
            if get_after_create["n"] == 1:
                return {"data": []}
            return {"data": [{"id": "sched1", "type": "appPriceSchedules"}]}

        client = _RouterClient(
            {
                ("GET", "/appPriceSchedules"): _get_schedules,
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
            }
        )

        with contextlib.redirect_stdout(io.StringIO()):
            verify_pricing(client, "app1")

        paths = [c["path"] for c in client.calls]
        self.assertIn("/appPriceSchedules", paths)
        self.assertIn("/apps/app1/appPricePoints", paths)
        self.assertIn("/appPriceSchedules", paths)
        post = next((c for c in client.calls if c["method"] == "POST" and c["path"] == "/appPriceSchedules"), None)
        self.assertIsNotNone(post, "expected verify_pricing() to POST /appPriceSchedules")
        # ASC enforces inline-created included entities to use a JSON:API local id with the '$' prefix.
        self.assertEqual(post["payload"]["included"][0]["id"], "$manualPrice0")
        self.assertEqual(post["payload"]["data"]["relationships"]["manualPrices"]["data"][0]["id"], "$manualPrice0")


if __name__ == "__main__":
    unittest.main()
