import unittest


class _RouterClient:
    def __init__(self, routes):
        self._routes = routes
        self.calls = []

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
        key = (method, path)
        if key not in self._routes:
            raise RuntimeError(f"unhandled route {method} {path}")
        value = self._routes[key]
        if isinstance(value, Exception):
            raise value
        if callable(value):
            return value()
        return value


class AscSubmitForReviewVerifyReviewDetailTests(unittest.TestCase):
    def test_verify_review_detail_reads_relationship_off_version(self):
        from scripts.asc_submit_for_review import verify_review_detail

        client = _RouterClient(
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
        from scripts.asc_submit_for_review import verify_review_detail

        client = _RouterClient(
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

