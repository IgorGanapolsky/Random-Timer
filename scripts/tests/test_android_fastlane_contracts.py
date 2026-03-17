from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FASTFILE = ROOT / "native-android" / "fastlane" / "Fastfile"


def test_internal_lane_skips_play_changelog_uploads():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "lane :internal do" in source
    assert 'track: "internal"' in source
    assert "skip_upload_metadata: true" in source
    assert "skip_upload_changelogs: true" in source
