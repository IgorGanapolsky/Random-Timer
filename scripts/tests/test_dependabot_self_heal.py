from __future__ import annotations

import json
from pathlib import Path

from scripts.dependabot_self_heal import (
    alert_package_key,
    build_upgrade_plan,
    parse_lock_versions,
    render_pyproject_pin,
    summarize_open_alerts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dependabot_config_exists_and_covers_uv() -> None:
    path = REPO_ROOT / ".github" / "dependabot.yml"
    assert path.is_file(), "missing .github/dependabot.yml (Dependabot must be repo-configured)"
    text = path.read_text(encoding="utf-8")
    assert "package-ecosystem: uv" in text or 'package-ecosystem: "uv"' in text
    assert "directory: /" in text or 'directory: "/"' in text
    assert "groups:" in text
    assert "security" in text.lower() or "dependencies" in text.lower()


def test_dependabot_automerge_workflow_targets_bot_prs() -> None:
    path = REPO_ROOT / ".github" / "workflows" / "dependabot-automerge.yml"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "dependabot[bot]" in text
    assert "gh pr merge" in text
    assert "--auto" in text
    assert "pull_request_target" in text or "pull_request:" in text
    # Concurrent labeled/opened events race; treat in-progress merge as success.
    assert "Merge already in progress" in text
    assert "concurrency:" in text


def test_dependabot_self_heal_workflow_is_scheduled() -> None:
    path = REPO_ROOT / ".github" / "workflows" / "dependabot-self-heal.yml"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "dependabot_self_heal.py" in text
    assert "workflow_dispatch" in text


def test_alert_package_key_normalizes_casing() -> None:
    assert alert_package_key("Pillow") == "pillow"
    assert alert_package_key("PyJWT") == "pyjwt"


def test_build_upgrade_plan_picks_highest_patched_floor() -> None:
    alerts = [
        {
            "number": 1,
            "security_advisory": {"severity": "high"},
            "security_vulnerability": {
                "package": {"name": "pillow"},
                "vulnerable_version_range": "< 12.3.0",
                "first_patched_version": {"version": "12.3.0"},
            },
            "dependency": {"manifest_path": "uv.lock"},
        },
        {
            "number": 2,
            "security_advisory": {"severity": "high"},
            "security_vulnerability": {
                "package": {"name": "Pillow"},
                "vulnerable_version_range": "< 12.2.0",
                "first_patched_version": {"version": "12.2.0"},
            },
            "dependency": {"manifest_path": "uv.lock"},
        },
    ]
    plan = build_upgrade_plan(alerts)
    assert plan["pillow"]["min_version"] == "12.3.0"
    assert plan["pillow"]["alert_numbers"] == [1, 2]


def test_build_upgrade_plan_infers_floor_from_range_when_patched_null() -> None:
    alerts = [
        {
            "number": 90,
            "security_advisory": {"severity": "high"},
            "security_vulnerability": {
                "package": {"name": "pillow"},
                "vulnerable_version_range": "< 12.3.0",
                "first_patched_version": None,
            },
            "dependency": {"manifest_path": "uv.lock"},
        }
    ]
    plan = build_upgrade_plan(alerts)
    assert plan["pillow"]["min_version"] == "12.3.0"


def test_summarize_open_alerts_dedupes_by_package() -> None:
    alerts = [
        {
            "number": 1,
            "security_advisory": {"severity": "high"},
            "security_vulnerability": {
                "package": {"name": "pillow"},
                "vulnerable_version_range": "< 12.3.0",
                "first_patched_version": {"version": "12.3.0"},
            },
            "dependency": {"manifest_path": "uv.lock"},
        },
        {
            "number": 2,
            "security_advisory": {"severity": "medium"},
            "security_vulnerability": {
                "package": {"name": "Pillow"},
                "vulnerable_version_range": "< 12.3.0",
                "first_patched_version": {"version": "12.3.0"},
            },
            "dependency": {"manifest_path": "pyproject.toml"},
        },
    ]
    summary = summarize_open_alerts(alerts)
    assert summary["open_count"] == 2
    assert summary["unique_packages"] == ["pillow"]
    assert summary["high_or_critical"] == 1


def test_render_pyproject_pin_updates_existing_constraint() -> None:
    src = 'dependencies = [\n    "pillow>=12.2.0,<13",\n]\n'
    out = render_pyproject_pin(src, "pillow", "12.3.0", upper="<13")
    assert '"pillow>=12.3.0,<13"' in out


def test_parse_lock_versions_reads_uv_lock(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(
        'name = "pillow"\nversion = "12.2.0"\n\nname = "pyjwt"\nversion = "2.13.0"\n',
        encoding="utf-8",
    )
    versions = parse_lock_versions(lock)
    assert versions["pillow"] == "12.2.0"
    assert versions["pyjwt"] == "2.13.0"


def test_self_heal_script_is_executable_module() -> None:
    path = REPO_ROOT / "scripts" / "dependabot_self_heal.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "def main(" in text
    assert "--check" in text
    assert "--apply" in text
