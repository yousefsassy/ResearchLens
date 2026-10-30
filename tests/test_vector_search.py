import numpy as np
import pytest
from src.retrieval.vector_search import VectorSearch


def test_cosine_ranking_ties_filters(chunks, encoder):
    search = VectorSearch(chunks, np.array([[1, 0], [0, 1], [1, 0], [-1, 0]]), encoder)
    rows = search.search("question", top_k=4)
    assert [r["chunk_id"] for r in rows] == [chunks[i]["chunk_id"] for i in (0, 2, 1, 3)]
    assert rows[0]["retrieval_score"] == pytest.approx(1)
    assert search.search("q", paper_ids=["P002"])[0]["pdf_page"] == 1
    assert search.search("q", paper_ids=["P002"], exclude_flagged=True) == []
    assert search.search("q", paper_ids=[]) == []
    assert search.search("q", paper_ids=["missing"]) == []


@pytest.mark.parametrize("question", ["", " ", None, 5])
def test_invalid_queries(chunks, encoder, question):
    with pytest.raises(ValueError):
        VectorSearch(chunks, np.ones((4, 2)), encoder).search(question)


def test_alignment_error(chunks, encoder):
    with pytest.raises(ValueError, match="row count"):
        VectorSearch(chunks, np.ones((3, 2)), encoder)


def test_query_embeddings_reused_across_scopes_and_bounded(chunks):
    class Encoder:
        def __init__(self):
            self.calls = []

        def encode_query(self, question):
            self.calls.append(question)
            return np.array([1, 0])

    encoder = Encoder()
    search = VectorSearch(chunks, np.ones((4, 2)), encoder)
    search.search("shared query", paper_ids=["P001"])
    search.search("shared query", paper_ids=["P002"])
    assert encoder.calls == ["shared query"]
    for index in range(33):
        search.search(f"query {index}")
    assert len(search._query_cache) == 32
    search.search("shared query")
    assert encoder.calls.count("shared query") == 2
    replacement = Encoder()
    search.encoder = replacement
    search.search("shared query")
    assert replacement.calls == ["shared query"]
