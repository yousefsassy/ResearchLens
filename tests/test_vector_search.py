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
