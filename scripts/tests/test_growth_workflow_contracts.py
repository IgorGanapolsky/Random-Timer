from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
INTERNAL_DISTRIBUTION_WORKFLOW = ROOT / ".github/workflows/internal-distribution.yml"
IOS_METADATA_SYNC_WORKFLOW = ROOT / ".github/workflows/ios-metadata-sync.yml"
IOS_INTERNAL_RETRY_WORKFLOW = ROOT / ".github/workflows/ios-internal-retry.yml"
IOS_SUBMIT_REVIEW_WORKFLOW = ROOT / ".github/workflows/ios-submit-review.yml"
NATIVE_RELEASE_WORKFLOW = ROOT / ".github/workflows/native-release.yml"
ANDROID_PRODUCTION_RETRY_WORKFLOW = ROOT / ".github/workflows/android-production-retry.yml"
NORTH_STAR_GUARDRAIL_WORKFLOW = ROOT / ".github/workflows/north-star-guardrail.yml"
NORTH_STAR_OPS_WORKFLOW = ROOT / ".github/workflows/north-star-ops.yml"
WEEKLY_EXPERIMENT_WORKFLOW = ROOT / ".github/workflows/weekly-north-star-experiment.yml"
WORKFLOW_CONTRACT = ROOT / "docs/workflow.md"
DEVICE_TESTS_WORKFLOW = ROOT / ".github/workflows/device-tests.yml"
WEEKLY_SHARED_WORKFLOW = ROOT / ".github/workflows/weekly-shared.yml"
WQTU_HEALTH_WORKFLOW = ROOT / ".github/workflows/wqtu-health.yml"


def test_ci_workflow_uses_real_python_suite_and_has_no_legacy_skip_path():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "python -m pytest scripts/tests/ -q" in source
    assert "pytest -q tests/python" not in source
    assert "No tests/python directory found; skipping legacy pytest suite." not in source


def test_ci_workflow_covers_release_and_hotfix_branches():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [develop, main, 'release/**', 'hotfix/**']" in source


def test_internal_distribution_workflow_verifies_store_uploads_and_uploads_evidence():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "preflight-release" in source or "Preflight release" in source
    assert "ios-testflight-internal" in source or "android-internal" in source
    assert "check_ios_version_lineage.py" in source
    assert "Install App Store Connect Python dependencies" in source
    assert source.index("Install App Store Connect Python dependencies") < source.index(
        "Guard iOS version lineage against ASC"
    )
    assert "Internal Testers" in source
    assert "TESTFLIGHT_GROUPS: ${{ vars.TESTFLIGHT_INTERNAL_GROUPS || secrets.TESTFLIGHT_GROUPS || 'Internal Testers' }}" in source
    assert "TESTFLIGHT_DISTRIBUTE_EXTERNAL: ${{ secrets.TESTFLIGHT_DISTRIBUTE_EXTERNAL || 'false' }}" in source
    assert "Ensure TestFlight internal distribution visibility" in source
    assert "scripts/ensure_internal_distribution.py" in source
    assert "ios-testflight-signoff:" in source
    assert "environment: testflight-signoff" in source
    assert "environment: internal-play" in source
    assert "android-firebase-signoff:" in source
    assert "environment: firebase-signoff" in source
    assert "internal-signoff/testflight" in source
    assert "internal-signoff/firebase" in source


def test_internal_distribution_workflow_keeps_ruby_setup_pin_in_sync_with_native_release():
    internal_source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")
    release_source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    ruby_pin = "ruby/setup-ruby@v1.300.0"
    assert ruby_pin in internal_source
    assert ruby_pin in release_source


def test_internal_distribution_workflow_emits_platform_specific_release_artifacts():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "ios-ipa-internal" in source or "ios-ipa" in source
    assert "android-aab-internal" in source or "android-aab" in source


def test_internal_distribution_workflow_passes_play_json_key_into_distribution_step():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    play_distribute_section = source.split("- name: Distribute to Google Play Internal", 1)[1].split(
        "- name: Verify Play internal track read-back", 1
    )[0]
    assert "env:" in play_distribute_section
    assert "GOOGLE_PLAY_JSON_KEY: ${{ secrets.GOOGLE_PLAY_JSON_KEY }}" in play_distribute_section


