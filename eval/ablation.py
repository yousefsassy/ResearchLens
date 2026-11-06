"""Compare four methods on the same manually labelled dataset."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.retrieval_eval import add_eval_arguments, evaluate, load_questions, save_report
from src.retrieval import ResearchRetriever
from src.retrieval.cli import config_from_args


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_eval_arguments(parser)
    parser.add_argument("--output", type=Path, default=Path("eval/results/ablation.json"))
    args = parser.parse_args()
    config = config_from_args(args)
    retriever = ResearchRetriever(config)
    questions = load_questions(args.dataset, retriever.chunks)
    experiments = {}
    table = ["| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Mean latency (s) | p95 latency (s) |",
             "|---|---|---|---|---|---|---|"]
    for label, mode, rerank in [("BM25", "bm25", False), ("Vector", "vector", False),
                                ("Hybrid RRF", "hybrid", False), ("Hybrid + rerank", "hybrid", True)]:
        report = evaluate(retriever, questions, mode, rerank, args.depth, not args.no_warmup)
        experiments[label] = report
        metrics = report["metrics"]
        values = [metrics[key] for key in ("recall@1", "recall@3", "recall@5", "mrr",
                                         "mean_latency_seconds", "p95_latency_seconds")]
        table.append("| " + label + " | " + " | ".join(f"{x:.4f}" for x in values) + " |")
    save_report({"experiments": experiments}, args.output, args.dataset)
    summary = "\n".join(table) + f"\n\nMRR truncated at depth {args.depth}. Warmup={not args.no_warmup}.\n"
    args.output.with_suffix(".md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
