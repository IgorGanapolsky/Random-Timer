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


def test_bump_patch_writes_changelog_for_incremented_version_code(tmp_path, monkeypatch):
    gradle = tmp_path / "build.gradle.kts"
    gradle.write_text(
        """
android {
    defaultConfig {
        versionCode = ciVersionCode ?: 1774900003
        versionName = "1.3.20"
    }
}
""",
        encoding="utf-8",
    )
    pbx = tmp_path / "project.pbxproj"
    pbx.write_text("MARKETING_VERSION = 1.3.20;\n", encoding="utf-8")
    changelog_dir = tmp_path / "changelogs"
    changelog_dir.mkdir(parents=True)
    release_notes = tmp_path / "release_notes.txt"

    monkeypatch.setattr(bump_patch_version, "ANDROID_GRADLE", gradle)
    monkeypatch.setattr(bump_patch_version, "IOS_PBXPROJ", pbx)
    monkeypatch.setattr(bump_patch_version, "ANDROID_CHANGELOG_DIR", changelog_dir)
    monkeypatch.setattr(bump_patch_version, "IOS_RELEASE_NOTES", release_notes)
    monkeypatch.setattr(bump_patch_version, "REPO_ROOT", tmp_path)

    bump_patch_version.bump(dry_run=False, changelog_message="Next patch notes", skip_changelog=False)

    gradle_body = gradle.read_text(encoding="utf-8")
    assert 'versionName = "1.3.21"' in gradle_body
    assert "versionCode = ciVersionCode ?: 1774900004" in gradle_body
    assert pbx.read_text(encoding="utf-8") == "MARKETING_VERSION = 1.3.21;\n"
    assert (changelog_dir / "1774900004.txt").read_text(encoding="utf-8") == "Next patch notes\n"
    assert not (changelog_dir / "1774900003.txt").exists()
    assert release_notes.read_text(encoding="utf-8") == "Next patch notes\n"
