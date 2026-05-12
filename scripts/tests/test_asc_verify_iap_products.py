from __future__ import annotations

import unittest

from scripts.asc import asc_verify_iap_products as verify


class _FakeClient:
    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []

    def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/apps":
            return {"data": [{"id": "app1", "attributes": {"bundleId": "com.example.app"}}]}
        if path == "/apps/app1/inAppPurchasesV2":
            return {
                "data": [
                    {
                        "id": "iap1",
                        "attributes": {
                            "productId": "com.example.app.pro",
                            "name": "Lifetime Pro",
                            "inAppPurchaseType": "NON_CONSUMABLE",
                            "state": "APPROVED",
                        },
                    }
                ]
            }
        if path == "/apps/app1/subscriptionGroups":
            return {"data": [{"id": "group1", "attributes": {"referenceName": "Pro"}}]}
        if path == "/subscriptionGroups/group1/subscriptions":
            return {
                "data": [
                    {
                        "id": "sub1",
                        "attributes": {
                            "productId": "com.example.app.pro.monthly",
                            "name": "Monthly Pro",
                            "state": "APPROVED",
                            "subscriptionPeriod": "ONE_MONTH",
                        },
                    }
                ]
            }
        raise AssertionError(f"Unexpected call: {path}")


class AscVerifyIapProductsTests(unittest.TestCase):
    def test_build_report_marks_expected_products_ready(self):
        report = verify.build_report(
            _FakeClient(),
            bundle_id="com.example.app",
            expected_product_ids=[
                "com.example.app.pro",
                "com.example.app.pro.monthly",
            ],
        )

        self.assertEqual("ready", report["status"])
        self.assertEqual(2, report["summary"]["expected_count"])
        self.assertEqual(2, report["summary"]["ready_expected_count"])
        self.assertEqual([], report["summary"]["missing_expected_product_ids"])
        self.assertEqual([], report["summary"]["blocked_expected_products"])

    def test_build_report_flags_missing_and_blocked_products(self):
        report = verify.build_report(
            _FakeClient(),
            bundle_id="com.example.app",
            expected_product_ids=[
                "com.example.app.pro",
                "com.example.app.pro.monthly",
                "com.example.app.pro.annual",
            ],
            ready_states={"APPROVED"},
        )

        self.assertEqual("blocked", report["status"])
        self.assertEqual(3, report["summary"]["expected_count"])
        self.assertEqual(2, report["summary"]["ready_expected_count"])
        self.assertEqual(
            ["com.example.app.pro.annual"],
            report["summary"]["missing_expected_product_ids"],
        )


if __name__ == "__main__":
    unittest.main()
