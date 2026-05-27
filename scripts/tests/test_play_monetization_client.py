from __future__ import annotations

import unittest

from scripts.play_monetization_client import REQUIRED_ONE_TIME, REQUIRED_SUBSCRIPTIONS


class PlayMonetizationClientTests(unittest.TestCase):
    def test_required_product_ids_match_android_billing_layer(self):
        self.assertEqual(REQUIRED_ONE_TIME, ("pro_base",))
        self.assertIn("elite_tactical", REQUIRED_SUBSCRIPTIONS)
        self.assertIn("elite_tactical_monthly", REQUIRED_SUBSCRIPTIONS)


if __name__ == "__main__":
    unittest.main()