def test_internal_distribution_workflow_hardens_play_version_probe_with_timeout_and_retries():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    compute_section = source.split("- name: Compute monotonic Play version code", 1)[1].split(
        "- name: Create google-services.json", 1
    )[0]
    assert "scripts/compute_android_release_version_code.py" in compute_section
    assert "--timeout-seconds 180" in compute_section
    assert "--request-retries 3" in compute_section


def test_internal_distribution_workflow_supports_targeted_reruns_and_firebase_delivery():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "target:" in source
    assert "default: all" in source
    assert "android_firebase" in source
    assert "android-firebase-internal" in source or "Android Firebase" in source
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" in source
    assert "FIREBASE_ANDROID_APP_ID" in source
    assert "android-apk-firebase-internal" in source or "app-release.apk" in source
    assert "groups: ${{ env.FIREBASE_INTERNAL_GROUPS }}" in source
    assert "Verify Firebase distribution read-back" in source
    firebase_section = source.split("- name: Distribute to Firebase", 1)[1].split(
        "- name: Upload Android APK artifact", 1
    )[0]
    assert "continue-on-error: true" not in firebase_section
    assert "Warn on Firebase distribution failure" not in firebase_section

    android_firebase_job = source.split("android-firebase-internal:", 1)[1].split(
        "android-play-internal:", 1
    )[0]
    assert "Setup Python" in android_firebase_job
    assert "python -m pip install --upgrade google-auth==2.48.0 requests==2.32.5" in android_firebase_job
    assert "Write Google Play service account key" not in android_firebase_job
    assert "Verify Google Play API access" not in android_firebase_job
    assert "1:624873778337:android:4503588605a3273edc14e0" not in source
    assert "1:712918404489:android:5fb1dfde1d712f53e7a558" in source


def test_internal_distribution_runs_automatically_on_develop_and_main_push_for_internal_signoff_builds():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "push:" in source
    assert "branches: [develop, main]" in source
    assert "github.event_name == 'workflow_dispatch' || github.event_name == 'push'" in source
    assert 'Automatic internal distribution is only allowed on pushes to develop or main.' in source
    assert 'TARGET="all"' in source
    assert 'REASON="auto_push_develop"' in source
    assert 'REASON="auto_push_main"' in source


def test_ios_internal_retry_dispatch_targets_ios_only():
    source = IOS_INTERNAL_RETRY_WORKFLOW.read_text(encoding="utf-8")

    assert "-f target=ios" in source


def test_ios_submit_review_workflow_guards_ios_version_lineage():
    source = IOS_SUBMIT_REVIEW_WORKFLOW.read_text(encoding="utf-8")

    assert "check_ios_version_lineage.py" in source
    assert 'fastlane metadata version:"$IOS_VERSION" skip_app_version_update:true' in source
    assert 'python scripts/asc/asc_submit_for_review.py "${SUBMIT_ARGS[@]}"' in source
    assert "fastlane submit_review" not in source


def test_ios_metadata_sync_falls_back_to_live_storefront_when_metadata_only_version_is_review_locked():
    source = IOS_METADATA_SYNC_WORKFLOW.read_text(encoding="utf-8")

    resolve_section = source.split("- name: Resolve editable App Store version", 1)[1].split(
        "- name: Strict screenshot replacement + metadata upload", 1
    )[0]
    assert 'if [[ "$IOS_METADATA_ONLY" == "true" ]]' in resolve_section
    assert "from scripts.asc.asc_resolve_version import _is_editable_state" in resolve_section
    assert "selected version state '$SELECTED_STATE' is not editable" in resolve_section
    assert 'SELECTED_VERSION="LIVE"' in resolve_section


def test_native_release_workflow_disables_hidden_play_fallback_and_verifies_requested_platforms_only():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert 'PLAY_FALLBACK_TRACK: ""' in source
    assert "require-internal-signoff:" in source
    assert "require-production-signoff:" in source
    assert "environment: production-signoff" in source
    assert "internal_signoff_gate.py" in source
    assert "(inputs.platform == 'both' && needs.ios-testflight.result == 'success' && needs.android-release.result == 'success')" in source
    assert "(inputs.platform == 'ios' && needs.ios-testflight.result == 'success')" in source
    assert "(inputs.platform == 'android' && needs.android-release.result == 'success')" in source


