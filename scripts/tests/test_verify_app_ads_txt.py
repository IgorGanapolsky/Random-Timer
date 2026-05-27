from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import verify_app_ads_txt as mod


class VerifyAppAdsTxtTests(unittest.TestCase):
    def test_verify_accepts_authorized_line(self):
        body = "google.com, pub-5173650670360699, DIRECT, f08c47fec0942fa0\n"
        with patch.object(mod, "fetch", return_value=body):
            ok, msg = mod.verify_app_ads_txt(url="https://example.com/app-ads.txt")
        self.assertTrue(ok)
        self.assertIn("ok", msg)

    def test_verify_rejects_missing_publisher(self):
        with patch.object(mod, "fetch", return_value="google.com, pub-000, DIRECT, f08c47fec0942fa0\n"):
            ok, _ = mod.verify_app_ads_txt(url="https://example.com/app-ads.txt")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
