"""One-command ResearchLens benchmark: offline tests, live run, readable reports.

This is a reporting layer over eval/benchmark.py; it does not change RAG behavior.
Run from the repository root (Windows PowerShell example):
    python eval/full_benchmark.py run --live --max-requests 210
    python eval/full_benchmark.py report eval/results/<run-name>
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval.benchmark import read_rows
from eval.benchmark_data import DEFAULT_DATASET, load_benchmark


def pct(value):
    return "N/A" if value is None else f"{100 * value:.1f}%"


def num(value, decimals=1):
    return "N/A" if value is None else f"{value:,.{decimals}f}"


def value_count(mapping, key):
    return mapping.get(key, 0)


def fraction(count, total):
    return f"{count}/{total} ({100 * count / total:.1f}%)" if total else "N/A"


def safe_cell(value):
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def fmt_status_group(group):
    status = group.get("status_distribution", {})
    return [status.get("complete", 0), status.get("partial", 0), status.get("error", 0),
            status.get("abstained", 0), status.get("needs_clarification", 0)]


def case_info(row):
    response = row["response"]
    evaluation = row["evaluation"]
    semantic = row.get("semantic", {})
    metrics = response.get("metrics", {})
    result = {
        "question_id": row["question_id"],
        "category": row["category"],
        "difficulty": row["difficulty"],
        "question": row["question"],
        "status": response["status"],
        "expected_status_match": evaluation.get("status_correct"),
        "citation_valid": evaluation.get("citation_validation"),
        "citation_count": evaluation.get("citation_count"),
        "paper_scope_valid": evaluation.get("paper_scope_valid"),
        "reference_chunk_recall_diagnostic": evaluation.get("reference_chunk_recall"),
        "semantic_status": semantic.get("status", "not_evaluated"),
        "semantic_accuracy": semantic.get("accuracy"),
        "semantic_completeness": semantic.get("completeness"),
        "semantic_citation_support": semantic.get("semantic_citation_support"),
        "judge_error_stage": semantic.get("error_stage"),
        "judge_error_code": semantic.get("error_code"),
        "generation_api_attempts": metrics.get("attempts"),
        "latency_seconds": metrics.get("total_seconds"),
        "input_tokens": metrics.get("prompt_tokens"),
        "output_tokens": metrics.get("completion_tokens"),
        "failure_categories": "; ".join(evaluation.get("failure_categories", [])),
        "error_code": (response.get("error") or {}).get("code"),
        "limitations": "; ".join(response.get("limitations", [])),
        "answer": response.get("answer", ""),
    }
    return result


def build_sections(summary, rows, test_info=None):
    n = summary.get("question_count", len(rows))
    planned = summary.get("planned_questions", n)
    statuses = summary["status_distribution"]
    judged = summary.get("semantic_evaluated_questions", 0)
    judge_errors = summary.get("semantic_status_distribution", {}).get("judge_error", 0)
    valid_denom = summary.get("citation_validation_denominator", 0)
    usable = summary.get("semantic_status_distribution", {})
    req = summary.get("reserved_api_requests", {})
    usage = summary.get("usage", {})
    gen = summary.get("latency", {}).get("total_seconds", {})
    x = []
    x.append("# ResearchLens — Full Benchmark Report")
    x.append("")
    x.append(f"- **Run mode:** {summary.get('mode', 'unknown')}")
    x.append(f"- **Run complete:** {'YES' if summary.get('run_complete') else 'NO — INCOMPLETE'} ({n}/{planned} questions)")
    x.append(f"- **Dataset:** {summary.get('dataset_sha256', 'unknown')[:12]}… (SHA-256 fingerprint)")
    x.append(f"- **Ground truth human-verified:** {'Yes' if summary.get('ground_truth_verified') else 'No'}")
    if test_info is not None:
        x.append(f"- **Offline tests:** {test_info['status']} (see `tests.txt`)")
    x += ["", "## 1. Overall results", "",
          "| Metric | Result | Meaning |", "|---|---:|---|",
          f"| Questions processed | {n}/{planned} | Full set only when all planned questions finish |",
          f"| Complete | {fraction(value_count(statuses, 'complete'), n)} | Model-reported answer status |",
          f"| Partial | {fraction(value_count(statuses, 'partial'), n)} | Model-reported answer status |",
          f"| Errors | {fraction(value_count(statuses, 'error'), n)} | Pipeline or validation failed |",
          f"| Abstained | {fraction(value_count(statuses, 'abstained'), n)} | May be correct for unanswerable items |",
          f"| Needs clarification | {fraction(value_count(statuses, 'needs_clarification'), n)} | May be correct for ambiguous items |",
          f"| Expected-status agreement | {pct(summary.get('status_accuracy'))} | Agreement with draft acceptable statuses; **not factual accuracy** |",
          f"| Citation validation | {pct(summary.get('citation_validation_pass_rate'))} ({valid_denom} checked) | Valid source IDs/quotes/structure; **not semantic support** |",
          f"| Semantic factual accuracy | {pct(summary.get('accuracy'))} | LLM judge, only {judged}/{n} questions successfully judged |",
          f"| Semantic completeness | {pct(summary.get('completeness'))} | LLM judge, only {judged}/{n} questions successfully judged |",
          f"| Semantic citation support | {pct(summary.get('semantic_citation_support'))} | LLM judge, only {judged}/{n} questions successfully judged |",
          f"| Judge coverage | {fraction(judged, n)} | Unjudged responses are **not** assigned a perfect score |",
          f"| Judge errors | {judge_errors} | Invalid/incomplete judge outputs or API failures |",
          "", "**Interpretation:** semantic judgments and rubric labels are not human-verified; do not present these numbers as independent ground-truth accuracy."]
    x += ["", "## 2. Latency, calls, and cost", "",
          "| Metric | Value |", "|---|---:|",
          f"| Average total latency | {num(gen.get('mean'))} s |",
          f"| Median total latency | {num(gen.get('median'))} s |",
          f"| P90 / P95 total latency | {num(gen.get('p90'))} / {num(gen.get('p95'))} s |",
          f"| Warm-response average | {num(summary.get('warm_latency', {}).get('mean'))} s |",
          f"| Generation requests reserved | {req.get('generation', 'N/A')} |",
          f"| Judge requests reserved | {req.get('judge', 'N/A')} |",
          f"| Generation input / output tokens (known subtotals) | {usage.get('prompt_tokens', {}).get('known_subtotal', 'N/A'):,} / {usage.get('completion_tokens', {}).get('known_subtotal', 'N/A'):,} |",
          f"| Judge input / output tokens (known subtotals) | {summary.get('judge_usage', {}).get('input_tokens', 0):,} / {summary.get('judge_usage', {}).get('output_tokens', 0):,} |",
          f"| Repair frequency | {pct(summary.get('repair_frequency'))} |",
          f"| Estimated generation cost | {'$' + num(summary['estimated_cost_usd'], 4) if summary.get('estimated_cost_usd') is not None else 'Unknown (no verified pricing supplied)'} |",
          "", "Cost estimates exclude judge usage. Account billing/credits must be checked separately."]
    for key, title in (("by_category", "By question category"), ("by_difficulty", "By difficulty")):
        x += ["", "## " + ("3. " if key == "by_category" else "4. ") + title, "",
              "| Group | N | Complete | Partial | Error | Expected-status match | Valid citations | Judged |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for group, item in sorted(summary.get(key, {}).items()):
            counts = fmt_status_group(item)
            x.append(f"| {safe_cell(group)} | {item['count']} | {counts[0]} | {counts[1]} | {counts[2]} | {pct(item.get('status_accuracy'))} | {pct(item.get('citation_validation_pass_rate'))} | {item.get('semantic_evaluated_questions', 0)} |")
    x += ["", "## 5. Failure categories", "",
          "Counts can overlap because one answer may have multiple failure categories.", "",
          "| Failure category | Count |", "|---|---:|"]
    for fail, count in sorted(summary.get("failure_categories", {}).items(), key=lambda it: (-it[1], it[0])):
        x.append(f"| {safe_cell(fail)} | {count} |")
    if not summary.get("failure_categories"):
        x.append("| None recorded | 0 |")
    x += ["", "## 6. Judge failures (diagnostics)", "",
          "| Error stage | Count |", "|---|---:|"]
    for stage, count in sorted(summary.get("judge_error_stages", {}).items()):
        x.append(f"| {safe_cell(stage)} | {count} |")
    if not summary.get("judge_error_stages"):
        x.append("| None recorded | 0 |")
    needs_review = [case_info(r) for r in rows if r["response"]["status"] == "error" or
                    not r["evaluation"].get("status_correct", True) or
                    r["evaluation"].get("citation_validation") is False or
                    r.get("semantic", {}).get("status") == "judge_error" or
                    r["response"]["status"] == "partial"]
    x += ["", "## 7. Questions needing review", "",
          "These are **review candidates**, not automatically incorrect answers. Full details are in `per_question.csv`.", "",
          "| ID | Status | Why review? | Question |", "|---|---|---|---|"]
    for entry in needs_review:
        issues = []
        if entry["status"] in {"error", "partial"}:
            issues.append(entry["status"])
        if entry["expected_status_match"] is False:
            issues.append("status mismatch")
        if entry["citation_valid"] is False:
            issues.append("invalid citations")
        if entry["semantic_status"] == "judge_error":
            issues.append("judge error" + (f" ({entry['judge_error_code']})" if entry["judge_error_code"] else ""))
        x.append(f"| {entry['question_id']} | {entry['status']} | {safe_cell(', '.join(dict.fromkeys(issues)))} | {safe_cell(entry['question'][:110])} |")
    if not needs_review:
        x.append("| None automatically flagged | — | — | — |")
    x += ["", "## 8. Per-question results", "",
          "| ID | Category | Status | Status match | Citations valid | Judge status | Accuracy* | Completeness* | Time (s) |",
          "|---|---|---|---|---|---|---:|---:|---:|"]
    for row in rows:
        r = case_info(row)
        x.append(f"| {r['question_id']} | {safe_cell(r['category'])} | {r['status']} | {r['expected_status_match']} | {r['citation_valid']} | {r['semantic_status']} | {pct(r['semantic_accuracy'])} | {pct(r['semantic_completeness'])} | {num(r['latency_seconds'])} |")
    x += ["", "*Accuracy and completeness shown only for successfully judged questions. They are unverified automated judgments.*", "",
          "## Files", "", "- `report.md`: this report", "- `per_question.csv`: all question-level metrics and answers",
          "- `answers.md`: readable answers with source paper/pages and limitations",
          "- `results.jsonl`: complete evidence, citations, prompts' outputs and judge details per case",
          "- `summary.json`: machine-readable summary", "- `manifest.json`: settings and dataset fingerprint",
          "- `request-budget.json`: reserved API requests (if available)", "- `tests.txt`: offline test log (if tests were run)", ""]
    return "\n".join(x), needs_review


def render_answers(rows):
    """Human-readable answer archive with real source locations and limitations."""
    lines = ["# ResearchLens — Answers and Sources", "",
             "These are the original model responses, not rewritten by the reporter.", ""]
    for row in rows:
        response = row["response"]
        evaluation = row["evaluation"]
        semantic = row.get("semantic", {})
        lines += [f"## {row['question_id']} — {row['question']}", "",
                  f"**Status:** {response['status']}  ",
                  f"**Category:** {row['category']} · **Difficulty:** {row['difficulty']}  ",
                  f"**Expected-status match:** {evaluation.get('status_correct')} · **Citation validation:** {evaluation.get('citation_validation')}  ",
                  f"**Semantic judge:** {semantic.get('status', 'not_evaluated')}", ""]
        if response.get("answer"):
            lines.extend(["### Answer", "", response["answer"], ""])
        else:
            lines.extend(["### Answer", "", "*No answer returned.*", ""])
        citations = response.get("citations") or []
        if citations:
            lines += ["### Citations", ""]
            for citation in citations:
                label = citation.get("citation_id", "?")
                paper = citation.get("paper_id", "?")
                page = citation.get("pdf_page", "?")
                chunk = citation.get("chunk_id", "?")
                quote = citation.get("quote", "").replace("\n", " ")
                lines += [f"- **[{label}]** {paper}, PDF p. {page} (`{chunk}`) — {quote}"]
            lines.append("")
        if response.get("limitations"):
            lines += ["### Limitations", ""]
            lines += [f"- {item}" for item in response["limitations"]]
            lines.append("")
        if response.get("error"):
            error = response["error"]
            lines += [f"**Error:** `{error.get('code', 'unknown')}` — {error.get('message', '')}", ""]
        lines += ["---", ""]
    return "\n".join(lines)


def render_terminal(summary, rows, output, test_info):
    n = summary.get("question_count", len(rows))
    planned = summary.get("planned_questions", n)
    statuses = summary.get("status_distribution", {})
    semantic_n = summary.get("semantic_evaluated_questions", 0)
    width = 78
    print("\n" + "=" * width)
    print("  RESEARCHLENS — FINAL BENCHMARK SCORECARD")
    print("=" * width)
    print(f"  Run mode       : {summary.get('mode', 'unknown').upper()}")
    print(f"  Run status     : {'COMPLETE' if summary.get('run_complete') else 'INCOMPLETE'} ({n}/{planned})")
    if test_info:
        print(f"  Offline tests  : {test_info['status']}")
    print(f"  Complete       : {fraction(statuses.get('complete', 0), n)}")
    print(f"  Partial        : {fraction(statuses.get('partial', 0), n)}")
    print(f"  Error          : {fraction(statuses.get('error', 0), n)}")
    print(f"  Abstained      : {fraction(statuses.get('abstained', 0), n)}")
    print(f"  Clarification  : {fraction(statuses.get('needs_clarification', 0), n)}")
    print("-" * width)
    print(f"  Expected-status match : {pct(summary.get('status_accuracy'))} (draft labels, NOT factual accuracy)")
    print(f"  Valid citations       : {pct(summary.get('citation_validation_pass_rate'))} (structure/exact quotes)")
    print(f"  Semantic accuracy     : {pct(summary.get('accuracy'))} (judged {semantic_n}/{n}; automated, unverified)")
    print(f"  Semantic completeness : {pct(summary.get('completeness'))} (judged {semantic_n}/{n})")
    print(f"  Semantic citation     : {pct(summary.get('semantic_citation_support'))} (judged {semantic_n}/{n})")
    print(f"  Judge errors          : {summary.get('semantic_status_distribution', {}).get('judge_error', 0)}")
    print("-" * width)
    latency = summary.get("latency", {}).get("total_seconds", {})
    ledger = summary.get("reserved_api_requests", {})
    print(f"  Latency mean / P95    : {num(latency.get('mean'))}s / {num(latency.get('p95'))}s")
    print(f"  API requests (gen/judge): {ledger.get('generation', 'N/A')} / {ledger.get('judge', 'N/A')}")
    print(f"  Repair frequency      : {pct(summary.get('repair_frequency'))}")
    if summary.get("estimated_cost_usd") is not None:
        print(f"  Generation cost estimate: ${num(summary['estimated_cost_usd'], 4)} (judge excluded)")
    else:
        print("  Cost                  : Not calculated; API calls may be billed")
    print("\n  CATEGORY BREAKDOWN")
    print("  " + f"{'Category':<23} {'N':>4} {'OK':>5} {'Partial':>7} {'Errors':>7} {'Status%':>9}")
    for cat, info in sorted(summary.get("by_category", {}).items()):
        a = info["status_distribution"]
        print("  " + f"{cat[:23]:<23} {info['count']:>4} {a.get('complete',0):>5} {a.get('partial',0):>7} {a.get('error',0):>7} {pct(info.get('status_accuracy')):>9}")
    flagged = [case_info(row) for row in rows if row["response"]["status"] in {"partial", "error"} or not row["evaluation"]["status_correct"] or row["evaluation"].get("citation_validation") is False]
    print(f"\n  PRIORITY REVIEW: {len(flagged)} structurally flagged cases")
    for entry in flagged[:15]:
        reason = entry["error_code"] or entry["failure_categories"] or entry["status"]
        print(f"  {entry['question_id']:<9} {entry['status']:<19} {reason[:48]}")
    if len(flagged) > 15:
        print(f"  ... plus {len(flagged) - 15} more (see report.md and per_question.csv)")
    print("-" * width)
    print("  SAVED REPORTS")
    for filename in ("report.md", "answers.md", "per_question.csv", "summary.json", "results.jsonl", "tests.txt"):
        if (output / filename).exists():
            print(f"  {output / filename}")
    if not summary.get("run_complete"):
        print("\n  WARNING: The run did not process every question. Do not call this a final full result.")
    if semantic_n < n:
        print("  NOTE: Semantic accuracy does NOT cover all questions.")
    if summary.get("mode") == "mock":
        print("  WARNING: MOCK results are synthetic, not model-quality measurements.")
    print("=" * width)


def report(directory, test_info=None):
    directory = Path(directory)
    summary_file = directory / "summary.json"
    if not summary_file.exists():
        raise FileNotFoundError(f"No summary.json in {directory}")
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    rows = read_rows(directory)
    if summary.get("question_count") != len(rows):
        raise ValueError("Summary and question records differ; do not report stale results")
    if test_info is None and (directory / "tests.json").exists():
        test_info = json.loads((directory / "tests.json").read_text(encoding="utf-8"))
    md, _ = build_sections(summary, rows, test_info)
    (directory / "report.md").write_text(md + "\n", encoding="utf-8")
    (directory / "answers.md").write_text(render_answers(rows) + "\n", encoding="utf-8")
    records = [case_info(row) for row in rows]
    if records:
        with (directory / "per_question.csv").open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    render_terminal(summary, rows, directory, test_info)
    return summary


def full_run(args):
    from dotenv import load_dotenv
    from eval.benchmark_judge import LLMJudge
    from eval.benchmark import run as perform
    from src.generation.config import GenerationConfig

    if not args.live:
        raise ValueError("Explicit --live required: this runs real, potentially billable API calls")
    if args.max_requests < 1 or args.judge_budget < 1:
        raise ValueError("Request budgets must be positive")
    out = args.output or ROOT / "eval" / "results" / ("full-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    out = Path(out).resolve()
    cases = load_benchmark(args.dataset)
    print("\n" + "=" * 78)
    print("  RESEARCHLENS — FULL EVALUATION")
    print("=" * 78)
    print(f"  Dataset         : {len(cases)} questions (all; no --ids or --limit)")
    print(f"  Output          : {out}")
    print(f"  Generation cap  : {args.max_requests} API requests")
    print(f"  LLM judge       : {args.judge_model or 'OFF (semantic accuracy will be N/A)'}")
    if args.judge_model:
        print(f"  Judge cap       : {args.judge_budget} API requests")
    print("  Pricing         : Not presumed; check API usage dashboard for actual spend")
    print("=" * 78)

    test_info = None
    if not args.skip_tests and not args.resume:
        print("\n[1/3] Running all offline project tests before spending on API calls ...", flush=True)
        completed = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=ROOT,
                                   capture_output=True, text=True, errors="replace")
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        test_info = {"status": "PASS" if completed.returncode == 0 else "FAIL", "exit_code": completed.returncode}
        print("\n".join(output.strip().splitlines()[-12:]))
        print(f"  Tests: {test_info['status']}")
        if completed.returncode != 0:
            out.mkdir(parents=True, exist_ok=True)
            (out / "tests.txt").write_text(output, encoding="utf-8")
            (out / "tests.json").write_text(json.dumps(test_info, indent=2), encoding="utf-8")
            print("Aborted before paid calls. Fix test failures first or use --skip-tests explicitly.")
            return 2
    else:
        output = None
    if not (ROOT / "data/processed/chunks.jsonl").exists():
        print("Missing data/processed/chunks.jsonl; build the index/corpus first.")
        return 2
    if not (ROOT / "data/indexes").exists():
        print("Missing data/indexes/; build your existing retrieval index first.")
        return 2

    load_dotenv(ROOT / ".env", override=False)
    if not __import__("os").environ.get("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY in .env or environment. No paid requests were made.")
        return 2
    judge = LLMJudge(args.judge_model, args.judge_budget) if args.judge_model else None
    print(f"\n[2/3] Running {len(cases)} live RAG questions; each line is one saved result ...", flush=True)
    try:
        perform(cases, out, mode="live", config=GenerationConfig.from_env(), resume=args.resume,
                max_requests=args.max_requests, judge=judge, dataset=args.dataset)
    finally:
        if judge:
            judge.close()
        if output is not None and out.exists():
            (out / "tests.txt").write_text(output, encoding="utf-8")
            (out / "tests.json").write_text(json.dumps(test_info, indent=2), encoding="utf-8")
    print("\n[3/3] Generating detailed reports ...", flush=True)
    summary = report(out, test_info)
    return 0 if summary.get("run_complete") else 3


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run all ResearchLens cases and save readable benchmark reports")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("run", help="Run offline tests and ALL live benchmark questions")
    command.add_argument("--live", action="store_true", help="Required consent for potentially billable API calls")
    command.add_argument("--output", type=Path, help="New output directory; default eval/results/full-<UTC timestamp>")
    command.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    command.add_argument("--max-requests", type=int, default=210, help="Generation request cap; default 2x 105 cases")
    command.add_argument("--judge-model", help="Optional additional API-backed semantic judge")
    command.add_argument("--judge-budget", type=int, default=105, help="Judge request cap, only if model specified")
    command.add_argument("--skip-tests", action="store_true", help="Skip offline pytest before the live run")
    command.add_argument("--resume", action="store_true", help="Resume existing output with unchanged settings")
    view = sub.add_parser("report", help="Generate reports from saved JSONL; no API calls")
    view.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return full_run(args)
        report(args.directory)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
