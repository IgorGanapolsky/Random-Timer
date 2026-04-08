"""Stack Overflow feed parser (read-only, no network in tests)."""

from __future__ import annotations

from scripts import stackoverflow_feed_triage as sft


def test_feed_url_for_tags_joins_with_plus() -> None:
    url = sft.feed_url_for_tags(["swiftui", "storekit"])
    assert "tagnames=swiftui+storekit" in url
    assert url.startswith("https://stackoverflow.com/feeds/tag")


def test_write_subscribe_markdown_from_tag_groups(tmp_path) -> None:
    from scripts import stackoverflow_feed_triage as sft

    groups = tmp_path / "groups.txt"
    groups.write_text("swiftui\nstorekit\n", encoding="utf-8")
    out = tmp_path / "sub.md"
    sft.write_subscribe_markdown(groups, out)
    text = out.read_text(encoding="utf-8")
    assert "feeds/tag" in text
    assert "swiftui" in text
    assert "SUBSCRIBE" in text or "Feed URL" in text


def test_parse_atom_entries_extracts_title_and_link() -> None:
    xml = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title type="text">Example question?</title>
    <id>https://stackoverflow.com/q/123</id>
    <link rel="alternate" href="https://stackoverflow.com/questions/123/example" />
    <published>2026-01-01T12:00:00Z</published>
  </entry>
</feed>"""
    rows = sft.parse_atom_entries(xml, limit=5)
    assert len(rows) == 1
    assert rows[0]["title"] == "Example question?"
    assert rows[0]["url"] == "https://stackoverflow.com/questions/123/example"
    assert "2026-01-01" in rows[0]["published"]
