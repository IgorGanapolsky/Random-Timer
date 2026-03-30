from __future__ import annotations

from scripts import fix_ios_subscription_metadata as mod


def test_md5_hexdigest_matches_expected():
    assert mod._md5_hexdigest(b"abc") == "900150983cd24fb0d6963f7d28e17f72"


def test_build_review_note_payload():
    payload = mod._build_review_note_payload("6761282921", "note")
    assert payload == {
        "data": {
            "id": "6761282921",
            "type": "subscriptions",
            "attributes": {"reviewNote": "note"},
        }
    }


def test_build_review_screenshot_create_payload():
    payload = mod._build_review_screenshot_create_payload(
        "6761282921",
        file_name="3_pro.png",
        file_size=123,
    )
    assert payload == {
        "data": {
            "type": "subscriptionAppStoreReviewScreenshots",
            "attributes": {
                "fileName": "3_pro.png",
                "fileSize": 123,
            },
            "relationships": {
                "subscription": {
                    "data": {
                        "id": "6761282921",
                        "type": "subscriptions",
                    }
                }
            },
        }
    }


def test_build_review_screenshot_commit_payload():
    payload = mod._build_review_screenshot_commit_payload(
        "screenshot-id",
        checksum_md5="abc123",
    )
    assert payload == {
        "data": {
            "id": "screenshot-id",
            "type": "subscriptionAppStoreReviewScreenshots",
            "attributes": {
                "uploaded": True,
                "sourceFileChecksum": "abc123",
            },
        }
    }


def test_headers_dict_filters_blank_names():
    assert mod._headers_dict(
        [
            {"name": "Content-Type", "value": "image/png"},
            {"name": "", "value": "ignored"},
        ]
    ) == {"Content-Type": "image/png"}


def test_slice_bytes_uses_offset_and_length():
    assert mod._slice_bytes(b"abcdefgh", offset=2, length=3) == b"cde"
