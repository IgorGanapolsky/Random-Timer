from __future__ import annotations

import unittest
from unittest.mock import patch

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import admob_status as mod  # noqa: E402


class AdmobStatusTests(unittest.TestCase):
    def test_print_app_ads_report_passes_when_urls_ok(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(True, "ok")):
            rc = mod.print_app_ads_report(also_play_path=False)
        self.assertEqual(rc, 0)

    def test_print_app_ads_report_fails_on_missing_file(self):
        with patch.object(mod, "verify_app_ads_txt", return_value=(False, "HTTP 404")):
            rc = mod.print_app_ads_report(also_play_path=False)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
