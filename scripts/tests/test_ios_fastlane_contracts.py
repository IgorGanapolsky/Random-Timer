from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FASTFILE = ROOT / "native-ios/fastlane/Fastfile"


def test_ios_beta_lane_keeps_testflight_groups_for_internal_and_external_distribution():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "TESTFLIGHT_GROUPS" in source
    assert "options[:groups] = group_names unless group_names.empty?" in source
    assert 'return options unless distribute_external' in source
    assert "options[:distribute_external] = true" in source
    assert 'TESTFLIGHT_GROUPS required when TESTFLIGHT_DISTRIBUTE_EXTERNAL=true' in source


def test_ios_beta_lane_handles_duplicate_build_numbers_with_retry_logic():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "duplicate_testflight_build_error?" in source
    assert "Retrying TestFlight upload" in source
