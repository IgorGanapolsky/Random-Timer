from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_pause_paid_campaigns_uses_environment_backed_reason() -> None:
    contents = _read(".github/workflows/pause-paid-campaigns.yml")
    assert 'INPUT_REASON: ${{ inputs.reason }}' in contents
    assert '--reason "$INPUT_REASON"' in contents


def test_security_workflow_moves_permissions_to_jobs() -> None:
    contents = _read(".github/workflows/security.yml")
    assert "\npermissions:\n" not in contents.split("jobs:", 1)[0]
    assert "security-scan:\n    runs-on: ubuntu-latest\n    permissions:" in contents
    assert "notify:\n    needs: security-scan\n    if: always()\n    runs-on: ubuntu-latest\n    permissions:" in contents


def test_security_sensitive_workflows_pin_third_party_actions() -> None:
    expected_pins = {
        ".github/workflows/android17-canary.yml": "android-actions/setup-android@9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407",
        ".github/workflows/device-tests.yml": "reactivecircus/android-emulator-runner@70f4dee990796918b78d040e3278474bdbd348a7",
        ".github/workflows/internal-distribution.yml": "ruby/setup-ruby@e5517072e87f198d9533967ae13d97c11b604005",
        ".github/workflows/internal-distribution.yml#firebase": "wzieba/Firebase-Distribution-Github-Action@bd494989dd4bec0343f78adee87fe66e48279ad6",
        ".github/workflows/release.yml#expo": "expo/expo-github-action@c7b66a9c327a43a8fa7c0158e7f30d6040d2481e",
        ".github/workflows/release.yml#sbom": "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610",
        ".github/workflows/release.yml#gh-release": "softprops/action-gh-release@153bb8e04406b158c6c84fc1615b65b24149a1fe",
        ".github/workflows/release.yml#slack": "8398a7/action-slack@047b09b154480ed39076984b64f324fff010d703",
        ".github/workflows/security.yml#snyk": "snyk/actions/node@9adf32b1121593767fc3c057af55b55db032dc04",
        ".github/workflows/security.yml#dependency-check": "dependency-check/Dependency-Check_Action@1e54355a8b4c8abaa8cc7d0b70aa655a3bb15a6c",
        ".github/workflows/security.yml#mobsf": "MobSF/mobsfscan@ec2927a8cfab6626a67f26b223be3aba52a34b70",
        ".github/workflows/security.yml#slack": "8398a7/action-slack@047b09b154480ed39076984b64f324fff010d703",
        ".github/workflows/weekly-attribution-feedback.yml": "peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c",
        ".github/workflows/wiki-sync.yml": "Andrew-Chen-Wang/github-wiki-action@50650fccf3a10f741995523cf9708c53cec8912a",
        ".github/workflows/pause-paid-campaigns.yml": "peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c",
    }

    workflow_cache: dict[str, str] = {}
    for keyed_path, pinned_ref in expected_pins.items():
        path = keyed_path.split("#", 1)[0]
        contents = workflow_cache.setdefault(path, _read(path))
        assert pinned_ref in contents, f"{path} is missing {pinned_ref}"
