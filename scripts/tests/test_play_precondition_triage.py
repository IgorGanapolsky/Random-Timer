import unittest

from scripts.play_precondition_triage import (
    build_issue_body,
    is_failed_precondition_payload,
    should_close_issue,
)


class PlayPreconditionTriageTests(unittest.TestCase):
    def test_is_failed_precondition_payload_true(self):
        payload = {
            "error": "HttpError 400",
            "response": '{"error":{"status":"FAILED_PRECONDITION","message":"Precondition check failed."}}',
        }
        self.assertTrue(is_failed_precondition_payload(payload))

    def test_is_failed_precondition_payload_false(self):
        payload = {
            "error": "HttpError 403",
            "response": '{"error":{"status":"PERMISSION_DENIED","message":"Forbidden"}}',
        }
        self.assertFalse(is_failed_precondition_payload(payload))

    def test_should_close_issue_only_on_production_success(self):
        self.assertTrue(
            should_close_issue(
                {
                    "requested_track": "production",
                    "effective_track": "production",
                    "fallback_used": False,
                    "precondition_blocked": False,
                }
            )
        )
        self.assertFalse(
            should_close_issue(
                {
                    "requested_track": "production",
                    "effective_track": "alpha",
                    "fallback_used": True,
                    "precondition_blocked": True,
                }
            )
        )

    def test_build_issue_body_contains_run_and_details(self):
        body = build_issue_body(
            run_url="https://github.com/org/repo/actions/runs/123",
            error_payload={
                "http_status": 400,
                "requested_track": "production",
                "track": "production",
                "release_status": "completed",
                "attempt": 1,
                "response": "FAILED_PRECONDITION: Precondition check failed.",
            },
            result_payload={"effective_track": "alpha", "fallback_used": True, "version_code": "42"},
        )
        self.assertIn("https://github.com/org/repo/actions/runs/123", body)
        self.assertIn("FAILED_PRECONDITION", body)
        self.assertIn('"effective_track": "alpha"', body)


if __name__ == "__main__":
    unittest.main()
