from __future__ import annotations

import json
from pathlib import Path

from scripts import store_growth_automation as sga


ROOT = Path(__file__).resolve().parents[2]
PERSONAS = ROOT / "marketing" / "store_growth" / "personas.json"


def test_personas_fit_store_limits() -> None:
    payload = json.loads(PERSONAS.read_text(encoding="utf-8"))

    assert sga.validate_personas(payload) == []
    assert len(payload["personas"]) == 4


def test_build_writes_persona_artifacts(tmp_path: Path) -> None:
    args = sga.build_parser().parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "--personas",
            str(PERSONAS),
            "build",
        ]
    )

    result = sga.build(args)

    assert result["personas"] == 4
    assert result["google_custom_store_listings"] == 4
    assert result["apple_custom_product_pages"] == 4
    assert (tmp_path / "marketing/store_growth/generated/store_growth_plan.json").is_file()
    assert (tmp_path / "marketing/site/audiences/combat-sports/index.html").is_file()
    attribution = json.loads((tmp_path / "marketing/data/store_growth_attribution.json").read_text(encoding="utf-8"))
    assert {row["campaign"] for row in attribution["personas"]} == {
        "persona_fitness_conditioning",
        "persona_combat_sports",
        "persona_tactical_public_safety",
        "persona_developer_open_source",
    }


def test_topic_selection_is_deterministic() -> None:
    args = sga.build_parser().parse_args(["--personas", str(PERSONAS), "topic", "--date", "2026-04-13"])

    first = sga.topic(args)
    second = sga.topic(args)

    assert first == second
    assert first["status"] == "ok"
    assert first["persona"]
    assert first["topic"]
