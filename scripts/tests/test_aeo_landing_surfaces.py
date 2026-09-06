"""Guardrails for AEO landing surfaces (FAQPage + brand subject-first)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_INDEX = ROOT / "marketing" / "product-pages" / "index.html"
LLMS = ROOT / "marketing" / "product-pages" / "llms.txt"
BASELINE = ROOT / "marketing" / "data" / "aeo_visibility_baseline.json"


def test_product_page_has_faqpage_jsonld() -> None:
    html = PRODUCT_INDEX.read_text(encoding="utf-8")
    assert '"@type": "FAQPage"' in html or '"@type":"FAQPage"' in html
    assert "Random Tactical Timer" in html
    assert "SmartFight Timer" in html
    assert "PB Intervals" in html


def test_llms_txt_leads_with_entity_answer() -> None:
    text = LLMS.read_text(encoding="utf-8")
    assert text.startswith("Random Tactical Timer")
    assert "Direct answers" in text
    assert "com.iganapolsky.randomtimer" in text


def test_aeo_baseline_skips_paid_hubspot() -> None:
    import json

    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert payload["hubspot_spa_decision"] == "skip_paid_tool"
    assert payload["north_star_context"]["wqtu_7d"] == 5
    assert len(payload["commercial_prompts"]) >= 5
