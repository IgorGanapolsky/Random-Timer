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
IOS_SMOKE_FLOW = ROOT / ".maestro/ios-smoke-test.yaml"
WEEKLY_SHARED_WORKFLOW = ROOT / ".github/workflows/weekly-shared.yml"
WQTU_HEALTH_WORKFLOW = ROOT / ".github/workflows/wqtu-health.yml"
ANALYTICS_WORKFLOW = ROOT / ".github/workflows/analytics.yml"
EXECUTIVE_METRICS_WORKFLOW = ROOT / ".github/workflows/executive-metrics.yml"
PLAY_IAP_READBACK_WORKFLOW = ROOT / ".github/workflows/play-iap-product-readback.yml"
WIKI_SYNC_WORKFLOW = ROOT / ".github/workflows/wiki-sync.yml"
ACTIONS_BUDGET_DOC = ROOT / "docs/ACTIONS_BUDGET.md"
STORE_RATINGS_SNAPSHOT_WORKFLOW = ROOT / ".github/workflows/store-ratings-snapshot.yml"
ADMOB_APP_ADS_VERIFY_WORKFLOW = ROOT / ".github/workflows/admob-app-ads-verify.yml"
AGENTS_DOC = ROOT / "AGENTS.md"
ANDROID_AGENT_WORKFLOW_DOC = ROOT / "docs/ANDROID_AGENT_WORKFLOW.md"


def test_admob_app_ads_verify_workflow_checks_hosted_files():
    source = ADMOB_APP_ADS_VERIFY_WORKFLOW.read_text(encoding="utf-8")

    assert "admob_status.py" in source
    assert "admob_metrics_snapshot.py" in source
    assert "--also-check-play-contact-path" in source
    assert "contents: write" in source
    assert "marketing/data/admob_status.json" in source


def test_store_ratings_snapshot_workflow_invokes_script_with_read_only_secrets():
    source = STORE_RATINGS_SNAPSHOT_WORKFLOW.read_text(encoding="utf-8")

    assert "store_ratings_snapshot.py" in source
    assert "--no-dotenv" in source
    assert "APPSTORE_KEY_ID" in source
    assert "GOOGLE_PLAY_JSON_KEY" in source
    assert "contents: read" in source


def test_android_agent_workflow_documents_official_cli_skills_and_docs_without_ci_lock_in():
    agents = AGENTS_DOC.read_text(encoding="utf-8")
    workflow = ANDROID_AGENT_WORKFLOW_DOC.read_text(encoding="utf-8")

    assert "scripts/android_agent_doctor.py --json" in agents
    assert "docs/ANDROID_AGENT_WORKFLOW.md" in agents
    assert "android docs search" in agents
    assert "android skills" in agents
    assert "Do not make preview Android CLI tooling a hard CI dependency" in agents
    assert "android update" in workflow
    assert "cd native-android && ./gradlew testDebugUnitTest lint" in workflow
    assert "never remove foreground service permissions" in workflow


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
    assert 'TESTFLIGHT_DISTRIBUTE_EXTERNAL: "false"' in source
    assert 'TESTFLIGHT_NOTIFY_EXTERNAL_TESTERS: "false"' in source
    assert "TESTFLIGHT_REQUIRED_TESTERS: ${{ vars.TESTFLIGHT_INTERNAL_TESTERS || secrets.TESTFLIGHT_INTERNAL_TESTERS || '' }}" in source
    assert "TESTFLIGHT_INTERNAL_TESTERS must include the CEO/TestFlight Apple ID" in source
    assert "secrets.FIREBASE_REQUIRED_TESTER_EMAIL" not in source.split("Ensure TestFlight internal distribution visibility", 1)[1].split(
        "Upload IPA artifact", 1
    )[0]
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

    ruby_pin = "ruby/setup-ruby@95ef2b042f9d7a56d8268cba8559e2842e2ad01b # v1.321.0"
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


def test_internal_distribution_workflow_preflights_play_fgs_declaration_before_build():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "Preflight Play foreground service declaration" in source
    assert "scripts/check_android_play_fgs_declaration.py" in source
    assert "PLAY_FGS_DECLARATION_ACK" in source
    assert source.index("Preflight Play foreground service declaration") < source.index("Build release Bundle (AAB)")


def test_internal_distribution_workflow_hardens_play_version_probe_with_timeout_and_retries():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    compute_section = source.split("- name: Compute monotonic Play version code", 1)[1].split(
        "- name: Create google-services.json", 1
    )[0]
    assert "scripts/compute_android_release_version_code.py" in compute_section
    assert "--timeout-seconds 180" in compute_section
    assert "--request-retries 3" in compute_section


