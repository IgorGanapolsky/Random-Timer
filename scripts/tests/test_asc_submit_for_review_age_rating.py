import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyAgeRatingTests(unittest.TestCase):
    def test_verify_age_rating_accepts_app_scoped_declaration(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {"data": []},
                ("GET", "/apps/app1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/apps/app1/appStoreAgeRatingDeclaration"): {"data": {"id": "decl1", "type": "appStoreAgeRatingDeclarations"}},
            }
        )
        verify_age_rating(client, "app1", None)

    def test_verify_age_rating_falls_back_to_version_scoped_declaration(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {"data": []},
                ("GET", "/apps/app1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/apps/app1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appStoreAgeRatingDeclaration"): {"data": {"id": "decl1", "type": "appStoreAgeRatingDeclarations"}},
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_falls_back_to_app_info_scoped_declaration(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {"data": [{"id": "info1", "type": "appInfos"}]},
                ("GET", "/apps/app1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/apps/app1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appInfos/info1/appInfoAgeRatingDeclaration"): {"data": {"id": "decl1", "type": "appInfoAgeRatingDeclarations"}},
            }
        )
        verify_age_rating(client, "app1", "ver1")

    def test_verify_age_rating_dies_when_missing(self):
        from scripts.asc_submit_for_review import verify_age_rating

        client = RouterClient(
            {
                ("GET", "/apps/app1/appInfos"): {"data": []},
                ("GET", "/apps/app1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/apps/app1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appStoreVersions/ver1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appInfos/info1/appInfoAgeRatingDeclaration"): RuntimeError("404"),
                ("GET", "/appInfos/info1/appStoreAgeRatingDeclaration"): RuntimeError("404"),
            }
        )
        with self.assertRaises(SystemExit):
            verify_age_rating(client, "app1", "ver1")


if __name__ == "__main__":
    unittest.main()
