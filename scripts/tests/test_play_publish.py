import unittest

from scripts.play_publish import (
    _is_failed_precondition,
    _is_no_country_targeting_error,
    _parse_country_codes,
    _release_payload,
)


class PlayPublishTests(unittest.TestCase):
    def test_detects_failed_precondition_marker(self):
        self.assertTrue(
            _is_failed_precondition(
                "HttpError 400",
                '{"error":{"status":"FAILED_PRECONDITION","message":"Precondition check failed."}}',
                400,
            )
        )

    def test_detects_precondition_phrase_for_400(self):
        self.assertTrue(
            _is_failed_precondition(
                "Bad request",
                "Precondition check failed for production publishing.",
                400,
            )
        )

    def test_does_not_false_positive_without_precondition(self):
        self.assertFalse(
            _is_failed_precondition(
                "HttpError 403",
                '{"error":{"status":"PERMISSION_DENIED","message":"No permission"}}',
                403,
            )
        )

    def test_detects_no_country_targeting_error(self):
        self.assertTrue(
            _is_no_country_targeting_error(
                "HttpError 403",
                '{"error":{"status":"PERMISSION_DENIED","message":"Release in track targeting no countries"}}',
                403,
            )
        )

    def test_does_not_false_positive_for_country_targeting_without_403(self):
        self.assertFalse(
            _is_no_country_targeting_error(
                "HttpError 400",
                '{"error":{"status":"FAILED_PRECONDITION","message":"Release in track targeting no countries"}}',
                400,
            )
        )

    def test_release_payload_in_progress_clamps_invalid_fraction(self):
        payload = _release_payload(
            version_code="123",
            release_status="inProgress",
            release_notes="",
            user_fraction_raw="1.0",
        )
        self.assertEqual(payload["userFraction"], 0.1)
        self.assertEqual(payload["status"], "inProgress")

    def test_release_payload_completed_skips_user_fraction(self):
        payload = _release_payload(
            version_code="123",
            release_status="completed",
            release_notes="notes",
            user_fraction_raw="0.5",
        )
        self.assertNotIn("userFraction", payload)
        self.assertEqual(payload["releaseNotes"][0]["text"], "notes")

    def test_release_payload_in_progress_adds_country_targeting(self):
        payload = _release_payload(
            version_code="123",
            release_status="inProgress",
            release_notes="",
            user_fraction_raw="0.99",
            country_codes=["US"],
            include_rest_of_world=False,
        )
        self.assertEqual(payload["countryTargeting"]["countries"], ["US"])
        self.assertFalse(payload["countryTargeting"]["includeRestOfWorld"])
        self.assertEqual(payload["userFraction"], 0.99)

    def test_parse_country_codes_normalizes_and_deduplicates(self):
        self.assertEqual(_parse_country_codes("us, CA,us,,ca, gb "), ["US", "CA", "GB"])


if __name__ == "__main__":
    unittest.main()
