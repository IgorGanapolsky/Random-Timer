from tools.rag.shieldcortex import redact, scan


def test_redacts_github_token():
    # Build a token-like string at runtime to avoid triggering secret scanners on repo text,
    # while still exercising the redaction regex.
    txt = "token=" + "gh" + "p_" + "1234567890ABCDEFGHIJKLmnopqrstuvwxyz"
    out = redact(txt)
    assert "ghp_" not in out
    assert "REDACTED" in out


def test_scan_detects_private_key_block():
    txt = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"
    issues = scan(txt)
    assert any(i.kind == "private_key_block" for i in issues)
