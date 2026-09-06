"""Tests for zero-cost AEO visibility scoring."""

from __future__ import annotations

from scripts.aeo_visibility_audit import brand_in_top_three, brand_mentioned, score_audit, score_engine_rows


def test_brand_mentioned_detects_aliases() -> None:
    assert brand_mentioned("Try Random Tactical Timer on iOS")
    assert brand_mentioned("open iganapolsky random timer")
    assert not brand_mentioned("PB Intervals and SmartFight Timer")


def test_top_three_recommendation() -> None:
    assert brand_in_top_three(["SmartFight Timer", "Random Tactical Timer", "PB Intervals"])
    assert not brand_in_top_three(["SmartFight Timer", "PB Intervals", "Tabata Timer"])


def test_score_engine_rows_computes_rates_and_gaps() -> None:
    rows = [
        {
            "prompt": "best random interval timer for MMA",
            "answer_text": "SmartFight Timer is popular.",
            "ordered_brands": ["SmartFight Timer", "PB Intervals"],
        },
        {
            "prompt": "best reaction timer app for BJJ",
            "answer_text": "Random Tactical Timer fires unpredictable cues.",
            "ordered_brands": ["Random Tactical Timer", "SmartFight Timer"],
        },
    ]
    scored = score_engine_rows(rows)
    assert scored["prompts_tested"] == 2
    assert scored["mentions"] == 1
    assert scored["top_three"] == 1
    assert scored["mention_rate"] == 0.5
    assert scored["recommendation_rate"] == 0.5
    assert scored["gap_prompts"] == ["best random interval timer for MMA"]


def test_score_audit_composites_engines() -> None:
    payload = {
        "brand": "Random Tactical Timer",
        "engines": {
            "chatgpt": [
                {
                    "prompt": "p1",
                    "answer_text": "Random Tactical Timer",
                    "ordered_brands": ["Random Tactical Timer"],
                }
            ],
            "perplexity": [
                {
                    "prompt": "p2",
                    "answer_text": "No match",
                    "ordered_brands": ["Other App"],
                }
            ],
        },
    }
    scored = score_audit(payload)
    assert scored["composite"]["engines_scored"] == 2
    assert scored["composite"]["mention_rate"] == 0.5
