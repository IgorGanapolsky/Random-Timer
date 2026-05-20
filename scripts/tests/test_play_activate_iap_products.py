from __future__ import annotations

import unittest
from unittest.mock import Mock

from scripts import play_monetization_client as client


class PlayActivateIapProductsTests(unittest.TestCase):
    def _service_with_product(self, product: dict) -> Mock:
        one_time = Mock()
        one_time.get.return_value.execute.return_value = product
        purchase_options = Mock()
        one_time.purchaseOptions.return_value = purchase_options
        monetization = Mock()
        monetization.onetimeproducts.return_value = one_time
        service = Mock()
        service.monetization.return_value = monetization
        return service, purchase_options

    def test_skips_already_active_purchase_option(self):
        service, purchase_options = self._service_with_product(
            {
                "purchaseOptions": [
                    {"purchaseOptionId": "pro-base-buy", "state": "ACTIVE"},
                ]
            }
        )
        result = client.activate_one_time_product(service, "pro_base")
        self.assertEqual(result["actions"][0]["action"], "skip")
        purchase_options.batchUpdateStates.assert_not_called()

    def test_activates_inactive_purchase_option(self):
        service, purchase_options = self._service_with_product(
            {
                "purchaseOptions": [
                    {"purchaseOptionId": "pro-base-buy", "state": "DRAFT"},
                ]
            }
        )
        result = client.activate_one_time_product(service, "pro_base")
        self.assertEqual(result["actions"][0]["action"], "activated")
        purchase_options.batchUpdateStates.assert_called_once()


if __name__ == "__main__":
    unittest.main()
