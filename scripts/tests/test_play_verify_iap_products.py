from __future__ import annotations

import unittest
from unittest.mock import Mock
from unittest.mock import patch

from scripts import play_verify_iap_products as verify
from scripts import play_monetization_client as client


class _FakeMonetization:
    def __init__(self, one_time=None, subscriptions=None):
        self._one_time = one_time or []
        self._subscriptions = subscriptions or []

    def onetimeproducts(self):
        parent = self

        class _OneTime:
            def list(self, **_kwargs):
                return Mock(execute=lambda: {"oneTimeProducts": parent._one_time})

        return _OneTime()

    def subscriptions(self):
        parent = self

        class _Subs:
            def list(self, **_kwargs):
                return Mock(execute=lambda: {"subscriptions": parent._subscriptions})

        return _Subs()


class PlayVerifyIapProductsTests(unittest.TestCase):
    def test_list_one_time_maps_product_ids(self):
        service = Mock()
        service.monetization.return_value = _FakeMonetization(
            one_time=[{"productId": "pro_base", "state": "ACTIVE"}]
        )
        products = client.list_one_time_products(service)
        self.assertEqual(products[0]["product_id"], "pro_base")

    def test_subscription_purchase_blockers_requires_monthly_somewhere(self):
        subscriptions = [
            {
                "product_id": "elite_tactical",
                "base_plans": [{"base_plan_id": "annual", "state": "ACTIVE"}],
            }
        ]
        blockers = client.subscription_purchase_blockers(subscriptions)
        self.assertTrue(any("monthly" in item["reason"] for item in blockers))

    def test_subscription_purchase_blockers_ok_when_monthly_on_elite_tactical_monthly(self):
        subscriptions = [
            {
                "product_id": "elite_tactical",
                "base_plans": [{"base_plan_id": "annual", "state": "ACTIVE"}],
            },
            {
                "product_id": "elite_tactical_monthly",
                "base_plans": [{"base_plan_id": "monthly", "state": "ACTIVE"}],
            },
        ]
        blockers = client.subscription_purchase_blockers(subscriptions)
        self.assertEqual(blockers, [])

    def test_subscription_purchase_blockers_ok_when_elite_annual_and_monthly_active(self):
        subscriptions = [
            {
                "product_id": "elite_tactical",
                "base_plans": [
                    {"base_plan_id": "annual", "state": "ACTIVE"},
                    {"base_plan_id": "monthly", "state": "ACTIVE"},
                ],
            }
        ]
        blockers = client.subscription_purchase_blockers(subscriptions)
        self.assertEqual(blockers, [])

    def test_missing_required_products_fails_main(self):
        service = Mock()
        service.monetization.return_value = _FakeMonetization(one_time=[], subscriptions=[])
        with patch.object(verify, "build_android_publisher_service", return_value=service):
            with patch.object(verify, "resolve_play_credentials", return_value="play-service-account.json"):
                with patch("sys.argv", ["play_verify_iap_products.py"]):
                    code = verify.main()
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
