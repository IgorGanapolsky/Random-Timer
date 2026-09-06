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


def test_workflow_if_conditions_do_not_reference_secrets_context() -> None:
    offenders: list[str] = []

    for path in sorted((REPO_ROOT / ".github/workflows").glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if line.lstrip().startswith("if:") and "${{ secrets." in line:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_number}")

    assert offenders == []


def test_monthly_pro_release_workflow_has_explicit_ci_guards() -> None:
    contents = _read(".github/workflows/monthly-pro-content-release.yml")

    assert "PROJECT_PAT != ''" not in contents
    assert "github.token" not in contents
    assert "Validate required secrets" in contents
    assert "Missing required secret(s):" in contents
    assert "FREESOUND_API_TOKEN" in contents
    assert "if: ${{ secrets." not in contents
    assert "FREESOUND_API_TOKEN not configured; skipping optional Freesound fetch." in contents
    assert contents.count("timeout-minutes:") >= 4
    assert "actions: write" in contents
    assert "--body \"Auto-generated monthly Pro content update." in contents
    assert '--release-month "${{ steps.meta.outputs.release_month }}"' in contents
    assert "git push origin develop" not in contents
    assert 'gh pr merge "${CONTENT_PR_NUMBER}"' in contents
    assert "--squash" in contents
    assert "--delete-branch" in contents
    assert "/trunk merge" not in contents
    assert 'gh pr comment "${CONTENT_PR_NUMBER}"' not in contents
    assert "-f submit_review=true" in contents
    assert "-f submit_review=false" not in contents
    assert "-f skip_internal_signoff=false" in contents
    assert "-f skip_internal_signoff=true" not in contents
    assert "gh pr create" in contents and "|| true" not in contents.split("gh pr create", 1)[1].split("echo \"changes_committed=true\"", 1)[0]
    assert "Public store availability must still be proven by public-store-version-readback.yml" in contents
    assert "Release branch ${RELEASE_BRANCH} already exists" in contents
    assert "git push origin \"${RELEASE_BRANCH}\" --force-with-lease" in contents


def test_public_store_version_readback_requires_public_evidence() -> None:
    contents = _read(".github/workflows/public-store-version-readback.yml")

    assert "workflow_run:" in contents
    assert 'workflows: ["Native App Release"]' in contents
    assert 'cron: "0 */6 1-7 * *"' in contents
    assert "scripts/verify_public_store_versions.py" in contents
    assert "GH_TOKEN: ${{ github.token }}" in contents
    assert "--json-out public-store-version-readback.json" in contents
    assert "Upload public store read-back evidence" in contents
    assert "workflow_run.head_sha" not in contents


def test_store_console_verification_targets_current_app_and_release_state() -> None:
    workflow = _read(".github/workflows/store-console-verification.yml")
    spec = _read("tests/playwright/specs/store/store-console-readonly.spec.ts")
    agent = _read("tests/playwright/scripts/verify-store-console-agent-browser.mjs")
    readme = _read("tests/playwright/README.md")

    assert "chromium chromium-headless-shell" in workflow
    assert "playwright@1.59.1 install chromium-headless-shell" in workflow
    assert "continue-on-error: true" in workflow
    for contents in (spec, agent):
        assert "play.google.com/console/u/1/developers/8239620436488925047/app/4976249162120849673/publishing" in contents
        assert "play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/publishing" not in contents
        assert "4974974102541773558" not in contents

    assert 'ASC_EXPECTED_STATE_TEXT || ""' in agent
    assert "Primary Playwright ASC verification remains blocking" in agent
    assert 'PLAY_EXPECTED_APP_NAME || "Random Tactical Timer"' in agent
    assert "`ASC_EXPECTED_STATE_TEXT` (optional; when set, the agent-browser check requires this state text)" in readme
    assert "`PLAY_EXPECTED_APP_NAME` (default: `Random Tactical Timer`)" in readme
    sync = _read("tests/playwright/scripts/sync-console-auth-secrets.mjs")
    assert "function filterAscStorageState" in sync
    assert "appstoreconnect\\.apple\\.com" in sync


def test_legacy_monthly_audio_pack_is_manual_only_and_fail_fast() -> None:
    contents = _read(".github/workflows/monthly-audio-pack.yml")

    assert "schedule:" not in contents
    assert "|| true" not in contents
    assert "monthly-pro-content-release.yml" in contents


def test_manual_ios_voice_callout_regen_uses_unique_branch_per_run() -> None:
    contents = _read(".github/workflows/generate-ios-voice-callouts.yml")

    assert "schedule:" not in contents
    assert "GITHUB_RUN_ID" in contents
    assert "GITHUB_RUN_ATTEMPT" in contents
    assert "feat/pro-audio-regen-$(date -u +%Y%m%d)" not in contents


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
    assert "BEFORE_SHA: ${{ github.event.before || '' }}" in ci
    assert "BEFORE_SHA: ${{ github.event.before || '' }}" in device_tests
    assert 'elif [[ "$EVENT_NAME" == "push" && -n "$BEFORE_SHA" && ! "$BEFORE_SHA" =~ ^0+$ ]]; then' in ci
    assert 'elif [[ "$EVENT_NAME" == "push" && -n "$BEFORE_SHA" && ! "$BEFORE_SHA" =~ ^0+$ ]]; then' in device_tests
    assert "python3 scripts/ci_changed_components.py --files /tmp/changed-files.txt --github-output" in ci
    assert "python3 scripts/ci_changed_components.py --files /tmp/changed-files.txt --github-output" in device_tests
    assert "if: needs.changes.outputs.android == 'true'" in ci
    assert "if: needs.changes.outputs.ios == 'true'" in ci
    assert "if: needs.changes.outputs.android_device == 'true'" in device_tests
    assert "if: needs.changes.outputs.ios_device == 'true'" in device_tests
    assert ci.count("timeout-minutes:") >= 9


