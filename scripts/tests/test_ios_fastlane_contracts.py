from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FASTFILE = ROOT / "native-ios/fastlane/Fastfile"


def test_ios_beta_lane_supports_explicit_testflight_groups():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "TESTFLIGHT_GROUPS" in source
    assert "options[:groups]" in source
    assert "distribute_external" in source


def test_ios_beta_lane_handles_duplicate_build_numbers_with_retry_logic():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "duplicate_testflight_build_error?" in source
    assert "Retrying TestFlight upload" in source
