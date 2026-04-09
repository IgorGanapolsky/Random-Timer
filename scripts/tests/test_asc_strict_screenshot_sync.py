import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from scripts.asc import asc_strict_screenshot_sync as strict_sync


def _report(state: str, *, iphone_ok: bool, ipad_ok: bool) -> dict:
    return {
        "app_store_state": state,
        "checks": [
            {"name": "Screenshots (iPhone)", "passed": iphone_ok},
            {"name": "Screenshots (iPad)", "passed": ipad_ok},
            {"name": "Localization Metadata", "passed": True},
        ],
        "screenshot_counts": {"APP_IPHONE_67": 3 if iphone_ok else 1, "APP_IPAD_PRO_3GEN_129": 3 if ipad_ok else 1},
        "screenshot_total_counts": {"APP_IPHONE_67": 3, "APP_IPAD_PRO_3GEN_129": 3},
        "screenshot_asset_states": {
            "APP_IPHONE_67": {"COMPLETE": 3 if iphone_ok else 1},
            "APP_IPAD_PRO_3GEN_129": {"COMPLETE": 3 if ipad_ok else 1},
        },
    }


class AscStrictScreenshotSyncTests(unittest.TestCase):
    def _run(self, *, retry_on_editable: bool = True) -> tuple[int, dict]:
        return strict_sync.run_strict_screenshot_sync(
            repo_root=Path("repo_root"),
            bundle_id="com.example.app",
            version="1.2.3",
            locale="en-US",
            min_iphone=3,
            min_ipad=3,
            require_build=False,
            retry_on_editable=retry_on_editable,
            dry_run=False,
        )

    def _run_with_verify(
        self,
        verify_side_effect: list[tuple[bool, dict]],
        *,
        retry_on_editable: bool = True,
        reset_value: Optional[dict] = None,
        fastlane_rc: int = 0,
    ):
        if reset_value is None:
            reset_value = {"deleted_assets": 6}
        with (
            patch.object(strict_sync, "verify_ready", side_effect=verify_side_effect),
            patch.object(strict_sync, "reset_screenshots", return_value=reset_value) as reset_mock,
            patch.object(strict_sync, "_run_fastlane_metadata", return_value=fastlane_rc) as fastlane_mock,
        ):
            rc, payload = self._run(retry_on_editable=retry_on_editable)
        return rc, payload, reset_mock, fastlane_mock

    def test_fails_fast_when_precheck_state_is_locked(self):
        with (
            patch.object(strict_sync, "verify_ready", side_effect=[(False, _report("WAITING_FOR_REVIEW", iphone_ok=False, ipad_ok=False))]),
            patch.object(strict_sync, "reset_screenshots") as reset_mock,
            patch.object(strict_sync, "_run_fastlane_metadata") as fastlane_mock,
        ):
            rc, payload = self._run()

        self.assertEqual(rc, 1)
        self.assertEqual(payload["result"], "failed_locked_before_replacement")
        self.assertEqual(len(payload["attempts"]), 0)
        reset_mock.assert_not_called()
        fastlane_mock.assert_not_called()

    def test_succeeds_on_first_attempt_when_verify_ready_passes(self):
        with (
            patch.object(
                strict_sync,
                "verify_ready",
                side_effect=[
                    (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                    (True, _report("PREPARE_FOR_SUBMISSION", iphone_ok=True, ipad_ok=True)),
                ],
            ),
            patch.object(strict_sync, "reset_screenshots", return_value={"deleted_assets": 6}) as reset_mock,
            patch.object(strict_sync, "_run_fastlane_metadata", return_value=0) as fastlane_mock,
        ):
            rc, payload = self._run()

        self.assertEqual(rc, 0)
        self.assertEqual(payload["result"], "success")
        self.assertEqual(len(payload["attempts"]), 1)
        self.assertEqual(reset_mock.call_count, 1)
        self.assertEqual(fastlane_mock.call_count, 1)

    def test_retries_once_when_screenshot_checks_fail_but_state_is_editable(self):
        rc, payload, reset_mock, fastlane_mock = self._run_with_verify(
            [
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                (True, _report("PREPARE_FOR_SUBMISSION", iphone_ok=True, ipad_ok=True)),
            ]
        )

        self.assertEqual(rc, 0)
        self.assertEqual(payload["result"], "success")
        self.assertEqual(len(payload["attempts"]), 2)
        self.assertEqual(reset_mock.call_count, 2)
        self.assertEqual(fastlane_mock.call_count, 2)

    def test_does_not_retry_when_screenshots_fail_and_state_locks(self):
        rc, payload, reset_mock, fastlane_mock = self._run_with_verify(
            [
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                (False, _report("WAITING_FOR_REVIEW", iphone_ok=False, ipad_ok=False)),
            ]
        )

        self.assertEqual(rc, 1)
        self.assertEqual(payload["result"], "failed_after_replacement_attempts")
        self.assertEqual(len(payload["attempts"]), 1)
        self.assertIn("locked", payload["reason"])
        self.assertEqual(reset_mock.call_count, 1)
        self.assertEqual(fastlane_mock.call_count, 1)

    def test_fastlane_failure_sets_final_from_post_failure_verify(self):
        rc, payload, reset_mock, fastlane_mock = self._run_with_verify(
            [
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                (False, _report("WAITING_FOR_REVIEW", iphone_ok=True, ipad_ok=True)),
            ],
            fastlane_rc=3,
        )

        self.assertEqual(rc, 2)
        self.assertEqual(payload["result"], "failed_fastlane_metadata")
        self.assertEqual(len(payload["attempts"]), 1)
        self.assertEqual(payload["final"]["app_store_state"], "WAITING_FOR_REVIEW")
        self.assertTrue(payload["final"]["screenshot_checks"]["passed"])
        self.assertEqual(payload["final_verify_report"]["app_store_state"], "WAITING_FOR_REVIEW")
        self.assertEqual(reset_mock.call_count, 1)
        self.assertEqual(fastlane_mock.call_count, 1)

    def test_does_not_retry_when_non_screenshot_checks_fail(self):
        rc, payload, reset_mock, fastlane_mock = self._run_with_verify(
            [
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=False, ipad_ok=False)),
                (False, _report("PREPARE_FOR_SUBMISSION", iphone_ok=True, ipad_ok=True)),
            ]
        )

        self.assertEqual(rc, 1)
        self.assertEqual(payload["result"], "failed_after_replacement_attempts")
        self.assertIn("other ASC readiness checks", payload["reason"])
        self.assertEqual(len(payload["attempts"]), 1)
        self.assertEqual(reset_mock.call_count, 1)
        self.assertEqual(fastlane_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
