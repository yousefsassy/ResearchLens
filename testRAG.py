"""Concise, opt-in live ResearchLens question runner."""
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAIError

from src.generation import GenerationConfig, ResearchGenerator
from src.profiling import collect


def display(result, verbose=False, debug=False, profile=None):
    print(f"Question: {result.question}")
    print(f"Status: {result.status}")
    print(f"\n{result.answer or '(No answer generated.)'}")
    if result.clarification:
        print(f"Clarification: {result.clarification.question}")
    if result.citations:
        print("\nCitations:")
        for citation in result.citations:
            print(f"  {citation.citation_id}: {citation.paper_id}, page {citation.pdf_page}, {citation.source_id}")
    if result.limitations:
        print("\nLimitations:")
        for limitation in result.limitations:
            print(f"  - {limitation}")
    if result.error:
        print(f"\nError: {result.error.code}: {result.error.message}")
    metrics = result.metrics
    print(f"\nTime: retrieval {metrics.retrieval_seconds:.2f}s | generation {metrics.generation_seconds:.2f}s"
          f" | validation {metrics.validation_seconds:.3f}s | total {metrics.total_seconds:.2f}s")
    print(f"LLM attempts: {metrics.attempts} | tokens: input {metrics.prompt_tokens}, "
          f"output {metrics.completion_tokens}, reasoning {metrics.reasoning_tokens}")
    if verbose or debug:
        print(f"Interpretation: {result.answer_type}; papers: {', '.join(result.paper_ids) or 'all'}")
        print(f"Selected evidence: {len(result.evidence)} passages")
        for item in result.evidence:
            print(f"  {item.source_id}: {item.chunk_id}, page {item.pdf_page}, "
                  f"{len(item.text)} characters, retrieval score {item.retrieval_score}")
    if debug and profile:
        print("Profile (nested timings overlap):")
        for name, item in sorted(profile.items()):
            print(f"  {name}: {item['seconds']:.4f}s ({item['calls']} calls)")


def main(argv=None, generator_factory=ResearchGenerator):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="*")
    parser.add_argument("--question", dest="question_option")
    parser.add_argument("--paper-ids", nargs="+")
    parser.add_argument("--answer-type", choices=["auto", "qa", "comparison"], default="auto")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("No API request sent. Add --live to enable generation.")
    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
    question = args.question_option or " ".join(args.question) or "What is SelfCheckGPT and how does it detect hallucinations?"
    config = GenerationConfig.from_env()
    if args.debug:
        config = config.model_copy(update={"debug_citations": True})
    generator = None
    try:
        generator = generator_factory(config=config)
        with collect() as profile:
            result = generator.answer(question, args.paper_ids, args.answer_type)
        display(result, args.verbose, args.debug, profile)
        return 1 if result.status == "error" else 0
    except (ValueError, OSError, RuntimeError, OpenAIError):
        print("Error: pipeline unavailable; check local configuration and dependencies.")
        return 1
    finally:
        if generator is not None:
            generator.close()


if __name__ == "__main__":
    raise SystemExit(main())
