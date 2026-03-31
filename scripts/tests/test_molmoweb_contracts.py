from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "molmoweb_browser_verify.py"
SKILL_VERIFY = ROOT / ".claude" / "skills" / "molmoweb-browser-verify.md"
SKILL_SERVER = ROOT / ".claude" / "skills" / "molmoweb-server.md"
SKILL_PLAY = ROOT / ".claude" / "skills" / "molmoweb-play-console.md"
SKILL_ASC = ROOT / ".claude" / "skills" / "molmoweb-appstore-connect.md"
MAKEFILE = ROOT / "Makefile"


def test_molmoweb_wrapper_script_exists_and_uses_repo_local_evidence_output():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "def resolve_molmoweb_home" in source
    assert "def default_output_path" in source
    assert 'Path("evidence") / "molmoweb"' in source
    assert "MOLMOWEB_HOME" in source
    assert "from inference import MolmoWeb" in source


def test_molmoweb_skills_exist_and_reference_repo_wrapper():
    verify_source = SKILL_VERIFY.read_text(encoding="utf-8")
    server_source = SKILL_SERVER.read_text(encoding="utf-8")
    play_source = SKILL_PLAY.read_text(encoding="utf-8")
    asc_source = SKILL_ASC.read_text(encoding="utf-8")

    assert "name: molmoweb-browser-verify" in verify_source
    assert "scripts/molmoweb_browser_verify.py" in verify_source
    assert "MOLMOWEB_ENDPOINT" in verify_source

    assert "name: molmoweb-server" in server_source
    assert "CKPT=./checkpoints/MolmoWeb-4B-infer" in server_source
    assert "PREDICTOR_TYPE=hf" in server_source

    assert "name: molmoweb-play-console" in play_source
    assert "molmoweb-browser-verify" in play_source
    assert "play-console" in play_source

    assert "name: molmoweb-appstore-connect" in asc_source
    assert "molmoweb-browser-verify" in asc_source
    assert "appstore-connect" in asc_source


def test_makefile_exposes_repo_native_molmoweb_targets():
    source = MAKEFILE.read_text(encoding="utf-8")

    assert "molmoweb-proof-example:" in source
    assert "molmoweb-proof-homepage:" in source
    assert "scripts/molmoweb_browser_verify.py" in source
