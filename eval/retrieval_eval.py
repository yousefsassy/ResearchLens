"""Evaluate manually labelled questions; never derive labels from retrieval."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
import platform
import os
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval import ResearchRetriever
from src.retrieval.cli import add_config_arguments, config_from_args
from src.retrieval.common import corpus_fingerprint


def load_questions(path: Path, chunks: list[dict]) -> list[dict]:
    """Labels are chunk IDs OR source pages (paper_id + one-based pdf_page)."""
    known_ids = {c["chunk_id"] for c in chunks}
    known_sources = {(c["paper_id"], c["pdf_page"]) for c in chunks}
    questions, seen = [], set()
    with Path(path).open(encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or row.get("is_template"):
                    raise ValueError("expected a manually verified question, not a template")
                for field in ("question_id", "question"):
                    if not isinstance(row.get(field), str) or not row[field].strip():
                        raise ValueError(f"{field} must be a nonempty string")
                if row["question_id"] in seen:
                    raise ValueError("duplicate question_id")
                ids, sources = row.get("relevant_chunk_ids"), row.get("relevant_sources")
                if bool(ids) == bool(sources):
                    raise ValueError("provide exactly one nonempty relevant_chunk_ids or relevant_sources list")
                if ids:
                    if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids):
                        raise ValueError("relevant_chunk_ids must be a list of strings")
                    if len(ids) != len(set(ids)) or not set(ids) <= known_ids:
                        raise ValueError("duplicate or unknown relevant chunk ID")
                else:
                    if not isinstance(sources, list) or any(not isinstance(x, dict) for x in sources):
                        raise ValueError("relevant_sources must be a list of source objects")
                    pairs = []
                    for item in sources:
                        if not isinstance(item.get("paper_id"), str) or type(item.get("pdf_page")) is not int:
                            raise ValueError("source requires paper_id and integer pdf_page")
                        pairs.append((item["paper_id"], item["pdf_page"]))
                    if len(pairs) != len(set(pairs)) or not set(pairs) <= known_sources:
                        raise ValueError("duplicate or unknown source page")
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f"{path}: line {line_number}: {error}") from error
            seen.add(row["question_id"])
            questions.append(row)
    if not questions:
        raise ValueError("evaluation dataset is empty")
    kinds = {"chunk" if q.get("relevant_chunk_ids") else "source_page" for q in questions}
    if len(kinds) != 1:
        raise ValueError("use one relevance unit per dataset: chunks or source pages")
    return questions


def query_metrics(question: dict, results: list[dict]) -> dict:
    if question.get("relevant_chunk_ids"):
        relevant = set(question["relevant_chunk_ids"])
        retrieved = [r["chunk_id"] for r in results]
    else:
        relevant = {(s["paper_id"], s["pdf_page"]) for s in question["relevant_sources"]}
        retrieved = [(r["paper_id"], r["pdf_page"]) for r in results]
    metrics = {f"recall@{k}": len(relevant.intersection(retrieved[:k])) / len(relevant)
               for k in (1, 3, 5, 10)}
    metrics.update({f"hit@{k}": float(bool(relevant.intersection(retrieved[:k])))
                    for k in (1, 3, 5, 10)})
    metrics["reciprocal_rank"] = next((1.0 / rank for rank, key in enumerate(retrieved, 1)
                                       if key in relevant), 0.0)
    return metrics


def environment() -> dict:
    packages = {}
    for name in ("numpy", "rank-bm25", "sentence-transformers", "torch", "transformers"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "not installed"
    torch_module = sys.modules.get("torch")
    hardware = {"logical_cpu_count": os.cpu_count()}
    if torch_module is not None:
        hardware.update(torch_threads=torch_module.get_num_threads(),
                        cuda_available=torch_module.cuda.is_available())
        if torch_module.cuda.is_available():
            hardware["gpu"] = torch_module.cuda.get_device_name(0)
    return {"hardware": hardware, "python": sys.version, "platform": platform.platform(),
            "processor": platform.processor(), "packages": packages}


def evaluate(retriever, questions: list[dict], mode: str, rerank: bool,
             depth: int = 10, warmup: bool = True) -> dict:
    """Macro-average passage recall; MRR is truncated at the retrieval depth."""
    if type(depth) is not int or depth < 10:
        raise ValueError("depth must be at least 10 to measure Recall@10")
    settings = dict(top_k=depth, mode=mode, rerank=rerank)
    cold_seconds = None
    if warmup:
        started = time.perf_counter()
        retriever.search(questions[0]["question"], **settings)
        cold_seconds = time.perf_counter() - started
    rows = []
    for question in questions:
        started = time.perf_counter()
        results = retriever.search(question["question"], **settings)
        latency = time.perf_counter() - started
        rows.append({"question_id": question["question_id"], "question": question["question"],
                     "metrics": query_metrics(question, results), "latency_seconds": latency,
                     "stage_timings": dict(retriever.last_timings), "results": results})
    metrics = {key: float(np.mean([r["metrics"][key] for r in rows])) for key in rows[0]["metrics"]}
    metrics["mrr"] = metrics.pop("reciprocal_rank")
    latencies = [r["latency_seconds"] for r in rows]
    metrics.update(mean_latency_seconds=float(np.mean(latencies)),
                   p50_latency_seconds=float(np.percentile(latencies, 50)),
                   p95_latency_seconds=float(np.percentile(latencies, 95)))
    return {"created_utc": datetime.now(timezone.utc).isoformat(), "metrics": metrics,
            "settings": {**settings, "warmup": warmup, "warmup_seconds": cold_seconds,
                         "mrr_depth": depth, "query_count": len(rows),
                         "relevance_unit": "chunk" if questions[0].get("relevant_chunk_ids") else "source_page"},
            "corpus_fingerprint": corpus_fingerprint(retriever.chunks),
            "system": retriever.status(), "environment": environment(), "per_question": rows}


def save_report(report: dict, output: Path, dataset: Path) -> None:
    report["dataset"] = {"path": str(dataset), "sha256": hashlib.sha256(dataset.read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def add_eval_arguments(parser) -> None:
    add_config_arguments(parser)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--no-warmup", action="store_true")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_eval_arguments(parser)
    parser.add_argument("--mode", choices=["bm25", "vector", "hybrid"], default="hybrid")
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("eval/results/retrieval.json"))
    args = parser.parse_args()
    retriever = ResearchRetriever(config_from_args(args))
    questions = load_questions(args.dataset, retriever.chunks)
    report = evaluate(retriever, questions, args.mode, args.rerank, args.depth, not args.no_warmup)
    save_report(report, args.output, args.dataset)
    print(f"Macro recall = fraction of ALL labelled relevant passages retrieved. MRR@{args.depth}.")
    print(json.dumps(report["metrics"], indent=2))
    print(f"Per-question results: {args.output}")


if __name__ == "__main__":
    main()
