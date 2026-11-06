"""Offline, repeated BM25 profiling; no model loading or API requests."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import statistics

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval.bm25_search import BM25Search
from src.retrieval.common import load_chunks


def profile(corpus, repeats=5):
    chunks = load_chunks(corpus)
    queries = ["hallucination causes", "stochastic sampling consistency", "atomic facts precision",
               "imitative falsehoods", "retrieval conversation"]
    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            index = BM25Search(chunks)
        initialization = time.perf_counter() - start
        start = time.perf_counter()
        answers = [[r["chunk_id"] for r in index.search(q, 8)] for q in queries]
        runs.append(dict(initialization_seconds=initialization,
                         warm_search_seconds=time.perf_counter() - start, ranked_chunk_ids=answers))
    return dict(method="offline_bm25_only", corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                queries=queries, runs=runs, semantic_quality="not_evaluated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=Path("data/processed/chunks.jsonl"))
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--compare-baseline", type=Path)
    args = parser.parse_args()
    if args.repeats < 2 or args.output.exists():
        parser.error("Use at least two repeats and a new output path.")
    result = profile(args.corpus, args.repeats)
    if args.compare_baseline:
        before = json.loads(args.compare_baseline.read_text(encoding="utf-8"))
        if before["corpus_sha256"] != result["corpus_sha256"] or before["queries"] != result["queries"]:
            parser.error("Baseline corpus or queries differ")
        rankings = before["runs"][0]["ranked_chunk_ids"]
        identical = all(r["ranked_chunk_ids"] == rankings for r in [*before["runs"], *result["runs"]])
        result["comparison"] = dict(ranked_results_identical=identical,
            baseline_mean_initialization_seconds=statistics.mean(r["initialization_seconds"] for r in before["runs"]),
            optimized_mean_initialization_seconds=statistics.mean(r["initialization_seconds"] for r in result["runs"]),
            semantic_quality="not_evaluated; offline component timings do not establish end-to-end improvement")
        if not identical:
            parser.error("Ranked results changed; reject this optimization pending review")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(f"Saved {args.repeats} offline repetitions to {args.output}")


if __name__ == "__main__":
    main()
