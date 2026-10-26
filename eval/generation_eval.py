"""Opt-in generation capture plus offline human scoring; never infer truth from quotes."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import platform
import statistics
import sys
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import Field, model_validator

from src.generation import GenerationConfig, ResearchGenerator
from src.generation.prompts import PROMPT_VERSION
from src.generation.schemas import GenerationResponse, StrictModel
from src.generation.citations import validate_and_render
from src.generation.schemas import ModelAnswer


class EvalCase(StrictModel):
    question_id: str
    question: str
    category: str
    paper_ids: list[str] | None = None
    answer_type: str = "auto"
    expected_status: str
    required_components: dict[str, str]
    human_verified: bool = False
    reviewer: str | None = None
    reference_sources: list[dict] = Field(default_factory=list)
    fixed_evidence: list[dict] = Field(default_factory=list)
    notes: str = ""
    tracks: list[Literal["fixed", "end-to-end"]] = Field(default_factory=lambda: ["fixed", "end-to-end"], min_length=1)

    @model_validator(mode="after")
    def valid_case(self):
        if not self.question_id.strip() or not self.question.strip():
            raise ValueError("question ID and text are required")
        if self.answer_type not in {"auto", "qa", "comparison"}:
            raise ValueError("invalid answer type")
        if self.expected_status not in {"complete", "partial", "abstained", "needs_clarification"}:
            raise ValueError("invalid expected status")
        if self.human_verified and not (self.reviewer or "").strip():
            raise ValueError("verified cases require a reviewer")
        if self.expected_status in {"complete", "partial"} and not self.required_components:
            raise ValueError("answerable cases require component rubrics")
        return self


class HumanReview(StrictModel):
    human_verified: bool
    reviewer: str = Field(min_length=1)
    response_sha256: str
    supported_claim_indices: list[int]
    supported_citation_ids: list[str]
    adequately_cited_claim_indices: list[int]
    correct_component_ids: list[str]
    notes: str = ""


class FixedEvidenceRetriever:
    """Use supplied reviewed contexts, never a neural or keyword index."""
    def __init__(self, rows):
        self.rows = rows

    def search(self, question, top_k=8, mode="hybrid", rerank=False,
               paper_ids=None, exclude_flagged=True):
        return [r for r in self.rows if (paper_ids is None or r["paper_id"] in paper_ids)
                and not (exclude_flagged and (r["needs_review"] or r["review_flags"]))][:top_k]


def load_cases(path: Path, allow_draft=False) -> list[EvalCase]:
    cases = [EvalCase.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases or len({c.question_id for c in cases}) != len(cases):
        raise ValueError("dataset must contain unique question IDs")
    if not allow_draft and any(not c.human_verified for c in cases):
        raise ValueError("Human approval is required; --allow-draft permits debugging only, not benchmark claims.")
    return cases


def capture(cases: list[EvalCase], generator: ResearchGenerator, track: str,
            output: Path, dataset: Path):
    cases = [case for case in cases if track in case.tracks]
    if not cases:
        raise ValueError("dataset contains no cases for this track")
    if output.exists():
        raise ValueError("output exists; choose a new path to preserve prior runs")
    if track == "fixed" and any(not c.fixed_evidence and c.expected_status in {"complete", "partial"} for c in cases):
        raise ValueError("fixed track requires supporting contexts for every answerable case")
    report = {
        "schema_version": "1.0", "created_utc": datetime.now(timezone.utc).isoformat(),
        "track": track, "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "prompt_version": PROMPT_VERSION, "python": platform.python_version(),
        "config": generator.config.model_dump(mode="json"),
        "approved_dataset": all(c.human_verified for c in cases),
        "planned_case_count": len(cases), "run_complete": False, "rows": [],
    }
    original_retriever = generator.retriever
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for case in cases:
            if track == "fixed":
                generator.retriever = FixedEvidenceRetriever(case.fixed_evidence)
            response = generator.answer(case.question, case.paper_ids, case.answer_type)
            serialized = response.model_dump(mode="json")
            report["rows"].append({"case": case.model_dump(), "response": serialized,
                                   "response_sha256": response_hash(serialized)})
            report["run_complete"] = len(report["rows"]) == len(cases)
            if track == "end-to-end" and generator.retriever is not None and hasattr(generator.retriever, "status"):
                report["retrieval_status"] = generator.retriever.status()
            _save(output, report)
            if response.error and response.error.code in {"quota_exhausted", "attempt_limit", "missing_api_key", "authentication_failed"}:
                break
    finally:
        if track == "fixed":
            generator.retriever = original_retriever
    return report


def _save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def response_hash(response: dict) -> str:
    return hashlib.sha256(json.dumps(response, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def _percentile(values, percent):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent
    low, high = math.floor(index), math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def score_report(report: dict, reviews: dict) -> dict:
    totals = {name: 0 for name in ("claims", "citations", "supported_claims", "supported_citations",
              "adequately_cited_claims", "correct_components", "required_components",
              "comparison_correct", "comparison_required", "abstention_tp", "abstention_fp", "abstention_fn")}
    reviewed, successful, structural, unsupported_answers, expected_status_matches = 0, 0, 0, 0, 0
    token_totals = {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "cost_usd": 0.0}
    known_counts = {key: 0 for key in token_totals}
    latencies, generation_latencies = [], []
    for row in report["rows"]:
        case = EvalCase.model_validate(row["case"])
        response = GenerationResponse.model_validate(row["response"])
        expected_status_matches += response.status == case.expected_status
        ok = response.status in {"complete", "partial", "abstained", "needs_clarification"}
        successful += ok
        if response.status in {"complete", "partial", "abstained"}:
            try:
                rendered, citations = validate_and_render(ModelAnswer(
                    status=response.status, claims=response.claims, limitations=response.limitations),
                    response.evidence, response.answer_type, response.paper_ids)
                structural += rendered == response.answer and citations == response.citations
            except ValueError:
                pass
        elif response.status == "needs_clarification" and response.clarification is not None:
            structural += not response.claims and not response.citations
        latencies.append(response.metrics.total_seconds)
        generation_latencies.append(response.metrics.generation_seconds)
        for key in token_totals:
            value = getattr(response.metrics, key)
            if value is not None:
                token_totals[key] += value
                known_counts[key] += 1
        # Report failure of unsupported cases separately; never count API errors
        # as correct abstention or hide them by treating them as negative answers.
        if case.expected_status == "abstained" and response.claims:
            unsupported_answers += 1
        if case.expected_status in {"complete", "abstained"}:
            expected = case.expected_status == "abstained"
            actual = response.status == "abstained"
            totals["abstention_tp"] += expected and actual
            totals["abstention_fp"] += not expected and actual
            totals["abstention_fn"] += expected and not actual
        raw_review = reviews.get(case.question_id)
        if raw_review is None:
            continue
        review = HumanReview.model_validate(raw_review)
        if not review.human_verified:
            continue
        if review.response_sha256 != response_hash(row["response"]):
            raise ValueError("human review belongs to a different response")
        claims = set(range(1, len(response.claims) + 1))
        citation_ids = {c.citation_id for c in response.citations}
        for values, allowed in ((review.supported_claim_indices, claims),
                                (review.adequately_cited_claim_indices, claims),
                                (review.supported_citation_ids, citation_ids),
                                (review.correct_component_ids, set(case.required_components))):
            if len(values) != len(set(values)) or not set(values) <= allowed:
                raise ValueError(f"invalid human review references for {case.question_id}")
        reviewed += 1
        totals["claims"] += len(claims)
        totals["citations"] += len(citation_ids)
        totals["supported_claims"] += len(review.supported_claim_indices)
        totals["supported_citations"] += len(review.supported_citation_ids)
        totals["adequately_cited_claims"] += len(review.adequately_cited_claim_indices)
        totals["correct_components"] += len(review.correct_component_ids)
        totals["required_components"] += len(case.required_components)
        if response.answer_type == "comparison":
            totals["comparison_correct"] += len(review.correct_component_ids)
            totals["comparison_required"] += len(case.required_components)
    count = len(report["rows"])
    complete = (reviewed == count and count > 0 and report.get("approved_dataset", False)
                and report.get("run_complete", False)
                and count == report.get("planned_case_count")
                and all(r["case"]["human_verified"] for r in report["rows"]))
    faithfulness = _ratio(totals["supported_claims"], totals["claims"])
    citation_accuracy = _ratio(totals["supported_citations"], totals["citations"])
    correctness = _ratio(totals["correct_components"], totals["required_components"])
    return {
        "case_count": count, "human_reviewed_count": reviewed, "final_quality_claims_allowed": complete,
        "success_rate": _ratio(successful, count), "structurally_valid_answers": structural,
        "expected_status_accuracy": _ratio(expected_status_matches, count),
        "faithfulness": faithfulness, "citation_accuracy": citation_accuracy,
        "citation_coverage": _ratio(totals["adequately_cited_claims"], totals["claims"]),
        "correctness": correctness,
        "comparison_completeness": _ratio(totals["comparison_correct"], totals["comparison_required"]),
        "abstention_precision": _ratio(totals["abstention_tp"], totals["abstention_tp"] + totals["abstention_fp"]),
        "abstention_recall": _ratio(totals["abstention_tp"], totals["abstention_tp"] + totals["abstention_fn"]),
        "unsupported_case_answers": unsupported_answers,
        "total_latency_p50": statistics.median(latencies) if latencies else None,
        "total_latency_p95": _percentile(latencies, .95),
        "generation_latency_p50": statistics.median(generation_latencies) if generation_latencies else None,
        "generation_latency_p95": _percentile(generation_latencies, .95),
        "usage_known_subtotals": token_totals, "usage_known_response_counts": known_counts,
        "accounting_complete": all(r["response"]["metrics"]["accounting_complete"] for r in report["rows"]),
        "denominators_and_counts": totals,
        "pilot_quality_gates_passed": bool(complete and faithfulness is not None and faithfulness >= .9
            and citation_accuracy is not None and citation_accuracy >= .9 and correctness is not None
            and correctness >= .8 and unsupported_answers == 0 and structural == count
            and totals["abstention_fn"] == 0 and successful == count),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--dataset", type=Path, required=True)
    run.add_argument("--track", choices=["fixed", "end-to-end"], required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--live", action="store_true")
    run.add_argument("--allow-draft", action="store_true")
    score = commands.add_parser("score")
    score.add_argument("--report", type=Path, required=True)
    score.add_argument("--reviews", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            if not args.live:
                parser.error("--live is required; no inference request sent")
            cases = load_cases(args.dataset, args.allow_draft)
            generator = ResearchGenerator(config=GenerationConfig.from_env())
            try:
                report = capture(cases, generator, args.track, args.output, args.dataset)
            finally:
                generator.close()
            print(json.dumps({"completed_cases": len(report["rows"]), "output": str(args.output)}))
        else:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
            print(json.dumps(score_report(report, reviews), indent=2, allow_nan=False))
    except (ValueError, OSError, KeyError):
        parser.error("Invalid dataset, report, review, configuration, or output path. See docs/generation_design.md.")


if __name__ == "__main__":
    main()