def test_internal_distribution_skips_impossible_auto_ios_uploads_without_signoff():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    signoff_index = source.index("ios-testflight-signoff:")
    upload_index = source.index("ios-testflight-internal:")
    assert signoff_index < upload_index

    signoff_job = source.split("ios-testflight-signoff:", 1)[1].split("ios-testflight-internal:", 1)[0]
    ios_job = source.split("ios-testflight-internal:", 1)[1].split("android-play-internal:", 1)[0]

    assert "needs: [gate]" in signoff_job
    assert "environment:" in signoff_job
    assert "testflight-signoff" in signoff_job
    assert "needs: [gate, ios-testflight-signoff]" in ios_job
    assert "needs.ios-testflight-signoff.result == 'success'" in ios_job
    assert "uploaded: ${{ steps.ios_lineage.outputs.uploadable }}" in ios_job
    assert "DISTRIBUTION_REASON: ${{ needs.gate.outputs.reason }}" in ios_job
    assert "blocked by (closed|a distribution-locked) App Store version" in ios_job
    assert "Skipping automatic iOS TestFlight upload" in ios_job
    assert "Record skipped iOS TestFlight upload" in ios_job
    assert "if: steps.ios_lineage.outputs.uploadable == 'true'" in ios_job


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
    firebase_auth_section = source.split("- name: Fail fast on Firebase distribution auth inputs", 1)[1].split(
        "- name: Preflight release checks (Android)", 1
    )[0]
    assert "FIREBASE_REQUIRED_TESTER_EMAIL: ${{ secrets.FIREBASE_REQUIRED_TESTER_EMAIL }}" in firebase_auth_section
    assert "FIREBASE_REQUIRED_TESTER_EMAIL must include the CEO Android tester email" in firebase_auth_section
    assert "COMBINED_FIREBASE_TESTERS" in firebase_auth_section
    assert 'os.environ.get("FIREBASE_REQUIRED_TESTER_EMAIL", "")' in firebase_auth_section
    assert 'echo "FIREBASE_INTERNAL_TESTERS=${COMBINED_FIREBASE_TESTERS}" >> "$GITHUB_ENV"' in firebase_auth_section
    firebase_section = source.split("- name: Distribute to Firebase", 1)[1].split(
        "- name: Upload Android APK artifact", 1
    )[0]
    assert "continue-on-error: true" not in firebase_section
    assert "Warn on Firebase distribution failure" not in firebase_section
    assert "FIREBASE_REQUIRED_TESTER_EMAIL" not in firebase_section
    assert '--firebase-required-testers "$FIREBASE_INTERNAL_TESTERS"' in firebase_section

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


def test_ios_metadata_sync_fails_fast_when_no_editable_app_store_version():
    source = IOS_METADATA_SYNC_WORKFLOW.read_text(encoding="utf-8")

    resolve_section = source.split("- name: Resolve editable App Store version", 1)[1].split(
        "- name: Strict screenshot replacement + metadata upload", 1
    )[0]
    upload_section = source.split("- name: Strict screenshot replacement + metadata upload", 1)[1].split(
        "- name: Upload readiness report", 1
    )[0]
    assert "asc_resolve_version.py" in resolve_section
    assert "from scripts.asc.asc_resolve_version import _is_editable_state" in resolve_section
    assert "Blocked on ASC" in resolve_section
    assert "asc_list_versions.py" in resolve_section
    assert 'SELECTED_VERSION="LIVE"' not in resolve_section
    assert "use_live_version:true" not in upload_section
    assert "asc_strict_screenshot_sync.py" in upload_section


def test_native_release_workflow_disables_hidden_play_fallback_and_verifies_requested_platforms_only():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert 'PLAY_FALLBACK_TRACK: ""' in source
    assert "internal-proof-or-waive:" in source
    assert "require-production-signoff:" in source
    assert "production-signoff-waive:" in source
    assert "environment: production-signoff" in source
    assert "internal_signoff_gate.py" in source
    assert "(inputs.platform == 'both' && needs.ios-testflight.result == 'success' && needs.android-release.result == 'success')" in source
    assert "(inputs.platform == 'ios' && needs.ios-testflight.result == 'success')" in source
    assert "(inputs.platform == 'android' && needs.android-release.result == 'success')" in source


def test_native_release_workflow_keeps_ios_review_submission_opt_in():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    submit_review_block = source.split("submit_review:", 1)[1].split("concurrency:", 1)[0]
    assert "default: 'false'" in submit_review_block


