import importlib.util
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "generate_pro_audio_content.py"
MANIFEST_PATH = ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_pro_audio_content", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_select_pack_uses_active_pack_by_default():
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)

    pack = module._select_pack(manifest, None)

    assert pack["id"] == manifest["activePackId"]


def test_select_pack_can_target_release_month() -> None:
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    expected = next(pack for pack in manifest["packs"] if pack["releaseMonth"] == "2026-04")

    pack = module._select_pack(manifest, None, "2026-04")

    assert pack["id"] == expected["id"]


def test_select_pack_fails_when_release_month_is_missing() -> None:
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)

    try:
        module._select_pack(manifest, None, "2099-12")
    except SystemExit as error:
        assert "releaseMonth '2099-12'" in str(error)
    else:
        raise AssertionError("Expected missing releaseMonth to fail fast")


def test_ensure_release_month_pack_is_noop_when_month_exists() -> None:
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    before_ids = {pack["id"] for pack in manifest["packs"]}

    updated, created = module.ensure_release_month_pack(manifest, "2026-05")

    assert created is False
    assert updated["activePackId"] == manifest["activePackId"]
    assert {pack["id"] for pack in updated["packs"]} == before_ids


def test_ensure_release_month_pack_clones_active_pack_for_missing_month() -> None:
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    active_pack_id = manifest["activePackId"]

    updated, created = module.ensure_release_month_pack(manifest, "2099-11")

    assert created is True
    assert updated["activePackId"] == "2099-11_m11_rotation"
    new_pack = next(pack for pack in updated["packs"] if pack["id"] == "2099-11_m11_rotation")
    assert new_pack["releaseMonth"] == "2099-11"
    assert "November 2099" in new_pack["theme"]
    source_pack = next(pack for pack in updated["packs"] if pack["id"] == active_pack_id)
    assert len(new_pack["commandCues"]) == len(source_pack["commandCues"])
    assert len(new_pack["soundArsenal"]) == len(source_pack["soundArsenal"])


def test_ensure_release_month_pack_uses_known_june_theme_slug() -> None:
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    prior_active = manifest["activePackId"]

    updated, created = module.ensure_release_month_pack(manifest, "2026-06")

    # Existing month packs are returned unchanged; activePackId only flips when a pack is created.
    assert created is False
    assert updated["activePackId"] == prior_active
    june_pack = next(pack for pack in updated["packs"] if pack["id"] == "2026-06_conditioning_lane")
    assert june_pack["releaseMonth"] == "2026-06"
    assert "Conditioning lane" in june_pack["theme"]


def test_voice_catalog_contains_preview_elapsed_elapsed_and_command_cues():
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    pack = module._select_pack(manifest, None)

    catalog = module._voice_catalog(pack)
    lines = module._voice_lines(catalog)

    expected_elapsed = [cue for cue in pack["elapsedCues"] if cue["second"] % 60 == 0]
    expected_count = 1 + len(expected_elapsed) + len(pack["commandCues"])
    assert len(lines) == expected_count
    assert lines[0] == (pack["previewElapsed"]["filename"], pack["previewElapsed"]["text"])
    assert [cue["second"] for cue in catalog["elapsedCues"]] == [cue["second"] for cue in expected_elapsed]


def test_sound_catalog_tracks_pack_metadata_and_all_sound_types():
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    pack = module._select_pack(manifest, None)

    catalog = module._sound_catalog(pack, manifest["defaults"]["entitlement"])

    assert catalog["packId"] == pack["id"]
    assert catalog["releaseMonth"] == pack["releaseMonth"]
    assert catalog["entitlement"] == "pro"
    assert len(catalog["sounds"]) == len(pack["soundArsenal"])


def test_estimate_credits_matches_manifest_shape():
    module = _load_module()
    manifest = module._load_manifest(MANIFEST_PATH)
    pack = module._select_pack(manifest, None)

    voice_estimate = module._estimate_voice_credits(module._voice_lines(module._voice_catalog(pack)), "eleven_multilingual_v2")
    sound_estimate = module._estimate_sound_credits(module._sound_entries(pack))

    assert voice_estimate > 0
    assert sound_estimate > 0


def test_resolve_voice_prefers_custom_voice_category():
    module = _load_module()
    voices = [
        {"name": "Marine Drill Voice", "voice_id": "premade-id", "category": "premade"},
        {"name": "Marine Drill Voice", "voice_id": "cloned-id", "category": "cloned"},
        {"name": "Something Else", "voice_id": "other-id", "category": "generated"},
    ]

    resolved = module._resolve_voice(voices, None, "marine")

    assert resolved["voice_id"] == "cloned-id"


