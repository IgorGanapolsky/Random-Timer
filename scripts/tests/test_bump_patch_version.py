from __future__ import annotations

from scripts import bump_patch_version


def test_read_android_version_code_supports_ci_fallback():
    gradle_text = """
        val ciVersionCode = providers.gradleProperty("ciVersionCode").orNull?.toIntOrNull()
        versionCode = ciVersionCode ?: 1774900003
    """

    assert bump_patch_version.read_android_version_code(gradle_text) == 1774900003


def test_update_android_changelog_uses_version_code_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(bump_patch_version, "ANDROID_CHANGELOG_DIR", tmp_path)
    monkeypatch.setattr(bump_patch_version, "REPO_ROOT", tmp_path.parent)

    path = bump_patch_version.update_android_changelog(
        1774900003,
        "Release notes",
        dry_run=False,
    )

    assert path == tmp_path / "1774900003.txt"
    assert path.read_text(encoding="utf-8") == "Release notes\n"


def test_write_android_version_code_updates_ci_fallback_line():
    text = """
        val ciVersionCode = providers.gradleProperty("ciVersionCode").orNull?.toIntOrNull()
        versionCode = ciVersionCode ?: 1774900003
        versionName = "1.3.20"
    """
    out = bump_patch_version.write_android_version_code(text, 1774900004)
    assert "versionCode = ciVersionCode ?: 1774900004" in out
    assert "1774900003" not in out


def test_write_android_version_then_semver_matches_bump_contract(tmp_path, monkeypatch):
    """Contract: semver bump applies first, then versionCode+1 (Play changelog id)."""
    gradle = """
android {
    defaultConfig {
        versionCode = ciVersionCode ?: 1774900003
        versionName = "1.3.20"
    }
}
"""
    after_ver = bump_patch_version.write_android_version(gradle, "1.3.21")
    after_code = bump_patch_version.write_android_version_code(after_ver, 1774900004)
    assert 'versionName = "1.3.21"' in after_code
    assert "versionCode = ciVersionCode ?: 1774900004" in after_code

    monkeypatch.setattr(bump_patch_version, "ANDROID_CHANGELOG_DIR", tmp_path)
    monkeypatch.setattr(bump_patch_version, "REPO_ROOT", tmp_path.parent)
    path = bump_patch_version.update_android_changelog(1774900004, "Notes", dry_run=False)
    assert path == tmp_path / "1774900004.txt"
    assert path.read_text(encoding="utf-8") == "Notes\n"