def test_native_release_ios_submit_review_resolves_version_even_when_review_locked():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    resolve_block = source.split("- name: Resolve editable App Store version", 1)[1].split(
        "- name: Write App Store Connect key (for API)", 1
    )[0]
    assert "asc_resolve_version.py" in resolve_block
    assert "--allow-review-locked-preferred" in resolve_block


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


def test_native_release_workflow_blocks_production_without_internal_signoff_proof_by_default():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "internal-proof-or-waive:" in source
    assert "skip_internal_signoff:" in source
    assert "skip_production_signoff:" in source
    assert "Internal artifact proof cannot be waived for production release." in source
    assert "Every release must have current internal-signoff/testflight and/or internal-signoff/firebase statuses" in source
    assert 'gh api "repos/${GITHUB_REPOSITORY}/commits/${GITHUB_SHA}/status"' in source
    assert "python3 scripts/internal_signoff_gate.py" in source
    assert "require-production-signoff:" in source
    assert "production-signoff-waive:" in source
    assert "Await fresh CEO production release approval" in source
    assert "internal-proof-or-waive" in source.split("ios-testflight:", 1)[1].split("android-release:", 1)[0]
    assert "require-production-signoff" in source.split("ios-testflight:", 1)[1].split("android-release:", 1)[0]
    assert "android-firebase-mirror:" not in source


def test_native_release_workflow_treats_public_play_listing_as_non_blocking_release_evidence():
    source = NATIVE_RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "Verify public Google Play listing (production only)" in source
    assert "id: play_public_listing" in source
    assert "continue-on-error: true" in source
    assert "python scripts/verify_play_public_listing.py" in source
    assert "--expected-version" in source
    assert "steps.versions.outputs.android_version" in source
    assert "Warn when Play storefront propagation lags production" in source
    assert "play-public-listing-report" in source


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

    assert "actions/checkout@v7" in source
    assert "actions/setup-python@v7" in source
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


def test_ci_north_star_guardrail_only_requires_posthog_when_paid_campaigns_are_active():
    source = CI_WORKFLOW.read_text(encoding="utf-8")
    guard_job = source.split("north-star-guardrail:", 1)[1].split("\n  security:\n", 1)[0]

    assert "--require-posthog-when-active" in guard_job
    assert "--require-posthog\n" not in guard_job


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

    assert "cancel-in-progress: true" in source
    assert "pull_request:" in trigger_section
    assert "branches: [develop, main, 'release/**', 'hotfix/**']" in trigger_section
    assert "paths:" not in trigger_section
    assert "iOS Simulator + Maestro + Agent Device" in source
    assert "scripts/device-tests/ci-maestro-ios.sh" in source
    assert "agent-device" in source
    assert "native-ios/build/device-tests-ios" not in source
    assert "regression-free-sound-preview-ios.yaml" in ios_script
    assert "regression-sound-arsenal-paywall-ios.yaml" in ios_script
    assert "CI_IOS_DEVICE_TIER" in ios_script
    assert "CI_IOS_DEVICE_TIER:" in source
    assert "workflow_dispatch' && 'full' || 'smoke'" in source
    assert "retry_agent_device_capture" in ios_script
    assert "AGENT_DEVICE_SESSION" in ios_script
    assert "MAESTRO_DRIVER_STARTUP_TIMEOUT=300000" in ios_script
    assert "run_with_timeout" in ios_script
    assert "IOS_BUILD_TIMEOUT_SECONDS" in ios_script
    assert "MAESTRO_FLOW_TIMEOUT_SECONDS" in ios_script
    assert "AGENT_DEVICE_TIMEOUT_SECONDS" in ios_script
    assert "AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS" in ios_script
    assert "SIMCTL_TIMEOUT_SECONDS" in ios_script
    assert "last-stage.txt" in ios_script
    assert "record_stage" in ios_script
    assert "run_maestro_flow" in ios_script
    assert "run_with_timeout \"$IOS_BUILD_TIMEOUT_SECONDS\" xcodebuild build" in ios_script
    assert "run_with_timeout \"$MAESTRO_FLOW_TIMEOUT_SECONDS\" bash -o pipefail -c" in ios_script
    assert "MAESTRO_FLOW_TIMEOUT_SECONDS:-180" in ios_script
    assert "xcrun simctl privacy \"$SIMULATOR_UDID\" grant notifications \"$BUNDLE_ID\"" in ios_script
    assert "xcrun simctl terminate \"$SIMULATOR_UDID\" \"$BUNDLE_ID\"" in ios_script
    assert "run_with_timeout \"$seconds\" npx -y agent-device" in ios_script
    assert "Reset app state before Agent Device validates the home screen" in ios_script
    assert "xcrun simctl uninstall \"$SIMULATOR_UDID\" \"$BUNDLE_ID\"" in ios_script
    assert "home-pre-agent.png" in ios_script
    assert "Simulator home screenshot was not captured." in ios_script
    assert "retry_agent_device \"wait-home\"" not in ios_script
    assert "Random Tactical Timer|Start First Drill|Start Timer|Timer Range" in ios_script
    assert ios_script.index("regression-sound-arsenal-paywall-ios.yaml") < ios_script.index("agent-device diagnostic screenshot")
    assert "retry_agent_device_capture \"snapshot\" \"$AGENT_DEVICE_TIMEOUT_SECONDS\"" not in ios_script
    assert "retry_agent_device \"install\" \"$AGENT_DEVICE_TIMEOUT_SECONDS\" install" in ios_script
    assert "retry_agent_device \"install\" \"$AGENT_DEVICE_TIMEOUT_SECONDS\" agent_device" not in ios_script
    assert "Agent Device screenshot/snapshot can hang or focus its runner shell" in ios_script
    assert "agent-device diagnostic screenshot" in ios_script
    assert "agent-device diagnostic snapshot" in ios_script
    assert "run_with_timeout \"$AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS\" npx -y agent-device" in ios_script
    assert "::warning::Agent Device snapshot did not include expected home anchors" in ios_script
    assert "retry_agent_device \"screenshot\"" not in ios_script
    assert "retry_agent_device_capture \"snapshot\"" not in ios_script


