"""Real-model smoke checks and latency observations, NOT labelled evaluation."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval import ResearchRetriever
from src.retrieval.cli import add_config_arguments, config_from_args
from src.retrieval.common import corpus_fingerprint
from src.retrieval.embeddings import load_index
from eval.retrieval_eval import environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    parser.add_argument("--output", type=Path, default=Path("eval/results/smoke.json"))
    args = parser.parse_args()
    config = config_from_args(args)
    retriever = ResearchRetriever(config)
    matrix, metadata = load_index(retriever.chunks, config)
    sources = {c["chunk_id"]: c for c in retriever.chunks}
    report = {"kind": "unlabelled_smoke_test_not_accuracy_evaluation",
              "environment": environment(), "configuration": config.to_dict(),
              "corpus_fingerprint": corpus_fingerprint(retriever.chunks),
              "chunks": len(sources), "shape": list(matrix.shape), "index": metadata,
              "chunks_per_paper": dict(Counter(c["paper_id"] for c in retriever.chunks)),
              "flagged_chunks": sum(c["needs_review"] for c in retriever.chunks), "runs": []}
    questions = ["How does SelfCheckGPT detect hallucinations?",
                 "How does FActScore evaluate factual precision using atomic facts?"]
    for mode, rerank in [("bm25", False), ("vector", False), ("hybrid", False), ("hybrid", True)]:
        for question in questions:
            started = time.perf_counter()
            results = retriever.search(question, top_k=5, mode=mode, rerank=rerank)
            elapsed = time.perf_counter() - started
            if not results:
                raise AssertionError(f"No results: {mode}, {question}")
            for row in results:
                source = sources[row["chunk_id"]]
                assert all(row[key] == value for key, value in source.items()), "citation metadata changed"
            run = {"mode": mode, "rerank": rerank, "question": question,
                   "latency_seconds": elapsed, "timings": dict(retriever.last_timings), "results": results}
            report["runs"].append(run)
            # Persist each completed configuration if a later download fails.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
            print(json.dumps({"mode": mode, "rerank": rerank, "question": question,
                              "seconds": elapsed, "top_chunk": results[0]["chunk_id"],
                              "pdf_page": results[0]["pdf_page"]}), flush=True)
    for mode in ("bm25", "vector", "hybrid"):
        rows = retriever.search(questions[0], mode=mode, rerank=False,
                                paper_ids=["P002"], exclude_flagged=True)
        assert rows and all(r["paper_id"] == "P002" and not r["needs_review"] and not r["review_flags"] for r in rows)
    print(f"All smoke checks passed. Full results: {args.output}")


if __name__ == "__main__":
    main()