def test_internal_distribution_requires_signoff_before_testflight_and_firebase_uploads() -> None:
    contents = _read(".github/workflows/internal-distribution.yml")

    ios_signoff = contents.index("ios-testflight-signoff:")
    ios_upload = contents.index("ios-testflight-internal:")
    firebase_signoff = contents.index("android-firebase-signoff:")
    firebase_upload = contents.index("android-firebase-internal:")

    assert ios_signoff < ios_upload
    assert firebase_signoff < firebase_upload
    assert "ios-testflight-internal:\n    name: iOS TestFlight (Internal)\n    needs: [gate, ios-testflight-signoff]" in contents
    assert (
        "android-firebase-internal:\n"
        "    name: Android Firebase (Internal)\n"
        "    needs: [gate, android-firebase-signoff]"
    ) in contents
    assert "needs.ios-testflight-signoff.result == 'success'" in contents
    assert "needs.android-firebase-signoff.result == 'success'" in contents


def test_security_workflow_moves_permissions_to_jobs() -> None:
    contents = _read(".github/workflows/security.yml")
    assert "\npermissions:\n" not in contents.split("jobs:", 1)[0]
    assert "security-scan:\n    runs-on: ubuntu-latest\n    permissions:" in contents
    assert "notify:\n    needs: security-scan\n    if: always()\n    runs-on: ubuntu-latest\n    permissions:" in contents


def test_ci_secret_scan_does_not_scan_all_refs_when_range_is_available() -> None:
    contents = _read(".github/workflows/ci.yml")
    secret_scan = contents.split("- name: Secret Scan", 1)[1].split("\n  autonomous-ai-review:", 1)[0]

    assert 'gitleaks git --no-banner --redact --exit-code 1 --log-opts "$RANGE"' in secret_scan
    assert 'gitleaks git --no-banner --redact --exit-code 1 --log-opts "--all $RANGE"' not in secret_scan
    assert "Scanning full git history fallback" in secret_scan


def test_security_sensitive_workflows_pin_third_party_actions() -> None:
    expected_pins = {
        ".github/workflows/android17-canary.yml": "android-actions/setup-android@40fd30fb8d7440372e1316f5d1809ec01dcd3699 # v4.0.1",
        ".github/workflows/device-tests.yml": "reactivecircus/android-emulator-runner@70f4dee990796918b78d040e3278474bdbd348a7 # v2",
        ".github/workflows/internal-distribution.yml": "ruby/setup-ruby@95ef2b042f9d7a56d8268cba8559e2842e2ad01b # v1.321.0",
        ".github/workflows/internal-distribution.yml#firebase": "wzieba/Firebase-Distribution-Github-Action@bd494989dd4bec0343f78adee87fe66e48279ad6 # v1",
        ".github/workflows/security.yml#snyk": "snyk/actions/node@9adf32b1121593767fc3c057af55b55db032dc04 # master",
        ".github/workflows/security.yml#dependency-check": "dependency-check/Dependency-Check_Action@1e54355a8b4c8abaa8cc7d0b70aa655a3bb15a6c # main",
        ".github/workflows/security.yml#mobsf": "MobSF/mobsfscan@2659f2ac6d185f0c60ce2eb754f5f48b683f73fb # main",
        ".github/workflows/security.yml#slack": "8398a7/action-slack@77eaa4f1c608a7d68b38af4e3f739dcd8cba273e # v3.19.0",
        ".github/workflows/weekly-attribution-feedback.yml": "peter-evans/create-pull-request@5f6978faf089d4d20b00c7766989d076bb2fc7f1 # v8.1.1",
        ".github/workflows/wiki-sync.yml": "Andrew-Chen-Wang/github-wiki-action@1bbb4280446f9630e8e21a18012cbacf3b0f992e # v5.0.6",
        ".github/workflows/pause-paid-campaigns.yml": "peter-evans/create-pull-request@5f6978faf089d4d20b00c7766989d076bb2fc7f1 # v8.1.1",
    }

    assert not (REPO_ROOT / ".github/workflows/release.yml").exists()

    workflow_cache: dict[str, str] = {}
    for keyed_path, pinned_ref in expected_pins.items():
        path = keyed_path.split("#", 1)[0]
        contents = workflow_cache.setdefault(path, _read(path))
        assert pinned_ref in contents, f"{path} is missing {pinned_ref}"


def test_native_release_post_tag_bump_opens_pr_not_direct_push_to_develop() -> None:
    contents = _read(".github/workflows/native-release.yml")
    bump_block = contents.split("bump-develop-version:", 1)[1]
    assert "git push origin develop" not in bump_block
    assert "gh pr create" in bump_block
    assert "pull-requests: write" in bump_block