def test_ios_maestro_regression_flows_use_bounded_scrolls_and_concrete_lock_anchors():
    pro_locks = (ROOT / ".maestro/regression-pro-locks-visible-ios.yaml").read_text(encoding="utf-8")
    free_preview = (ROOT / ".maestro/regression-free-sound-preview-ios.yaml").read_text(encoding="utf-8")
    paywall = (ROOT / ".maestro/regression-sound-arsenal-paywall-ios.yaml").read_text(encoding="utf-8")
    voice_focus = (ROOT / ".maestro/regression-voice-focus-ios.yaml").read_text(encoding="utf-8")
    pro_preview = (ROOT / ".maestro/regression-pro-sound-preview-not-paywall-ios.yaml").read_text(encoding="utf-8")

    assert "Unlock Voice Callouts" in pro_locks
    assert "Unlock Sound Arsenal" in pro_locks
    assert "timeout: 10000" in pro_locks
    assert "timeout: 10000" in free_preview
    assert "timeout: 10000" in paywall
    assert 'element: "Unlock Sound Arsenal"' in free_preview
    assert 'element: "SOUND ARSENAL"' not in free_preview
    assert "Klaxon" in free_preview
    assert "Gentle.*" not in free_preview
    assert 'element: "Unlock Sound Arsenal"' in paywall
    assert 'element: "SOUND ARSENAL"' not in paywall
    assert "- stopApp" in pro_locks
    assert "- stopApp" in free_preview
    assert "- stopApp" in paywall
    assert "timeout: 10000" in voice_focus
    assert pro_preview.count("timeout: 10000") >= 2
    assert 'element: "Unlock Sound Arsenal"' in pro_preview
    assert 'element: "SOUND ARSENAL"' not in pro_preview
    assert "Klaxon" in pro_preview


def test_ios_smoke_flow_avoids_flaky_post_start_hierarchy_queries():
    source = IOS_SMOKE_FLOW.read_text(encoding="utf-8")

    assert "- tapOn: 'Start First Drill'" in source
    assert "- stopApp" in source
    assert ".*Timer running.*" not in source
    assert "text: 'Pause'" not in source
    assert "text: 'Stop'" not in source


def test_weekly_shared_workflow_closes_prior_report_issue_before_creating_next_one():
    source = WEEKLY_SHARED_WORKFLOW.read_text(encoding="utf-8")

    assert "Close stale automated report issues" in source
    assert '--search "\\"${ISSUE_TITLE}\\" in:title"' in source
    assert 'jq -r --arg issue_title "$ISSUE_TITLE"' in source
    assert "select(.title == $issue_title)" in source
    assert "Closing previous automated report issue before publishing refreshed weekly output." in source


