from __future__ import annotations

import unittest
from unittest.mock import Mock

from scripts import play_activate_iap_products as activate


class _FakePurchaseOptions:
    def __init__(self, parent):
        self._parent = parent

    def batchUpdateStates(self, **_kwargs):
        self._parent.updated = True
        return Mock(execute=lambda: {})


class _FakeOneTimeProduct:
    def __init__(self, product, parent):
        self._product = product
        self._parent = parent

    def get(self, **_kwargs):
        return Mock(execute=lambda: self._product)

    def purchaseOptions(self):
        return _FakePurchaseOptions(self._parent)


class _FakeMonetization:
    def __init__(self, product):
        self.updated = False
        self._product = product

    def onetimeproducts(self):
        return _FakeOneTimeProduct(self._product, self)


class PlayActivateIapProductsTests(unittest.TestCase):
    def test_skips_already_active_purchase_option(self):
        service = Mock()
        service.monetization.return_value = _FakeMonetization(
            {
                "purchaseOptions": [
                    {"purchaseOptionId": "pro-base-buy", "state": "ACTIVE"},
                ]
            }
        )
        result = activate._activate_one_time_product(service, "pro_base")
        self.assertEqual(result["actions"][0]["action"], "skip")
        self.assertFalse(service.monetization.return_value.updated)

    def test_activates_inactive_purchase_option(self):
        service = Mock()
        service.monetization.return_value = _FakeMonetization(
            {
                "purchaseOptions": [
                    {"purchaseOptionId": "pro-base-buy", "state": "DRAFT"},
                ]
            }
        )
        result = activate._activate_one_time_product(service, "pro_base")
        self.assertEqual(result["actions"][0]["action"], "activated")
        self.assertTrue(service.monetization.return_value.updated)


if __name__ == "__main__":
    unittest.main()
