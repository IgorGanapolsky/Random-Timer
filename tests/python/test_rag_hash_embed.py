from tools.rag.hash_embed import hashed_embedding


def test_hashed_embedding_is_deterministic_and_normalized():
    a = hashed_embedding("App Store review")
    b = hashed_embedding("App Store review")
    assert a == b
    # L2 norm should be ~1 for non-empty strings.
    norm = sum(x * x for x in a) ** 0.5
    assert 0.99 <= norm <= 1.01


def test_hashed_embedding_empty_is_zero():
    v = hashed_embedding("")
    assert all(x == 0.0 for x in v)