def test_native_release_workflow_keeps_ios_review_submission_opt_in():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    submit_review_block = source.split("submit_review:", 1)[1].split("concurrency:", 1)[0]
    assert "default: 'false'" in submit_review_block


def test_native_release_workflow_marks_android_firebase_mirror_input_deprecated():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    mirror_block = source.split("android_internal_mirror:", 1)[1].split("submit_review:", 1)[0]
    assert "Deprecated. Internal Firebase signoff must happen before production release." in mirror_block
    assert "default: 'skip'" in mirror_block
    assert "'firebase'" in mirror_block
    assert "'skip'" in mirror_block


def test_native_release_workflow_requires_explicit_confirm_for_ios_only_release_branches():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    confirm_block = source.split("confirm_ios_only_release:", 1)[1].split("concurrency:", 1)[0]
    assert "default: 'false'" in confirm_block
    assert "release-intent-gate:" in source
    assert "RELEASE_INTENT_CONFIRM_IOS_ONLY: ${{ inputs.confirm_ios_only_release }}" in source
    assert "run: python3 scripts/release_intent_gate.py" in source


def test_native_release_workflow_blocks_production_without_internal_signoff_proof():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "require-internal-signoff:" in source
    assert 'gh api "repos/${GITHUB_REPOSITORY}/commits/${GITHUB_SHA}/status"' in source
    assert 'python scripts/internal_signoff_gate.py \\' in source
    assert "require-production-signoff:" in source
    assert "Await fresh CEO production release approval" in source
    assert "needs: [release-intent-gate, require-internal-signoff, require-production-signoff]" in source
    assert "android-firebase-mirror:" not in source


def test_native_release_workflow_verifies_public_play_listing_for_production():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "Verify public Google Play listing (production only)" in source
    assert "python scripts/verify_play_public_listing.py" in source
    assert "--expected-version" in source
    assert "steps.versions.outputs.android_version" in source


def test_native_release_workflow_creates_annotated_release_from_exact_sha():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    tag_block = source.split("tag-release:", 1)[1].split("sync-main:", 1)[0]
    assert "scripts/source_versions.py --repo-root . --format json" in tag_block
    assert "scripts/release_notes.py" in tag_block
    assert 'git tag -a "${{ steps.version.outputs.tag }}" "${GITHUB_SHA}"' in tag_block
    assert '--verify-tag \\' in tag_block
    assert '--target "${GITHUB_SHA}" \\' in tag_block
    assert "### Release metadata" in tag_block


def test_android_production_retry_uses_public_storefront_truth_instead_of_issue_title():
    source = ANDROID_PRODUCTION_RETRY_WORKFLOW.read_text(encoding="utf-8")

    assert "actions/checkout@v6.0.2" in source
    assert "actions/setup-python@v6.2.0" in source
    assert "python -m pip install --upgrade pip requests==2.32.5" in source
    assert "scripts/source_versions.py --format value --key ANDROID_VERSION_NAME" in source
    assert "from scripts.verify_play_public_listing import build_store_url, verify_public_listing" in source
    assert 'build_store_url("com.iganapolsky.randomtimer", "US")' in source
    assert "play_public_current" in source
    assert "play_public_" in source
    assert "ISSUE_TITLE: Android production publish blocked by Play FAILED_PRECONDITION" not in source


def test_ci_workflow_has_dedicated_regression_guards_job():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "regression-guards:" in source
    guard_job = source.split("regression-guards:", 1)[1].split("\n  android:\n", 1)[0]
    assert "python scripts/regression_guards.py --mode ci" in guard_job
    assert "scripts/tests/test_regression_guards.py" in guard_job
    assert "scripts/tests/test_mobile_feature_parity.py" in guard_job
    assert "scripts/tests/test_voice_regression_contracts.py" in guard_job
    assert "TimerRepositoryImplTest" in guard_job
    assert "AIVoiceCalloutManagerSelectionTest" in guard_job


def test_north_star_guardrail_workflow_runs_daily_ops_pipeline():
    source = NORTH_STAR_GUARDRAIL_WORKFLOW.read_text(encoding="utf-8")

    assert "scripts/north_star_guardrail.py" in source
    assert "marketing/data/north_star.json" in source


