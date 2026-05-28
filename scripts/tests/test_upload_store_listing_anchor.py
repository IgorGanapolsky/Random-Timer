"""Tests for upload_store_listing_anchor.py."""

from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from scripts import upload_store_listing_anchor as usa


def test_load_env_sets_vars_from_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('ANCHOR_TEST=from_file\nANCHOR_TEST2="quoted"')
    monkeypatch.setattr(usa, "REPO", tmp_path)
    monkeypatch.delenv("ANCHOR_TEST", raising=False)
    monkeypatch.delenv("ANCHOR_TEST2", raising=False)
    usa.load_env()
    assert os.environ.get("ANCHOR_TEST") == "from_file"
    assert os.environ.get("ANCHOR_TEST2") == "quoted"


def test_load_env_skips_existing_var(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_VAR=overwrite")
    monkeypatch.setenv("EXISTING_VAR", "keep_me")
    monkeypatch.setattr(usa, "REPO", tmp_path)
    usa.load_env()
    assert os.environ.get("EXISTING_VAR") == "keep_me"


def test_load_env_no_file_no_error(tmp_path, monkeypatch):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    assert not (tmp_path / ".env").exists()
    usa.load_env()


def test_create_screenshots_zip_creates_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    screenshots_root = tmp_path / "native-ios" / "fastlane" / "screenshots" / "en-US"
    for device in ["iPhone-6.9-inch", "iPad-Pro-13-inch"]:
        dev_dir = screenshots_root / device
        dev_dir.mkdir(parents=True, exist_ok=True)
        (dev_dir / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(usa, "SCREENSHOTS", screenshots_root)
    zip_path = usa.create_screenshots_zip()
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"
    assert zip_path.stat().st_size > 0


def test_create_screenshots_zip_empty_when_no_screenshots(tmp_path, monkeypatch):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    screenshots_root = tmp_path / "native-ios" / "fastlane" / "screenshots" / "en-US"
    for device in ["iPhone-6.9-inch", "iPad-Pro-13-inch"]:
        (screenshots_root / device).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(usa, "SCREENSHOTS", screenshots_root)
    zip_path = usa.create_screenshots_zip()
    assert zip_path.exists()


def test_create_screenshots_zip_skips_missing_device_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    screenshots_root = tmp_path / "native-ios" / "fastlane" / "screenshots" / "en-US"
    (screenshots_root / "iPhone-6.9-inch").mkdir(parents=True, exist_ok=True)
    (screenshots_root / "iPhone-6.9-inch" / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(usa, "SCREENSHOTS", screenshots_root)
    zip_path = usa.create_screenshots_zip()
    assert zip_path.exists()
