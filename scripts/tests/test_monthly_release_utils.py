"""Tests for monthly storefront semver helper."""

from __future__ import annotations

import pytest


def test_bump_semver_patch() -> None:
    from scripts.monthly_release_utils import bump_semver_patch

    assert bump_semver_patch("1.3.19") == "1.3.20"
    assert bump_semver_patch("0.0.0") == "0.0.1"


def test_bump_semver_patch_rejects_invalid() -> None:
    from scripts.monthly_release_utils import bump_semver_patch

    with pytest.raises(ValueError):
        bump_semver_patch("1.2")
    with pytest.raises(ValueError):
        bump_semver_patch("1.2.a")
