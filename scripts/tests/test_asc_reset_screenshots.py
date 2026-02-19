import unittest

from scripts import asc_reset_screenshots


class _FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        if path == "/appStoreVersionLocalizations/loc1/appScreenshotSets":
            return {
                "data": [
                    {
                        "id": "set_iphone",
                        "attributes": {"screenshotDisplayType": "APP_IPHONE_67"},
                    },
                    {
                        "id": "set_ipad",
                        "attributes": {"screenshotDisplayType": "APP_IPAD_PRO_3GEN_129"},
                    },
                ]
            }
        if path == "/appScreenshotSets/set_iphone/appScreenshots":
            return {
                "data": [
                    {
                        "id": "shot_a",
                        "attributes": {
                            "fileName": "1_setup.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    },
                    {
                        "id": "shot_b",
                        "attributes": {
                            "fileName": "2_active.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    },
                ]
            }
        if path == "/appScreenshotSets/set_ipad/appScreenshots":
            return {
                "data": [
                    {
                        "id": "shot_c",
                        "attributes": {
                            "fileName": "5_ipad_setup.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    }
                ]
            }
        return {"data": []}


class AscResetScreenshotsTests(unittest.TestCase):
    def test_list_screenshot_assets_reads_all_sets(self):
        client = _FakeClient()
        assets = asc_reset_screenshots.list_screenshot_assets(client, "loc1")
        self.assertEqual(len(assets), 3)
        self.assertEqual([a["screenshot_id"] for a in assets], ["shot_a", "shot_b", "shot_c"])
        self.assertEqual(assets[0]["display_type"], "APP_IPHONE_67")
        self.assertEqual(assets[-1]["display_type"], "APP_IPAD_PRO_3GEN_129")


if __name__ == "__main__":
    unittest.main()
