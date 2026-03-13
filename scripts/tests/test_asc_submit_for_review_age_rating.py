import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyAgeRatingTests(unittest.TestCase):
    def test_verify_age_rating_reads_age_rating_declaration_from_app_info_relationship(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {
                    "data": [{"id": "info1", "type": "appInfos", "attributes": {"platform": "IOS"}}]
                },
                ("GET", "/appInfos/info1/relationships/ageRatingDeclaration"): {
                    "data": {"id": "decl1", "type": "ageRatingDeclarations"}
                }
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_falls_back_to_legacy_version_relationship(self):
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
                ("GET", "/apps/app1/appInfos"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/ageRatingDeclaration"): RuntimeError("404"),
            }
        )
        with self.assertRaises(SystemExit):
            verify_age_rating(client, "app1", "ver1")


if __name__ == "__main__":
    unittest.main()
