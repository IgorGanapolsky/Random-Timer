from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

IOS_DISTRIBUTION_WORKFLOWS = [
    ".github/workflows/internal-distribution.yml",
    ".github/workflows/native-release.yml",
    ".github/workflows/ios-submit-review.yml",
    ".github/workflows/ios-apple-id-release.yml",
]


def test_ios_distribution_uploads_use_xcode_26_runner() -> None:
    for workflow in IOS_DISTRIBUTION_WORKFLOWS:
        source = (ROOT / workflow).read_text(encoding="utf-8")
        assert "runs-on: macos-26" in source, (
            f"{workflow} must use macos-26 so App Store uploads are built "
            "with the iOS 26 SDK required by App Store Connect."
        )
        assert "runs-on: macos-15" not in source, (
            f"{workflow} must not use macos-15 for distribution uploads; "
            "that runner builds with an SDK App Store Connect rejects."
        )
