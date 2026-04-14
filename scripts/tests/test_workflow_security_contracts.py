from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_pause_paid_campaigns_uses_environment_backed_reason() -> None:
    contents = _read(".github/workflows/pause-paid-campaigns.yml")
    assert 'INPUT_REASON: ${{ inputs.reason }}' in contents
    assert '--reason "$INPUT_REASON"' in contents


def test_workflow_inputs_are_not_interpolated_inside_run_blocks() -> None:
    offenders: list[str] = []

    for path in sorted((REPO_ROOT / ".github/workflows").glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        active_run_indent: int | None = None
        for line_number, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if active_run_indent is not None:
                if stripped and indent <= active_run_indent:
                    active_run_indent = None
                elif "${{ inputs." in line:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_number}")

            if stripped.startswith("run: |") or stripped.startswith("run: >"):
                active_run_indent = indent

    assert offenders == []


def test_monthly_pro_release_workflow_has_explicit_ci_guards() -> None:
    contents = _read(".github/workflows/monthly-pro-content-release.yml")

    assert "PROJECT_PAT != ''" not in contents
    assert "github.token" not in contents
    assert "Validate required secrets" in contents
    assert "Missing required secret(s):" in contents
    assert "FREESOUND_API_TOKEN" in contents
    assert contents.count("timeout-minutes:") >= 4
    assert "actions: write" in contents
    assert "--body \"Auto-generated monthly Pro content update." in contents
    assert "gh pr create" in contents and "|| true" not in contents.split("gh pr create", 1)[1].split("echo \"changes_committed=true\"", 1)[0]


def test_public_store_version_readback_requires_public_evidence() -> None:
    contents = _read(".github/workflows/public-store-version-readback.yml")

    assert "workflow_run:" in contents
    assert 'workflows: ["Native App Release"]' in contents
    assert 'cron: "0 */6 1-7 * *"' in contents
    assert "scripts/verify_public_store_versions.py" in contents
    assert "--json-out public-store-version-readback.json" in contents
    assert "Upload public store read-back evidence" in contents
    assert "workflow_run.head_sha" not in contents


def test_legacy_monthly_audio_pack_is_manual_only_and_fail_fast() -> None:
    contents = _read(".github/workflows/monthly-audio-pack.yml")

    assert "schedule:" not in contents
    assert "|| true" not in contents
    assert "monthly-pro-content-release.yml" in contents


def test_release_automerge_uses_default_token_before_pat_fallback() -> None:
    contents = _read(".github/workflows/autonomous-release-automerge.yml")

    assert 'GH_TOKEN="${PROJECT_PAT:-$DEFAULT_TOKEN}"' not in contents
    assert "timeout-minutes: 5" in contents
    assert contents.index('enable_automerge "GITHUB_TOKEN" "$DEFAULT_TOKEN"') < contents.index(
        'enable_automerge "PROJECT_PAT fallback" "${PROJECT_PAT:-}"'
    )


def test_pr_ci_uses_path_aware_heavy_job_gates() -> None:
    ci = _read(".github/workflows/ci.yml")
    device_tests = _read(".github/workflows/device-tests.yml")

    assert "\npermissions:\n" not in ci.split("concurrency:", 1)[0]
    assert "\npermissions:\n" not in device_tests.split("concurrency:", 1)[0]
    assert ci.count("permissions:\n      contents: read") >= 9
    assert device_tests.count("permissions:\n      contents: read") >= 3
    assert "Path-Aware CI Gate" in ci
    assert "Path-Aware Device Gate" in device_tests
    assert "python3 scripts/ci_changed_components.py --files /tmp/changed-files.txt --github-output" in ci
    assert "python3 scripts/ci_changed_components.py --files /tmp/changed-files.txt --github-output" in device_tests
    assert "if: needs.changes.outputs.android == 'true'" in ci
    assert "if: needs.changes.outputs.ios == 'true'" in ci
    assert "if: needs.changes.outputs.android_device == 'true'" in device_tests
    assert "if: needs.changes.outputs.ios_device == 'true'" in device_tests
    assert ci.count("timeout-minutes:") >= 9


def test_security_workflow_moves_permissions_to_jobs() -> None:
    contents = _read(".github/workflows/security.yml")
    assert "\npermissions:\n" not in contents.split("jobs:", 1)[0]
    assert "security-scan:\n    runs-on: ubuntu-latest\n    permissions:" in contents
    assert "notify:\n    needs: security-scan\n    if: always()\n    runs-on: ubuntu-latest\n    permissions:" in contents


def test_security_sensitive_workflows_pin_third_party_actions() -> None:
    expected_pins = {
        ".github/workflows/android17-canary.yml": "android-actions/setup-android@9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407",
        ".github/workflows/device-tests.yml": "reactivecircus/android-emulator-runner@70f4dee990796918b78d040e3278474bdbd348a7",
        ".github/workflows/internal-distribution.yml": "ruby/setup-ruby@e65c17d16e57e481586a6a5a0282698790062f92 # v1.300.0",
        ".github/workflows/internal-distribution.yml#firebase": "wzieba/Firebase-Distribution-Github-Action@bd494989dd4bec0343f78adee87fe66e48279ad6",
        ".github/workflows/security.yml#snyk": "snyk/actions/node@9adf32b1121593767fc3c057af55b55db032dc04",
        ".github/workflows/security.yml#dependency-check": "dependency-check/Dependency-Check_Action@1e54355a8b4c8abaa8cc7d0b70aa655a3bb15a6c",
        ".github/workflows/security.yml#mobsf": "MobSF/mobsfscan@ec2927a8cfab6626a67f26b223be3aba52a34b70",
        ".github/workflows/security.yml#slack": "8398a7/action-slack@047b09b154480ed39076984b64f324fff010d703",
        ".github/workflows/weekly-attribution-feedback.yml": "peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c",
        ".github/workflows/wiki-sync.yml": "Andrew-Chen-Wang/github-wiki-action@50650fccf3a10f741995523cf9708c53cec8912a",
        ".github/workflows/pause-paid-campaigns.yml": "peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c",
    }

    assert not (REPO_ROOT / ".github/workflows/release.yml").exists()

    workflow_cache: dict[str, str] = {}
    for keyed_path, pinned_ref in expected_pins.items():
        path = keyed_path.split("#", 1)[0]
        contents = workflow_cache.setdefault(path, _read(path))
        assert pinned_ref in contents, f"{path} is missing {pinned_ref}"
