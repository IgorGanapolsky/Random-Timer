import unittest
from unittest.mock import patch

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyAgeRatingTests(unittest.TestCase):
    def test_verify_age_rating_reads_age_rating_declaration_from_app_info(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {
                    "data": [
                        {
                            "id": "info1",
                            "type": "appInfos",
                            "attributes": {"platform": "IOS"},
                        }
                    ]
                },
                ("GET", "/appInfos/info1/ageRatingDeclaration"): {
                    "data": {"id": "decl1", "type": "ageRatingDeclarations", "attributes": {}}
                },
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_falls_back_to_version_path(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/ageRatingDeclaration"): {
                    "data": {"id": "decl1", "type": "ageRatingDeclarations", "attributes": {}}
                },
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_dies_when_missing(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {
                    "data": [
                        {
                            "id": "info1",
                            "type": "appInfos",
                            "attributes": {"platform": "IOS"},
                        }
                    ]
                },
                ("GET", "/appInfos/info1/ageRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appInfos/info1/relationships/ageRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/ageRatingDeclaration"): RuntimeError("404"),
            }
        )
        with self.assertRaises(SystemExit):
            verify_age_rating(client, "app1", "ver1")

    def test_cleanup_stale_submission_deletes_existing_submission_for_editable_state(self):
        from scripts.asc_submit_for_review import cleanup_stale_submission

        responses = iter(
            [
                {"data": {"id": "sub1", "type": "appStoreVersionSubmissions"}},
                {"data": None},
            ]
        )

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1/appStoreVersionSubmission"): lambda: next(responses),
                ("DELETE", "/appStoreVersionSubmissions/sub1"): {},
            }
        )

        with patch("scripts.asc_submit_for_review.time.sleep", lambda *_a, **_k: None):
            cleanup_stale_submission(client, "ver1", state="PREPARE_FOR_SUBMISSION")

        self.assertTrue(
            any(
                call["method"] == "DELETE"
                and call["path"] == "/appStoreVersionSubmissions/sub1"
                for call in client.calls
            )
        )

    def test_cleanup_stale_submission_skips_when_version_already_submitted(self):
        from scripts.asc_submit_for_review import cleanup_stale_submission

        client = RouterClient({})
        cleanup_stale_submission(client, "ver1", state="WAITING_FOR_REVIEW")
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