def test_north_star_ops_workflow_exists_and_runs_report_script():
    source = NORTH_STAR_OPS_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/north_star_ops.py" in source
    assert "north-star-ops-report" in source


def test_weekly_experiment_workflow_builds_a_single_experiment_brief():
    source = WEEKLY_EXPERIMENT_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/north_star_guardrail.py" in source
    assert "python scripts/attribution_feedback.py" in source
    assert "python scripts/north_star_ops.py" in source
    assert "python scripts/north_star_experiment.py" in source
    assert "marketing/data/north_star_experiment.json" in source
    assert "marketing/data/north_star_experiment.md" in source


def test_workflow_contract_exists_and_points_at_canonical_proof_commands():
    source = WORKFLOW_CONTRACT.read_text(encoding="utf-8")

    assert "python3 -m pytest -q scripts/tests/" in source
    assert "cd native-android" in source
    assert "./gradlew testDebugUnitTest" in source
    assert "xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer" in source
    assert "maestro test .maestro/ios-smoke-test.yaml" in source
    assert "scripts/tests" in source
    assert "tests/python" not in source


def test_device_tests_workflow_covers_ios_simulator_maestro_and_agent_device():
    source = DEVICE_TESTS_WORKFLOW.read_text(encoding="utf-8")
    ios_script = (ROOT / "scripts/device-tests/ci-maestro-ios.sh").read_text(encoding="utf-8")
    trigger_section = source.split("concurrency:", 1)[0]

    assert "pull_request:" in trigger_section
    assert "branches: [develop, main]" in trigger_section
    assert "paths:" not in trigger_section
    assert "iOS Simulator + Maestro + Agent Device" in source
    assert "scripts/device-tests/ci-maestro-ios.sh" in source
    assert "agent-device" in source
    assert "native-ios/build/device-tests-ios" not in source
    assert "regression-free-sound-preview-ios.yaml" in ios_script
    assert "regression-sound-arsenal-paywall-ios.yaml" in ios_script
    assert "retry_agent_device_capture" in ios_script
    assert "AGENT_DEVICE_SESSION" in ios_script
    assert "MAESTRO_DRIVER_STARTUP_TIMEOUT=300000" in ios_script
    assert "run_maestro_flow" in ios_script
    assert "Reset app state before Agent Device validates the home screen" in ios_script
    assert "xcrun simctl uninstall \"$SIMULATOR_UDID\" \"$BUNDLE_ID\"" in ios_script
    assert ios_script.index("regression-sound-arsenal-paywall-ios.yaml") < ios_script.index("retry_agent_device \"wait-home\"")


def test_weekly_shared_workflow_closes_prior_report_issue_before_creating_next_one():
    source = WEEKLY_SHARED_WORKFLOW.read_text(encoding="utf-8")

    assert "Close stale automated report issues" in source
    assert '--search "\\"${ISSUE_TITLE}\\" in:title"' in source
    assert 'jq -r --arg issue_title "$ISSUE_TITLE"' in source
    assert "select(.title == $issue_title)" in source
    assert "Closing previous automated report issue before publishing refreshed weekly output." in source


def test_wqtu_health_workflow_closes_prior_alert_issue_before_creating_next_one():
    source = WQTU_HEALTH_WORKFLOW.read_text(encoding="utf-8")

    assert '"⚠️ WQTU Alert:" in:title' in source
    assert 'select(.title | startswith("⚠️ WQTU Alert:"))' in source
    assert "Closing previous weekly WQTU alert before publishing refreshed weekly output." in source


def test_dead_play_precondition_stub_is_removed():
    assert not (ROOT / "scripts/play_precondition_triage.py").exists()


def test_ci_crashlytics_job_uses_dedicated_runtime_secret_and_is_not_best_effort():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    crashlytics_section = source.split("crashlytics:", 1)[1].split("notify:", 1)[0]
    assert "CRASHLYTICS_SERVICE_ACCOUNT_JSON" in crashlytics_section
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" not in crashlytics_section
    assert "google-github-actions/auth" not in crashlytics_section
    assert "google-auth==" in crashlytics_section
    assert "Missing CRASHLYTICS_SERVICE_ACCOUNT_JSON secret" in crashlytics_section
    assert "continue-on-error: true" not in crashlytics_section
