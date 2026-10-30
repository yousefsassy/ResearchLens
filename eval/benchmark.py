"""Opt-in benchmark execution, offline fixtures, incremental results and comparison."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from openai import OpenAIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.benchmark_data import DEFAULT_CORPUS, DEFAULT_DATASET, digest, load_benchmark
from eval.benchmark_scoring import compare, evaluate, summarize
from src.generation import GenerationConfig, ResearchGenerator
from src.generation.client import GenerationFailure, OpenAIClient
from src.generation.prompts import PROMPT_VERSION
from src.generation.schemas import ErrorInfo, GenerationResponse, Metrics
from src.profiling import collect


class BudgetClient:
    """Reuse one SDK transport, with a separately enforced whole-run request cap."""
    def __init__(self, config, limit, used=0, reserve=None):
        self.config = config.model_copy(update={"max_attempts": 1})
        self.owner = OpenAIClient(self.config)
        self.limit, self.used = limit, used
        self.reserve = reserve

    def complete(self, messages):
        if self.used >= self.limit:
            raise GenerationFailure("attempt_limit", "Benchmark request budget exhausted.")
        self.used += 1  # Reserve before the request, including failed requests.
        if self.reserve:
            self.reserve()
        client = OpenAIClient(self.config, client=self.owner.client)
        return client.complete(messages)

    complete_repair = complete

    def close(self):
        self.owner.close()


class FixtureRetriever:
    def __init__(self):
        self.rows = []

    def search(self, question, top_k=8, mode="hybrid", rerank=False, paper_ids=None, exclude_flagged=True):
        return [r for r in self.rows if paper_ids is None or r["paper_id"] in paper_ids][:top_k]


class FixtureClient:
    """Synthetic pipeline exercise, deliberately not a model-quality benchmark."""
    def complete(self, messages):
        payload = json.loads(messages[-1]["content"])
        passages = payload["evidence"]
        if not passages:
            output = dict(status="abstained", claims=[], limitations=["No fixture evidence."])
        else:
            claims = [dict(text="Offline fixture repeats a source excerpt: " + " ".join(p["text"].split()[:16]),
                           kind="reported", citations=[dict(source_id=p["source_id"], quote=" ".join(p["text"].split()[:10]))])
                      for p in passages[:2]]
            output = dict(status="partial", claims=claims, limitations=["Synthetic offline response; not an accuracy measurement."])
        return output, Metrics(attempts=1, model="offline-fixture", provider="mock", prompt_tokens=0, completion_tokens=0,
                               reasoning_tokens=0, cost_usd=0.0)

    def close(self):
        pass


def read_rows(directory, recover_tail=False):
    path = Path(directory) / "results.jsonl"
    if not path.exists():
        return []
    rows = []
    content = path.read_bytes()
    lines = content.split(b"\n")
    for index, line in enumerate(lines):
        if line.strip():
            try:
                row = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeError):
                if not recover_tail or any(tail.strip() for tail in lines[index + 1:]):
                    raise ValueError("Corrupt result record") from None
                backup = path.with_name(f"results.interrupted-{time.time_ns()}.jsonl")
                with backup.open("xb") as stream:
                    stream.write(content)
                temporary = path.with_suffix(".recovered.tmp")
                temporary.write_bytes(b"\n".join(lines[:index]) + (b"\n" if index else b""))
                temporary.replace(path)
                print(f"Recovered an interrupted final record; original preserved at {backup.name}")
                break
            if digest(row["response"]) != row["response_sha256"]:
                raise ValueError("Stored response hash mismatch")
            GenerationResponse.model_validate(row["response"])
            rows.append(row)
    if len({r["question_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate result IDs")
    return rows


def save_summary(directory, rows, manifest):
    summary = {**summarize(rows), "mode": manifest["mode"], "planned_questions": len(manifest["question_ids"]),
               "run_complete": len(rows) == len(manifest["question_ids"]),
               "dataset_sha256": manifest["dataset_sha256"], "rubrics_human_verified": False}
    ledger_path = directory / "request-budget.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"generation": 0, "judge": 0}
    summary["reserved_api_requests"] = ledger
    summary["request_accounting_complete"] = all(r["response"]["metrics"]["accounting_complete"] for r in rows)
    if manifest["mode"] == "live" and ledger["generation"] > sum(r["response"]["metrics"]["attempts"] for r in rows):
        summary["request_accounting_complete"] = False
        summary["estimated_cost_usd"] = None
    temporary = directory / "summary.json.tmp"
    temporary.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(directory / "summary.json")
    return summary


def estimate_cost(metrics, pricing, model):
    if not pricing or pricing["model"] != model or not metrics.accounting_complete:
        return None
    if metrics.prompt_tokens is None or metrics.completion_tokens is None:
        return None
    return (metrics.prompt_tokens * pricing["input_per_million_usd"]
            + metrics.completion_tokens * pricing["output_per_million_usd"]) / 1_000_000


def run(cases, directory, *, mode, config=None, resume=False, max_requests=20, judge=None,
        generator=None, pricing=None, dataset=DEFAULT_DATASET, corpus=DEFAULT_CORPUS):
    directory = Path(directory)
    if mode not in {"mock", "live"} or max_requests < 1 or not cases:
        raise ValueError("Invalid run mode, budget or empty subset")
    config = config or GenerationConfig.from_env()
    root = Path(__file__).resolve().parents[1]
    if mode == "live":
        from dotenv import load_dotenv
        load_dotenv(root / ".env", override=False)
    sources = sorted((root / "src").rglob("*.py")) + sorted((root / "eval").glob("benchmark*.py"))
    implementation = digest({str(p.relative_to(root)): p.read_text(encoding="utf-8") for p in sources})
    manifest = dict(schema_version="1.0", mode=mode, implementation_sha256=implementation,
                    dataset_sha256=digest(Path(dataset).read_text(encoding="utf-8")),
                    corpus_sha256=digest(Path(corpus).read_text(encoding="utf-8")), prompt_version=PROMPT_VERSION,
                    question_ids=[c.question_id for c in cases], case_hashes={c.question_id: digest(c.model_dump(mode="json")) for c in cases},
                    generation={key: getattr(config, key) for key in ("model", "max_tokens", "context_chars", "request_timeout")},
                    max_requests=max_requests, judge_model=getattr(judge, "model", None),
                    judge_budget=getattr(judge, "budget", None), pricing=pricing)
    if directory.exists() and not resume:
        raise ValueError("Run directory already exists; use --resume or a new directory")
    if resume:
        prior = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if prior != manifest:
            raise ValueError("Resume requires the same dataset, subset, settings and budgets")
        rows = read_rows(directory, recover_tail=True)
        if any(r["question_id"] not in manifest["case_hashes"] or r["case_sha256"] != manifest["case_hashes"][r["question_id"]] for r in rows):
            raise ValueError("Result cases differ from manifest")
    else:
        directory.mkdir(parents=True)
        with (directory / "manifest.json").open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
        rows = []
    done = {r["question_id"] for r in rows}
    used = sum(r["response"]["metrics"]["attempts"] for r in rows)
    ledger_path = directory / "request-budget.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"generation": 0, "judge": 0}
    used = max(used, ledger["generation"])

    def reserve(kind):
        ledger[kind] += 1
        temporary = directory / "request-budget.json.tmp"
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(ledger, stream)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(ledger_path)

    if judge:
        judge.attempts = max(ledger["judge"], sum(r.get("semantic", {}).get("usage", {}).get("attempts", 0) for r in rows))
        judge.reserve = lambda: reserve("judge")
    owned = generator is None
    fixture = FixtureRetriever() if mode == "mock" else None
    if owned:
        client = FixtureClient() if mode == "mock" else BudgetClient(config, max_requests, used, lambda: reserve("generation"))
        generator = ResearchGenerator(retriever=fixture, client=client, config=config)
    process_calls = 0
    try:
        for case in cases:
            if case.question_id in done:
                continue
            if mode == "live" and getattr(generator.client, "used", used) >= max_requests:
                break
            if fixture is not None:
                fixture.rows = [dict(chunk_id=r.chunk_id, paper_id=r.paper_id, pdf_page=r.pdf_page,
                                     pdf_filename=r.pdf_filename, text=r.quote, needs_review=False, review_flags=[])
                                for r in case.reference_sources]
            started = time.perf_counter()
            with collect() as profile:
                try:
                    response = generator.answer(case.question, case.paper_ids, case.answer_type)
                except Exception:
                    response = GenerationResponse(question=case.question, status="error",
                        error=ErrorInfo(code="pipeline_exception", message="Pipeline failed; no exception payload logged."))
                    response.metrics.total_seconds = time.perf_counter() - started
            selection = profile.get("evidence_selection_including_search", {}).get("seconds", 0)
            search = profile.get("aspect_search_including_initialization", {}).get("seconds", 0)
            profile["evidence_filtering_selection_exclusive"] = dict(seconds=max(0, selection - search), calls=int(selection > 0))
            embedding = profile.get("query_embedding_including_model_load", {}).get("seconds", 0)
            loading = profile.get("bge_model_loading", {}).get("seconds", 0)
            profile["query_embedding_exclusive"] = dict(seconds=max(0, embedding - loading), calls=profile.get("query_embedding_including_model_load", {}).get("calls", 0))
            serialized = response.model_dump(mode="json")
            semantic = judge.evaluate(case, response) if judge and mode == "live" and not response.error else {"status": "not_evaluated"}
            # Judges only receive independent serialized data and cannot replace the response.
            if serialized != response.model_dump(mode="json"):
                raise ValueError("Evaluator modified the answer")
            row = dict(question_id=case.question_id, question=case.question, category=case.category,
                       difficulty=case.difficulty, case_sha256=digest(case.model_dump(mode="json")),
                       response=serialized, response_sha256=digest(serialized), evaluation=evaluate(case, response),
                       semantic=semantic, profile=profile, process_phase="cold" if process_calls == 0 else "warm",
                       created_utc=datetime.now(timezone.utc).isoformat(),
                       estimated_cost_usd=estimate_cost(response.metrics, pricing, config.model))
            if semantic.get("status") == "evaluated":
                judgments = semantic["judgments"]
                for category, items, verdicts in (
                    ("judge_flagged_factual_issue", judgments["claims"], {"contradicted", "unsupported"}),
                    ("judge_flagged_missing_component", judgments["points"], {"missing"}),
                    ("judge_flagged_citation_support", judgments["citations"], {"contradicted", "unsupported"}),
                ):
                    if any(item["verdict"] in verdicts for item in items):
                        row["evaluation"]["failure_categories"].append(category)
            # Commit each row before starting the next question. Never overwrite old rows.
            with (directory / "results.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            rows.append(row)
            process_calls += 1
            used += response.metrics.attempts
            save_summary(directory, rows, manifest)
            print(f"{case.question_id}: {response.status} | {response.metrics.total_seconds:.2f}s | attempts {response.metrics.attempts}")
            if response.error and response.error.code in {"attempt_limit", "openai_api_error"}:
                break
    finally:
        if owned:
            generator.close()
    return save_summary(directory, rows, manifest)


def print_summary(summary):
    print(f"Questions: {summary['question_count']}/{summary['planned_questions']} ({summary['mode']})")
    print("Statuses:", ", ".join(f"{key}={value}" for key,value in summary["status_distribution"].items()))
    print(f"Citation validity: {summary['citation_validation_pass_rate']} | semantic method: {summary['semantic_method']}")
    print(f"Accuracy: {summary['accuracy']} | completeness: {summary['completeness']}")
    total = summary["latency"]["total_seconds"]
    print(f"Total latency (seconds): mean={total['mean']}, median={total['median']}, P90={total['p90']}, P95={total['p95']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    modes = execute.add_mutually_exclusive_group(required=True)
    modes.add_argument("--mock", action="store_true")
    modes.add_argument("--live", action="store_true")
    execute.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--limit", type=int)
    execute.add_argument("--ids", nargs="+")
    execute.add_argument("--resume", action="store_true")
    execute.add_argument("--max-requests", type=int, default=20)
    execute.add_argument("--judge-model")
    execute.add_argument("--judge-budget", type=int, default=10)
    execute.add_argument("--pricing", type=Path, help="Explicit USD per-million rates with model and as_of fields")
    show = commands.add_parser("summary")
    show.add_argument("directory", type=Path)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--baseline", type=Path, required=True)
    comparison.add_argument("--optimized", type=Path, required=True)
    args = parser.parse_args(argv)
    judge = None
    try:
        if args.command == "summary":
            print_summary(json.loads((args.directory / "summary.json").read_text(encoding="utf-8")))
        elif args.command == "compare":
            before = json.loads((args.baseline / "manifest.json").read_text(encoding="utf-8"))
            after = json.loads((args.optimized / "manifest.json").read_text(encoding="utf-8"))
            if any(before[key] != after[key] for key in ("mode", "corpus_sha256", "dataset_sha256", "judge_model")):
                raise ValueError("Comparison requires matching corpus, dataset, mode and judge")
            print(json.dumps(compare(read_rows(args.baseline), read_rows(args.optimized)), indent=2))
        else:
            if args.max_requests < 1 or args.judge_budget < 1 or (args.limit is not None and args.limit < 1):
                raise ValueError("Budgets and limits must be positive")
            if args.judge_model and not args.live:
                raise ValueError("A judge requires --live")
            cases = load_benchmark(args.dataset)
            if args.ids:
                if not set(args.ids) <= {c.question_id for c in cases}:
                    raise ValueError("Unknown question IDs")
                cases = [c for c in cases if c.question_id in args.ids]
            if args.limit:
                cases = cases[:args.limit]
            pricing = json.loads(args.pricing.read_text(encoding="utf-8")) if args.pricing else None
            if pricing:
                import math
                from datetime import date
                allowed = {"model", "as_of", "input_per_million_usd", "output_per_million_usd"}
                if set(pricing) != allowed or not pricing.get("model") or not pricing.get("as_of") or any(
                    not isinstance(pricing.get(key), (float, int)) or not math.isfinite(pricing[key]) or pricing[key] < 0
                    for key in ("input_per_million_usd", "output_per_million_usd")):
                    raise ValueError("Invalid explicit pricing")
                date.fromisoformat(pricing["as_of"])
            if args.judge_model:
                from dotenv import load_dotenv
                load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
                from eval.benchmark_judge import LLMJudge
                judge = LLMJudge(args.judge_model, args.judge_budget)
            summary = run(cases, args.output, mode="live" if args.live else "mock", resume=args.resume,
                          max_requests=args.max_requests, judge=judge, pricing=pricing, dataset=args.dataset)
            print_summary(summary)
    except (ValueError, OSError, KeyError, OpenAIError):
        parser.error("Invalid dataset, output, resume settings, budget or pricing. Existing runs are preserved.")
    finally:
        if judge:
            judge.close()


if __name__ == "__main__":
    main()
