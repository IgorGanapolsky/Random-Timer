import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyAgeRatingTests(unittest.TestCase):
    def test_verify_age_rating_reads_age_rating_declaration_from_state_matched_app_info(self):
        from scripts.asc.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1"): {
                    "data": {"id": "ver1", "type": "appStoreVersions", "attributes": {"appStoreState": "REJECTED"}}
                },
                ("GET", "/apps/app1/appInfos"): {
                    "data": [
                        {"id": "info-ready", "type": "appInfos", "attributes": {"appStoreState": "READY_FOR_SALE"}},
                        {"id": "info-rejected", "type": "appInfos", "attributes": {"appStoreState": "REJECTED"}},
                    ]
                },
                ("GET", "/appInfos/info-rejected/ageRatingDeclaration"): {
                    "data": {"id": "decl1", "type": "ageRatingDeclarations", "attributes": {}}
                }
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_dies_when_missing(self):
        from scripts.asc.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1"): {
                    "data": {"id": "ver1", "type": "appStoreVersions", "attributes": {"appStoreState": "REJECTED"}}
                },
                ("GET", "/apps/app1/appInfos"): {
                    "data": [{"id": "info-rejected", "type": "appInfos", "attributes": {"appStoreState": "REJECTED"}}]
                },
                ("GET", "/appInfos/info-rejected/ageRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/ageRatingDeclaration"): RuntimeError("404"),
            }
        )
        with self.assertRaises(SystemExit):
            verify_age_rating(client, "app1", "ver1")


if __name__ == "__main__":
    unittest.main()
