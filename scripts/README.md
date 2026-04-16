# `scripts/` layout

Automation grew as **one-off tools** were added for releases, growth, App Store Connect, and Play. Python modules stay at the top level so `from scripts.foo import …` and `pythonpath = ["."]` (see `pyproject.toml`) keep working without a large package move.

## `scripts/asc/`

App Store Connect automation (`asc_*.py`, `asc_client.py`). Import as `from scripts.asc.asc_submit_for_review import …`; CLI: `python scripts/asc/asc_submit_for_review.py`.

## `scripts/shell/`

Bash entry points (release, hygiene, iOS verify, MCP wrapper, maintenance). Prefer running these from the **repository root**; each script resolves `REPO_ROOT` / `PROJECT_ROOT` from its own path.

## `scripts/tests/`

Pytest suite for scripts and workflow contracts.

## `scripts/device-tests/`

ADB, Maestro, and PhoneClaw device automation.

## Top-level Python (by domain)

| Domain | Examples |
|--------|----------|
| **App Store Connect** | `asc_*.py`, `asc_client.py` |
| **Google Play** | `play_*.py`, `sync_android_metadata.py`, `verify_play_public_listing.py` |
| **Store creatives & ASO** | `generate_*_store_creatives.py`, `check_store_listing_parity.py`, `aso_keyword_rotation.py`, `listing_snapshot.py` |
| **Release & versioning** | `verify_release.py`, `release_ops.py`, `release_context.py`, `validate_release_branch.py`, `compute_android_release_version_code.py`, `source_versions.py` |
| **Growth & North Star** | `growth_*.py`, `north_star_*.py`, `executive_metrics_snapshot.py`, `wqtu_dashboard.py`, `cro_optimization.py`, `store_ratings_snapshot.py` |
| **Audio / Pro content** | `generate_pro_audio_content.py`, `pro_audio_freshness.py`, `add_ios_audio_assets.py` |
| **CI & guards** | `regression_guards.py`, `north_star_guardrail.py`, `review_contract_check.py`, `check_crashlytics.py` |
| **Integrations** | `verify_elevenlabs_voices.py`, `perplexity_*.py`, `posthog_dashboard.py`, `apple_ads_*.py` |

A deeper **subpackage** layout (e.g. `scripts/store/…`) would require updating every `from scripts.X` import and all workflows; track that as a follow-up if you want stricter physical grouping.
