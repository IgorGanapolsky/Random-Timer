from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_android_store_copy_uses_reaction_positioning() -> None:
    full_description = (
        REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "full_description.txt"
    ).read_text(encoding="utf-8")
    short_description = (
        REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "short_description.txt"
    ).read_text(encoding="utf-8")

    assert "TRAIN FOR CHAOS. NOT RHYTHM." in full_description
    assert "Random Tactical Timer is a random timer and reaction timer" in full_description
    assert "dry fire timer, boxing timer, BJJ timer, or HIIT timer" in full_description
    assert "serious fighters and operators" not in full_description
    assert short_description.strip() == "Random timer for dry fire, boxing, BJJ, HIIT, and reaction drills."


def test_ios_store_copy_matches_reaction_positioning() -> None:
    description = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "description.txt"
    ).read_text(encoding="utf-8")
    promotional_text = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "promotional_text.txt"
    ).read_text(encoding="utf-8")
    subtitle = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "subtitle.txt"
    ).read_text(encoding="utf-8").strip()
    keywords = (
        REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "keywords.txt"
    ).read_text(encoding="utf-8").strip()

    assert "TRAIN FOR CHAOS. NOT RHYTHM." in description
    assert "Random Tactical Timer is a random timer and reaction timer" in description
    assert "dry fire timer, boxing timer, BJJ timer, or HIIT timer" in description
    assert promotional_text.strip() == "Random timer for dry fire, boxing, BJJ, HIIT, and reaction drills."
    assert subtitle == "Dry Fire, Boxing, BJJ, HIIT"
    assert "shot timer" in keywords
