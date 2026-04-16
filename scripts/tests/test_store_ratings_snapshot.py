from __future__ import annotations

import math

from scripts import store_ratings_snapshot as srs


def test_histogram_and_mean():
    hist, mean, n = srs.histogram_and_mean([5, 4, 5, 1, 0, 99])
    assert n == 4
    assert math.isclose(mean, 3.75)
    assert hist["5"] == 2
    assert hist["4"] == 1
    assert hist["1"] == 1
    assert hist["2"] == hist["3"] == 0


def test_play_star_from_review_reads_user_comment():
    r = {
        "reviewId": "x",
        "comments": [{"userComment": {"starRating": 4, "text": "ok"}}],
    }
    assert srs.play_star_from_review(r) == 4


def test_play_star_from_review_none_without_user_star():
    r = {"reviewId": "x", "comments": [{"developerComment": {"text": "hi"}}]}
    assert srs.play_star_from_review(r) is None


def test_ios_rating_from_item():
    item = {"id": "1", "attributes": {"rating": 5, "title": "t"}}
    assert srs.ios_rating_from_item(item) == 5
    assert srs.ios_rating_from_item({"attributes": {}}) is None
