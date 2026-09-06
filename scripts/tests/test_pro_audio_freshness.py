import importlib.util
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "pro_audio_freshness.py"
MANIFEST_PATH = ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("pro_audio_freshness", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_allowed_release_months_accept_previous_month_on_grace_day():
    module = _load_module()

    assert module.allowed_release_months(date(2026, 4, 1)) == ("2026-03", "2026-04")


def test_allowed_release_months_require_current_month_after_grace_day():
    module = _load_module()

    assert module.allowed_release_months(date(2026, 4, 2)) == ("2026-04",)


def test_current_manifest_is_fresh_for_today():
    module = _load_module()

    evidence = module.verify_manifest_freshness(MANIFEST_PATH, today=date(2026, 9, 6))

    assert evidence["release_month"] == "2026-09"
    assert str(evidence["active_pack_id"]).startswith("2026-09_")
