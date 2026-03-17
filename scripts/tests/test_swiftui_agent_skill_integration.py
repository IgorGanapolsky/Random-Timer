from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
MAKEFILE = ROOT / "Makefile"
DOC = ROOT / "docs" / "SWIFTUI_AGENT_SKILL.md"
INSTALLER = ROOT / "scripts" / "install-swiftui-agent-skill.sh"
VERIFIER = ROOT / "scripts" / "verify-swiftui-agent-skill.sh"


def test_readme_links_to_swiftui_skill_guide():
    source = README.read_text(encoding="utf-8")
    assert "docs/SWIFTUI_AGENT_SKILL.md" in source


def test_makefile_exposes_swiftui_skill_targets():
    source = MAKEFILE.read_text(encoding="utf-8")
    assert "swiftui-skill-install:" in source
    assert "swiftui-skill-verify:" in source


def test_swiftui_skill_doc_scopes_usage():
    source = DOC.read_text(encoding="utf-8")
    assert "SwiftUI-Agent-Skill" in source
    assert "$0" in source
    assert "SwiftUI" in source
    assert "Do not use this skill for release" in source
    assert "make swiftui-skill-install" in source
    assert "make swiftui-skill-verify" in source


def test_installer_script_uses_upstream_skill_installer_and_repo_path():
    source = INSTALLER.read_text(encoding="utf-8")
    assert "skill-installer" in source
    assert "twostraws/SwiftUI-Agent-Skill" in source
    assert "swiftui-pro" in source
    assert "CODEX_HOME" in source


def test_verifier_script_checks_expected_skill_layout():
    source = VERIFIER.read_text(encoding="utf-8")
    assert "SKILL.md" in source
    assert "agents" in source
    assert "references" in source
    assert "swiftui-pro" in source