def test_analytics_workflow_uploads_reports_as_artifacts_not_open_issues():
    source = ANALYTICS_WORKFLOW.read_text(encoding="utf-8")

    assert "issue_title: Weekly CI/CD Performance Report" not in source
    assert "issue_title: Weekly Security Metrics Report" not in source
    assert "issue_title: Weekly Deployment Metrics Report" not in source
    assert "artifact_name: weekly-cicd-performance-report" in source
    assert "artifact_name: weekly-security-metrics-report" in source
    assert "artifact_name: weekly-deployment-metrics-report" in source


def test_analytics_deployment_report_reads_deployment_statuses():
    source = ANALYTICS_WORKFLOW.read_text(encoding="utf-8")

    assert "/deployments/{deployment['id']}/statuses?per_page=1" in source
    assert 'latest_state = statuses[0]["state"] if statuses else "unknown"' in source
    assert '.state == "success"' not in source


def test_wiki_sync_refreshes_posthog_snapshots_and_commits_marketing_data():
    source = WIKI_SYNC_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/paywall_conversion_report.py --repo-root . --days 30" in source
    assert "python scripts/attribution_feedback.py --repo-root . --days 30" in source
    assert "python scripts/north_star_guardrail.py" in source
    assert "python scripts/store_downloads_snapshot.py --repo-root . --days 30" in source
    assert "Commit refreshed marketing analytics snapshots" in source
    assert "marketing/data/paywall_conversion_report.json" in source
    assert "marketing/data/north_star.json" in source
    assert "wiki/Daily-Metrics-Dashboard.md" in source
    assert "wiki/Paid-Acquisition.md" in source
    assert "marketing/keywords/posthog_feedback.json" in source
    assert "git add marketing/data" in source
    assert "git pull --rebase origin develop" in source


def test_analytics_workflow_publishes_weekly_paywall_conversion_report_artifact():
    source = ANALYTICS_WORKFLOW.read_text(encoding="utf-8")

    assert "analyze-paywall-conversion:" in source
    assert "python scripts/paywall_conversion_report.py --repo-root . --days 30" in source
    assert "pip_packages: requests==2.32.5" in source
    assert "artifact_name: weekly-paywall-conversion-report" in source
    assert "marketing/data/paywall_conversion_report.md" in source
    assert "marketing/data/paywall_conversion_report.json" in source


def test_play_iap_readback_workflow_scheduled_on_develop():
    source = PLAY_IAP_READBACK_WORKFLOW.read_text(encoding="utf-8")

    assert "schedule:" in source
    assert 'cron: "45 7 * * *"' in source
    assert "play_verify_iap_products.py" in source
    assert "play_activate_iap_products.py" in source
    assert 'PYTHONPATH: ${{ github.workspace }}' in source
    assert "GOOGLE_PLAY_JSON_KEY" in source
    assert "marketing/data/play_iap_catalog.json" in source
    assert "contents: write" in source


def test_wiki_sync_builds_wqtu_health_snapshot():
    source = WIKI_SYNC_WORKFLOW.read_text(encoding="utf-8")

    assert "wqtu_dashboard.py" in source
    assert "marketing/data" in source


def test_executive_metrics_workflow_runs_daily_and_guards_ios_refund_signal():
    source = EXECUTIVE_METRICS_WORKFLOW.read_text(encoding="utf-8")

    assert "schedule:" in source
    assert "cron: '17 6 * * *'" in source
    assert "workflow_dispatch:" in source
    assert "Verify iOS refund ground-truth signal" in source
    assert "python3 - <<'PY'" in source
    assert "refunds.ios_status is not ok" in source
    assert "refunds.ios_sales_report_vendor_number_present is not true" in source
    assert "refunds.ios_refund_count_metric_id missing expected token" in source
    assert "app_store_connect_sales_reports_daily_summary_negative_units_sum" in source


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


def test_actions_budget_throttles_high_frequency_schedules():
    wiki = WIKI_SYNC_WORKFLOW.read_text(encoding="utf-8")
    watcher = (ROOT / ".github/workflows/store-release-watcher.yml").read_text(encoding="utf-8")
    main_metrics = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    resolve = (ROOT / ".github/workflows/resolve-bot-comments.yml").read_text(encoding="utf-8")
    budget_doc = ACTIONS_BUDGET_DOC.read_text(encoding="utf-8")

    assert "cron: '5 */6 * * *'" in wiki
    assert "cron: '10 */6 * * *'" in watcher
    assert "cron: '20 */6 * * *'" in main_metrics
    assert "schedule:" not in resolve.split("workflow_dispatch:", 1)[0]
    assert ACTIONS_BUDGET_DOC.exists()
    assert "CI_IOS_DEVICE_TIER" in budget_doc
    assert "public" in budget_doc.lower()
