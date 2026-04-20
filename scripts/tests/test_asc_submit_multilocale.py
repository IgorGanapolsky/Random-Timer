"""Tests for multi-locale App Store version localization listing."""

import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitMultilocaleTests(unittest.TestCase):
    def test_list_app_store_version_locale_codes_returns_sorted_unique(self):
        from scripts.asc.asc_submit_for_review import list_app_store_version_locale_codes

        client = RouterClient(
            {
                (
                    "GET",
                    "/appStoreVersions/ver-1/appStoreVersionLocalizations",
                ): {
                    "data": [
                        {
                            "id": "loc-ko",
                            "type": "appStoreVersionLocalizations",
                            "attributes": {"locale": "ko"},
                        },
                        {
                            "id": "loc-en",
                            "type": "appStoreVersionLocalizations",
                            "attributes": {"locale": "en-US"},
                        },
                        {
                            "id": "loc-ja",
                            "type": "appStoreVersionLocalizations",
                            "attributes": {"locale": "ja"},
                        },
                    ],
                    "links": {},
                },
            }
        )

        codes = list_app_store_version_locale_codes(client, "ver-1")
        self.assertEqual(codes, ["en-US", "ja", "ko"])
