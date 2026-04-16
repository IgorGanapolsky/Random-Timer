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
    assert "Most timers teach anticipation. Random Tactical Timer trains reaction." in full_description
    assert "pattern-interrupt training built for combat sports, sparring, drills, and reaction work." in full_description
    assert "serious fighters and operators" not in full_description
    assert (
        short_description.strip()
        == "Random tactical timer: MMA, boxing, BJJ & HIIT. Random cues + AI coach voices."
    )


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
    assert "Most timers teach anticipation. Random Tactical Timer trains reaction." in description
    assert "Built for combat sports, HIIT, CrossFit, and reaction training." in description
    assert (
        promotional_text.strip()
        == "Unpredictable intervals for combat sports & HIIT. AI coach voices, 60‑min sessions, full sound library—optional Pro."
    )
    assert subtitle == "Random HIIT & combat rounds"
    assert "mma" in keywords
    assert "crossfit" in keywords
