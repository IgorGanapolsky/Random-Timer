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
