import json
import pytest
from src.retrieval import ResearchRetriever, RetrievalConfig
from src.retrieval.common import load_chunks
from src.retrieval.embeddings import build_index


def test_all_modes_json_metadata_and_lazy_loading(config, chunks, encoder):
    build_index(chunks, config, encoder)
    retriever = ResearchRetriever(config)
    assert retriever.status()["index"]["valid"]
    retriever.encoder = encoder
    retriever.search("SelfCheckGPT", mode="bm25", rerank=False)
    assert retriever._vector is None
    assert retriever.reranker._model is None
    class Model:
        def predict(self, pairs, **kwargs): return list(range(len(pairs)))
    retriever.reranker._model = Model()
    for mode in ("bm25", "vector", "hybrid"):
        for rerank in (False, True):
            rows = retriever.search("SelfCheckGPT", mode=mode, rerank=rerank)
            json.dumps(rows, allow_nan=False)
            for row in rows:
                source = next(c for c in chunks if c["chunk_id"] == row["chunk_id"])
                assert all(row[key] == value for key, value in source.items())
            assert retriever.last_timings["total_seconds"] >= 0
    rows[0]["extra"]["preserve"] = False
    assert chunks[0]["extra"]["preserve"]


def test_errors_and_empty_filters(config):
    retriever = ResearchRetriever(config)
    assert not retriever.status()["index"]["valid"]
    with pytest.raises(ValueError): retriever.search(" ")
    with pytest.raises(ValueError): retriever.search("q", mode="invalid")
    with pytest.raises(ValueError): retriever.search("q", top_k=0)
    with pytest.raises(ValueError): retriever.search("q", top_k=100)
    with pytest.raises(ValueError): retriever.search("q", mode="bm25", paper_ids="P001")
    assert retriever.search("q", mode="bm25", paper_ids=[]) == []


@pytest.mark.integration
def test_actual_corpus_bm25_and_citations():
    config = RetrievalConfig()
    if not config.chunks_path.exists():
        pytest.skip("Actual chunks.jsonl is missing; run Member 1 ingestion")
    retriever = ResearchRetriever(config)
    for query, paper in [("SelfCheckGPT", "P002"), ("FActScore", "P003")]:
        results = retriever.search(query, mode="bm25", rerank=False, paper_ids=[paper])
        assert results
        for row in results:
            assert row["paper_id"] == paper
            assert type(row["pdf_page"]) is int and row["pdf_page"] > 0
            assert row["pdf_filename"].startswith(paper)
            assert row["text"]
    assert not retriever.status()["embedding_model_loaded"]
