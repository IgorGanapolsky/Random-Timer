import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class NorthStarGuardrailTests(unittest.TestCase):
    def _write_paid_campaigns(self, root: Path, statuses: list[str]) -> None:
        path = root / "marketing" / "data" / "paid_campaigns.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "campaigns": [
                {"platform": f"p{i}", "status": status, "daily_budget_usd": 10.0}
                for i, status in enumerate(statuses)
            ]
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_run_missing_credentials_marks_skipped(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["draft"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "posthog_api_key": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ):
                result = nsg.run(root)

            self.assertEqual(result["status"], "skipped")
            out = root / "marketing" / "data" / "north_star.json"
            self.assertTrue(out.exists())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "skipped")
            self.assertFalse(payload["paid"]["guardrail_violated"])

    def test_guardrail_violates_when_active_and_zero_paid_users(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                # query_scalar calls:
                # wqtu, completions_7d, completed_users_7d, paid_distinct_users_30d
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[0, 2, 1, 0],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[],
                ):
                    result = nsg.run(root)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["active_campaign_count"], 1)
            self.assertEqual(result["paid_distinct_users_30d"], 0)
            self.assertTrue(result["guardrail_violated"])

    def test_guardrail_passes_with_paid_users(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active", "running"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[3, 12, 4, 7],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[["apple_ads", 20, 7]],
                ):
                    result = nsg.run(root)

            self.assertEqual(result["wqtu_7d"], 3)
            self.assertEqual(result["active_campaign_count"], 2)
            self.assertEqual(result["paid_distinct_users_30d"], 7)
            self.assertFalse(result["guardrail_violated"])


if __name__ == "__main__":
    unittest.main()
