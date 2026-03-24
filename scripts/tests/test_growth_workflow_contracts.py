from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
INTERNAL_DISTRIBUTION_WORKFLOW = ROOT / ".github/workflows/internal-distribution.yml"
IOS_INTERNAL_RETRY_WORKFLOW = ROOT / ".github/workflows/ios-internal-retry.yml"
IOS_SUBMIT_REVIEW_WORKFLOW = ROOT / ".github/workflows/ios-submit-review.yml"
NORTH_STAR_GUARDRAIL_WORKFLOW = ROOT / ".github/workflows/north-star-guardrail.yml"
NORTH_STAR_OPS_WORKFLOW = ROOT / ".github/workflows/north-star-ops.yml"
WEEKLY_EXPERIMENT_WORKFLOW = ROOT / ".github/workflows/weekly-north-star-experiment.yml"
WORKFLOW_CONTRACT = ROOT / "docs/workflow.md"


def test_ci_workflow_uses_real_python_suite_and_has_no_legacy_skip_path():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "python -m pytest scripts/tests/ -q" in source
    assert "pytest -q tests/python" not in source
    assert "No tests/python directory found; skipping legacy pytest suite." not in source


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
    assert "TESTFLIGHT_DISTRIBUTE_EXTERNAL: ${{ secrets.TESTFLIGHT_DISTRIBUTE_EXTERNAL || 'false' }}" in source


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


def test_internal_distribution_workflow_supports_targeted_reruns_and_firebase_delivery():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "target:" in source
    assert "android_firebase" in source
    assert "android-firebase-internal" in source or "Android Firebase" in source
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" in source
    assert "FIREBASE_ANDROID_APP_ID" in source
    assert "android-apk-firebase-internal" in source or "app-release.apk" in source
    firebase_section = source.split("- name: Distribute to Firebase", 1)[1].split(
        "- name: Upload Android APK artifact", 1
    )[0]
    assert "continue-on-error: true" not in firebase_section
    assert "Warn on Firebase distribution failure" not in firebase_section

    android_firebase_job = source.split("android-firebase-internal:", 1)[1].split(
        "android-play-internal:", 1
    )[0]
    assert "Write Google Play service account key" not in android_firebase_job
    assert "Verify Google Play API access" not in android_firebase_job
    assert "1:624873778337:android:4503588605a3273edc14e0" not in source
    assert "1:712918404489:android:5fb1dfde1d712f53e7a558" in source


def test_ios_internal_retry_dispatch_targets_ios_only():
    source = IOS_INTERNAL_RETRY_WORKFLOW.read_text(encoding="utf-8")

    assert "-f target=ios" in source


def test_ios_submit_review_workflow_guards_ios_version_lineage():
    source = IOS_SUBMIT_REVIEW_WORKFLOW.read_text(encoding="utf-8")

    assert "check_ios_version_lineage.py" in source
    assert 'python scripts/asc_submit_for_review.py "${SUBMIT_ARGS[@]}"' in source
    assert "fastlane submit_review" not in source


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
