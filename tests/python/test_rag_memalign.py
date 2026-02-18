from tools.rag.memalign import score_record


def test_memalign_prefers_higher_similarity():
    low = score_record(vector_sim=0.2, fts_rank=0.0, importance=0.5, recency_days=7)
    high = score_record(vector_sim=0.8, fts_rank=0.0, importance=0.5, recency_days=7)
    assert high.score > low.score


def test_memalign_recency_boost():
    old = score_record(vector_sim=0.5, fts_rank=0.0, importance=0.5, recency_days=30)
    new = score_record(vector_sim=0.5, fts_rank=0.0, importance=0.5, recency_days=1)
    assert new.score > old.score

