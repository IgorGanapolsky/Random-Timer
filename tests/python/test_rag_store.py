import json

from tools.rag.store import add_memory, query_memories, rebuild_index


def test_store_roundtrip_with_fallback(tmp_path, monkeypatch):
    # Force jsonl fallback mode by making LanceDB import fail.
    from tools.rag import store as store_mod

    def boom():
        raise RuntimeError("no lancedb")

    monkeypatch.setattr(store_mod, "_import_lancedb", boom)

    events = tmp_path / "events.jsonl"
    db = tmp_path / "lancedb"

    add_memory(
        kind="question",
        text="Is my app published?",
        tags=["appstore"],
        db_dir=db,
        events_path=events,
        dim=64,
    )
    add_memory(
        kind="answer",
        text="No, it is waiting for review.",
        tags=["appstore", "status"],
        db_dir=db,
        events_path=events,
        dim=64,
    )

    hits = query_memories(
        "published",
        limit=5,
        db_dir=db,
        events_path=events,
        dim=64,
    )
    assert hits
    assert any("published" in h["text"].lower() for h in hits)


def test_rebuild_index_no_events_returns_zero(tmp_path):
    n = rebuild_index(db_dir=tmp_path / "db", events_path=tmp_path / "events.jsonl")
    assert n == 0

