from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_verify_billing_catalog_script_targets_random_timer_package():
    source = _read("scripts/device-tests/adb/verify-billing-catalog.sh")

    assert "$PACKAGE" in source
    assert "$ACTIVITY" in source
    assert "PRO: 1H" in source
    assert "billing_product_catalog_status" in source
    assert "elite_tactical_monthly" in source


def test_verify_billing_catalog_script_sources_adb_common():
    source = _read("scripts/device-tests/adb/verify-billing-catalog.sh")

    assert 'source "$SCRIPT_DIR/lib/common.sh"' in source
