from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FASTFILE = ROOT / "native-ios/fastlane/Fastfile"


def test_ios_beta_lane_only_assigns_testflight_groups_for_external_distribution():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "TESTFLIGHT_GROUPS" in source
    assert 'return options unless distribute_external' in source
    internal_block = source.split("def testflight_upload_options", 1)[1].split(
        'return options unless distribute_external', 1
    )[0]
    assert "options[:groups]" not in internal_block
    external_block = source.split('return options unless distribute_external', 1)[1].split(
        "options[:changelog]", 1
    )[0]
    assert "options[:groups] = group_names" in external_block
    assert "options[:distribute_external] = true" in source
    assert 'TESTFLIGHT_GROUPS required when TESTFLIGHT_DISTRIBUTE_EXTERNAL=true' in source


def test_ios_beta_lane_handles_duplicate_build_numbers_with_retry_logic():
    source = FASTFILE.read_text(encoding="utf-8")

    assert "duplicate_testflight_build_error?" in source
    assert "Retrying TestFlight upload" in source
