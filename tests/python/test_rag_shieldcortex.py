from tools.rag.shieldcortex import redact, scan


def test_redacts_github_token():
    txt = "token=ghp_1234567890ABCDEFGHIJKLmnopqrstuvwxyz"
    out = redact(txt)
    assert "ghp_" not in out
    assert "REDACTED" in out


def test_scan_detects_private_key_block():
    txt = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"
    issues = scan(txt)
    assert any(i.kind == "private_key_block" for i in issues)

