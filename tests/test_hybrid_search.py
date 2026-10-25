import pytest
from src.retrieval.common import make_result
from src.retrieval.hybrid_search import reciprocal_rank_fusion, HybridSearch


def test_rrf_math_merge_and_debug(chunks):
    a, b = [make_result(c, 100, "bm25") for c in chunks[:2]]
    rows = reciprocal_rank_fusion({"bm25": [a, b, a], "vector": [b, a]}, top_k=5)
    assert len(rows) == 2
    assert rows[0]["chunk_id"] == a["chunk_id"]
    assert rows[0]["retrieval_score"] == pytest.approx(1/61 + 1/62)
    assert rows[0]["bm25_rank"] == 1
    assert rows[0]["vector_rank"] == 2
    assert rows[0]["bm25_score"] == 100
    assert reciprocal_rank_fusion({"vector": [], "bm25": []}) == []


def test_filters_and_counts_propagate(config):
    class Backend:
        calls = []
        def search(self, question, count, **filters):
            self.calls.append((count, filters))
            return []
    backend = Backend()
    assert HybridSearch(backend, backend, config).search("q", paper_ids=iter(["P001"]), exclude_flagged=True) == []
    assert backend.calls == [(config.bm25_candidates, {"paper_ids": ("P001",), "exclude_flagged": True}),
                             (config.vector_candidates, {"paper_ids": ("P001",), "exclude_flagged": True})]
