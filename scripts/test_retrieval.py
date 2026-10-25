"""Run a real retrieval query and print citation-bearing JSON results."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval import ResearchRetriever
from src.retrieval.cli import add_config_arguments, config_from_args


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    parser.add_argument("--question", default="How does SelfCheckGPT detect hallucinations?")
    parser.add_argument("--mode", choices=["bm25", "vector", "hybrid"], default="hybrid")
    parser.add_argument("--no-rerank", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--paper-ids", nargs="*")
    parser.add_argument("--exclude-flagged", action="store_true")
    args = parser.parse_args()
    retriever = ResearchRetriever(config_from_args(args))
    rows = retriever.search(args.question, top_k=args.top_k, mode=args.mode,
        rerank=not args.no_rerank, paper_ids=args.paper_ids, exclude_flagged=args.exclude_flagged)
    print(json.dumps({"question": args.question, "results": rows,
                      "timings": retriever.last_timings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
