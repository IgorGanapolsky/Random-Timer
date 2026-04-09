import unittest


from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyReviewDetailTests(unittest.TestCase):
    def test_verify_review_detail_reads_relationship_off_version(self):
        from scripts.asc.asc_submit_for_review import verify_review_detail

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                    "data": {
                        "id": "rd1",
                        "type": "appStoreReviewDetails",
                        "attributes": {"contactEmail": "dev@example.com", "contactPhone": "+15551231234"},
                    }
                }
            }
        )
        verify_review_detail(client, "ver1")
        self.assertEqual([c["path"] for c in client.calls], ["/appStoreVersions/ver1/appStoreReviewDetail"])

    def test_verify_review_detail_requires_contact_email(self):
        from scripts.asc.asc_submit_for_review import verify_review_detail

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                    "data": {"id": "rd1", "type": "appStoreReviewDetails", "attributes": {"contactPhone": "123"}}
                }
            }
        )
        with self.assertRaises(SystemExit):
            verify_review_detail(client, "ver1")


if __name__ == "__main__":
    unittest.main()
