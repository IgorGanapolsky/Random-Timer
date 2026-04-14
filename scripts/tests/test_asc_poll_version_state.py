import unittest


class _FakeClient:
    def __init__(self, versions):
        self._versions = versions

    def get_all(self, path, *, params=None):
        return self._versions


class AscPollVersionStateTests(unittest.TestCase):
    def test_find_app_store_version_id_returns_id_and_state(self):
        from scripts.asc.asc_poll_version_state import find_app_store_version_id

        client = _FakeClient(
            [
                {
                    "id": "ver123",
                    "type": "appStoreVersions",
                    "attributes": {"appStoreState": "WAITING_FOR_REVIEW"},
                }
            ]
        )

        vid, state = find_app_store_version_id(client, app_id="app1", version="1.2.3")
        self.assertEqual(vid, "ver123")
        self.assertEqual(state, "WAITING_FOR_REVIEW")

    def test_find_app_store_version_id_dies_when_missing(self):
        from scripts.asc.asc_poll_version_state import find_app_store_version_id

        client = _FakeClient([])
        with self.assertRaises(SystemExit):
            find_app_store_version_id(client, app_id="app1", version="1.2.3")

    def test_find_app_store_version_id_defaults_to_unknown_state(self):
        from scripts.asc.asc_poll_version_state import find_app_store_version_id

        client = _FakeClient([{"id": "ver123", "type": "appStoreVersions"}])
        vid, state = find_app_store_version_id(client, app_id="app1", version="1.2.3")
        self.assertEqual(vid, "ver123")
        self.assertEqual(state, "UNKNOWN")

    def test_find_app_store_version_id_dies_when_id_is_missing(self):
        from scripts.asc.asc_poll_version_state import find_app_store_version_id

        client = _FakeClient(
            [
                {
                    "type": "appStoreVersions",
                    "attributes": {"appStoreState": "WAITING_FOR_REVIEW"},
                }
            ]
        )
        with self.assertRaises(SystemExit):
            find_app_store_version_id(client, app_id="app1", version="1.2.3")


if __name__ == "__main__":
    unittest.main()
