"""Ask ResearchLens. Inference requires explicit --live; no paid fallback."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.generation import GenerationConfig, ResearchGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True)
    parser.add_argument("--paper-ids", nargs="*")
    parser.add_argument("--answer-type", choices=["auto", "qa", "comparison"], default="auto")
    parser.add_argument("--live", action="store_true", help="Enable free hosted inference")
    args = parser.parse_args()
    if not args.live:
        parser.error("No request sent. Add --live to enable free hosted inference.")
    try:
        generator = ResearchGenerator(config=GenerationConfig.from_env())
    except (ValueError, OSError):
        parser.error("Invalid generation configuration or missing paper catalog.")
    try:
        result = generator.answer(args.question, args.paper_ids, args.answer_type)
        print(result.model_dump_json(indent=2))
        return 1 if result.status == "error" else 0
    finally:
        generator.close()


if __name__ == "__main__":
    raise SystemExit(main())
