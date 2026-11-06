import json
import pytest
from eval.retrieval_eval import load_questions, query_metrics, evaluate
from src.retrieval import ResearchRetriever


def test_recall_differs_from_any_hit(chunks):
    question = {"relevant_chunk_ids": [chunks[0]["chunk_id"], chunks[1]["chunk_id"]]}
    metrics = query_metrics(question, [chunks[2], chunks[0], chunks[0]])
    assert metrics["recall@1"] == 0
    assert metrics["recall@3"] == 0.5
    assert metrics["hit@3"] == 1
    assert metrics["reciprocal_rank"] == 0.5
    assert query_metrics(question, [])["reciprocal_rank"] == 0


def test_source_page_labels(chunks):
    question = {"relevant_sources": [{"paper_id": "P001", "pdf_page": 1}]}
    assert query_metrics(question, [chunks[0]])["recall@1"] == 1


@pytest.mark.parametrize("changes", [
    {"is_template": True}, {"relevant_chunk_ids": []},
    {"relevant_chunk_ids": ["unknown"]}, {"question": ""},
    {"relevant_chunk_ids": "not a list"}])
def test_reject_bad_labels(tmp_path, chunks, changes):
    row = {"question_id": "Q1", "question": "test", "relevant_chunk_ids": [chunks[0]["chunk_id"]]}
    row.update(changes)
    path = tmp_path / "labels.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError): load_questions(path, chunks)


def test_evaluation_pipeline_with_synthetic_labels(config, chunks, tmp_path):
    row = {"question_id": "synthetic", "question": "SelfCheckGPT", "relevant_chunk_ids": [chunks[0]["chunk_id"]]}
    path = tmp_path / "labels.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    questions = load_questions(path, chunks)
    report = evaluate(ResearchRetriever(config), questions, "bm25", False)
    assert report["metrics"]["recall@1"] == 1
    assert report["metrics"]["mrr"] == 1
    assert report["metrics"]["p95_latency_seconds"] >= 0
    assert len(report["per_question"]) == 1
    json.dumps(report, allow_nan=False)


def test_ablation_cli_synthetic_only(config, chunks, encoder, monkeypatch, tmp_path):
    import sys
    from src.retrieval.embeddings import build_index
    from eval import ablation
    build_index(chunks, config, encoder)
    retriever = ResearchRetriever(config)
    retriever.encoder = encoder
    class Model:
        def predict(self, pairs, **kwargs): return [1.0] * len(pairs)
    retriever.reranker._model = Model()
    labels = tmp_path / "synthetic.jsonl"
    labels.write_text(json.dumps({"question_id": "synthetic-only", "question": "SelfCheckGPT",
        "relevant_chunk_ids": [chunks[0]["chunk_id"]]}), encoding="utf-8")
    output = tmp_path / "ablation.json"
    monkeypatch.setattr(ablation, "ResearchRetriever", lambda config: retriever)
    monkeypatch.setattr(sys, "argv", ["ablation", "--dataset", str(labels), "--output", str(output)])
    ablation.main()
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(report["experiments"]) == 4
    assert output.with_suffix(".md").exists()
    assert report["dataset"]["sha256"]
