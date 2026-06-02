from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_android_store_copy_uses_reaction_positioning() -> None:
    full_description = (
        REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "full_description.txt"
    ).read_text(encoding="utf-8")
    short_description = (
        REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "short_description.txt"
    ).read_text(encoding="utf-8").strip()

    assert "TRAIN FOR CHAOS. NOT RHYTHM." in full_description
    assert "unpredictable interval" in full_description.lower()
    assert "reaction" in full_description.lower()
    assert "wrestling" in full_description.lower()
    assert "serious fighters and operators" not in full_description
    assert len(short_description) <= 80
    assert "interval timer" in short_description.lower()
    assert "mma" in short_description.lower()
    assert "coach" in short_description.lower()
    assert "ai coach" not in short_description.lower()


def test_ios_store_copy_matches_reaction_positioning() -> None:
    description = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "description.txt"
    ).read_text(encoding="utf-8")
    promotional_text = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "promotional_text.txt"
    ).read_text(encoding="utf-8").strip()
    subtitle = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "subtitle.txt"
    ).read_text(encoding="utf-8").strip()
    keywords = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "keywords.txt"
    ).read_text(encoding="utf-8").strip()

    assert "TRAIN FOR CHAOS. NOT RHYTHM." in description
    assert "trains reaction" in description.lower()
    assert "wrestling" in description.lower()
    assert len(subtitle) <= 30
    assert "round timer" in subtitle.lower() or "interval" in subtitle.lower()
    assert len(promotional_text) <= 170
    assert "unpredictable" in promotional_text.lower()
    assert "ai coach" not in promotional_text.lower()
    assert len(keywords) <= 100
    keyword_tokens = {k.strip() for k in keywords.split(",")}
    assert "mma" not in keyword_tokens
    assert "boxing" not in keyword_tokens
    assert "bjj" in keyword_tokens
    assert "wrestling" in keyword_tokens