def test_remove_stale_assets_keeps_expected_stems_only():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        (output_dir / "keep_me.mp3").write_bytes(b"keep")
        (output_dir / "delete_me.mp3").write_bytes(b"delete")

        module._remove_stale_assets({"keep_me"}, output_dir)

        assert (output_dir / "keep_me.mp3").exists()
        assert not (output_dir / "delete_me.mp3").exists()


def test_resolve_repo_path_rejects_external_paths():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            module._resolve_repo_path(Path(tmpdir))
        except SystemExit as error:
            assert "outside repository" in str(error)
        else:
            raise AssertionError("Expected external paths to be rejected")


def test_managed_output_paths_stay_inside_repository():
    module = _load_module()

    managed_paths = (
        module.CANONICAL_MANIFEST_PATH,
        module.IOS_VOICE_CATALOG_PATH,
        module.ANDROID_VOICE_CATALOG_PATH,
        module.IOS_SOUND_CATALOG_PATH,
        module.ANDROID_SOUND_CATALOG_PATH,
        module.RUNTIME_MANIFEST_PATH,
    )

    assert all(module.REPO_ROOT in path.parents for path in managed_paths)


def test_copy_assets_can_normalize_android_resource_names():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        destination_dir = Path(tmpdir) / "destination"
        source_dir.mkdir()
        (source_dir / "gentle-chime.mp3").write_bytes(b"audio")

        copied = module._copy_assets(
            source_dir,
            destination_dir,
            {"gentle-chime"},
            stem_transform=module._android_safe_stem,
        )

        assert copied == {"gentle_chime"}
        assert (destination_dir / "gentle_chime.mp3").exists()
        assert not (destination_dir / "gentle-chime.mp3").exists()


def test_runtime_manifest_contains_hashed_assets_and_catalogs():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runtime_dir = root / "runtime"
        manifest = module._load_manifest(MANIFEST_PATH)
        pack = module._select_pack(manifest, None)
        voice_dir = runtime_dir / "packs" / pack["id"] / "voice"
        sound_dir = runtime_dir / "packs" / pack["id"] / "sounds"
        voice_dir.mkdir(parents=True)
        sound_dir.mkdir(parents=True)
        (voice_dir / f"{pack['previewElapsed']['filename']}.mp3").write_bytes(b"voice-audio")
        (sound_dir / f"{pack['soundArsenal'][0]['filename']}.mp3").write_bytes(b"sound-audio")
        payload = module._runtime_manifest(
            pack,
            manifest["defaults"]["entitlement"],
            module._voice_catalog(pack),
            module._sound_catalog(pack, manifest["defaults"]["entitlement"]),
            runtime_base_url="https://example.com/runtime",
            runtime_assets_dir=runtime_dir,
        )

        assert payload["schemaVersion"] == 1
        assert payload["packId"] == pack["id"]
        assert payload["voiceCatalog"]["previewElapsed"]["filename"] == pack["previewElapsed"]["filename"]
        assert payload["soundCatalog"]["packId"] == pack["id"]
        assert len(payload["assets"]) == 1
        assert {asset["kind"] for asset in payload["assets"]} == {"voice"}
        assert all(asset["sha256"] for asset in payload["assets"])
        assert all(asset["url"].startswith("https://example.com/runtime/") for asset in payload["assets"])


def test_stage_runtime_assets_replaces_stale_pack_directories():
    module = _load_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ios_voice_dir = root / "ios-voice"
        ios_sound_dir = root / "ios-sound"
        runtime_dir = root / "runtime"
        ios_voice_dir.mkdir()
        ios_sound_dir.mkdir()
        (ios_voice_dir / "preview_elapsed.mp3").write_bytes(b"voice-audio")
        (ios_sound_dir / "alarm.mp3").write_bytes(b"sound-audio")
        stale_dir = runtime_dir / "packs" / "old-pack" / "voice"
        stale_dir.mkdir(parents=True)
        (stale_dir / "stale.mp3").write_bytes(b"stale")

        module._stage_runtime_assets(
            "new-pack",
            ios_audio_dir=ios_voice_dir,
            ios_sounds_dir=ios_sound_dir,
            runtime_assets_dir=runtime_dir,
            voice_stems={"preview_elapsed"},
            sound_stems={"alarm"},
        )

        assert (runtime_dir / "packs" / "new-pack" / "voice" / "preview_elapsed.mp3").exists()
        assert (runtime_dir / "packs" / "new-pack" / "sounds" / "alarm.mp3").exists()
        assert not (runtime_dir / "packs" / "old-pack").exists()
