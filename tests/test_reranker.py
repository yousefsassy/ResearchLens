import pytest
from src.retrieval.common import make_result
from src.retrieval.reranker import CrossEncoderReranker


def test_rerank_preserves_metadata(config, chunks):
    class Model:
        def predict(self, pairs, **kwargs):
            assert pairs[0] == ("q", chunks[0]["text"])
            assert kwargs["batch_size"] == config.rerank_batch_size
            return [-5.0, 3.0]
    ranker = CrossEncoderReranker(config, Model())
    original = [make_result(row, 0.5, "vector") for row in chunks[:2]]
    rows = ranker.rerank("q", original)
    assert rows[0]["paper_id"] == "P002"
    assert rows[0]["rerank_score"] == 3
    assert rows[0]["retrieval_score"] == 0.5
    assert rows[0]["review_flags"] == ["table"]
    assert original[0]["rerank_score"] is None
    assert ranker.last_latency_seconds >= 0


def test_empty_does_not_load_model(config):
    ranker = CrossEncoderReranker(config)
    assert ranker.rerank("q", []) == []
    assert ranker._model is None


def test_bad_scores(config, chunks):
    class Model:
        def predict(self, *args, **kwargs): return [float("nan")]
    with pytest.raises(ValueError, match="invalid scores"):
        CrossEncoderReranker(config, Model()).rerank("q", chunks[:1])
