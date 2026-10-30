"""Deterministic structural checks; lexical overlap is never factual verification."""
from collections import Counter
import statistics

from eval.generation_eval import _percentile
from src.generation.citations import validate_and_render
from src.generation.schemas import ModelAnswer


def evaluate(case, response):
    failures = []
    validity = None
    if response.claims or (response.error and response.error.code == "invalid_model_output"):
        validity = False
        try:
            model = ModelAnswer(status=response.status, claims=response.claims, limitations=response.limitations)
            rendered, citations = validate_and_render(model, response.evidence, response.answer_type, response.paper_ids)
            validity = rendered == response.answer and citations == response.citations
        except (ValueError, TypeError):
            pass
        if not validity:
            failures.append("citation_validation")
    status_correct = response.status in case.acceptable_statuses
    if not status_correct:
        failures.append("status_mismatch")
    cited = {c.paper_id for c in response.citations}
    scope_valid = not case.paper_ids or cited <= set(case.paper_ids)
    if not scope_valid:
        failures.append("paper_scope")
    if response.error:
        failures.append(response.error.code)
    if any("retrieval failed" in gap for gap in response.limitations):
        failures.append("retrieval_failure")
    requested = set(case.paper_ids or [])
    missing_papers = sorted(requested - cited) if response.answer_type == "comparison" else []
    if missing_papers and response.status == "complete":
        failures.append("comparison_paper_coverage")
    expected_chunks = {r.chunk_id for r in case.reference_sources}
    selected_chunks = {e.chunk_id for e in response.evidence}
    reference_recall = len(expected_chunks & selected_chunks) / len(expected_chunks) if expected_chunks else None
    return dict(method="deterministic_structure_only", status_correct=status_correct,
                citation_validation=validity, citation_count=len(response.citations),
                paper_scope_valid=scope_valid, missing_compared_papers=missing_papers,
                reference_chunk_recall=reference_recall,
                reference_recall_note="Diagnostic only: alternative chunks may contain valid support.",
                accuracy=None, completeness=None, semantic_citation_support=None,
                semantic_method="not_evaluated", failure_categories=list(dict.fromkeys(failures)))


def distribution(values):
    return {"count": len(values), "mean": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "p90": _percentile(values, .90), "p95": _percentile(values, .95)}


def summarize(rows):
    validations = [r["evaluation"]["citation_validation"] for r in rows if r["evaluation"]["citation_validation"] is not None]
    semantic = [r["semantic"] for r in rows if r.get("semantic", {}).get("status") == "evaluated"]
    def average(key):
        values = [s[key] for s in semantic if s.get(key) is not None]
        return statistics.mean(values) if values else None
    metrics = [r["response"]["metrics"] for r in rows]
    times = {name: distribution([m[name] for m in metrics]) for name in (
        "interpretation_seconds", "retrieval_seconds", "generation_seconds", "validation_seconds", "total_seconds")}
    usage = {}
    for name in ("attempts", "prompt_tokens", "completion_tokens", "reasoning_tokens"):
        known = [m[name] for m in metrics if m[name] is not None]
        usage[name] = {"known_subtotal": sum(known), "known_questions": len(known)}
    costs = [r["estimated_cost_usd"] for r in rows if r.get("estimated_cost_usd") is not None]
    initial = [r["profile"]["initial_generation_request"]["seconds"] for r in rows if "initial_generation_request" in r["profile"]]
    repair = [r["profile"]["citation_repair_request"]["seconds"] for r in rows if "citation_repair_request" in r["profile"]]
    result = dict(question_count=len(rows), status_distribution=dict(Counter(r["response"]["status"] for r in rows)),
        status_accuracy=sum(r["evaluation"]["status_correct"] for r in rows) / len(rows) if rows else None,
        citation_validation_pass_rate=sum(validations) / len(validations) if validations else None,
        citation_validation_denominator=len(validations), accuracy=average("accuracy"), completeness=average("completeness"),
        semantic_citation_support=average("semantic_citation_support"), semantic_evaluated_questions=len(semantic),
        semantic_coverage=len(semantic) / len(rows) if rows else None,
        semantic_status_distribution=dict(Counter(r.get("semantic", {}).get("status", "not_evaluated") for r in rows)),
        judge_error_stages=dict(Counter(r["semantic"].get("error_stage", "unknown") for r in rows
                                      if r.get("semantic", {}).get("status") == "judge_error")),
        semantic_score_scope="Successfully judged responses only; not overall run accuracy",
        semantic_method="optional_llm_judge_unverified" if semantic else "not_evaluated",
        ground_truth_verified=False, latency=times, usage=usage,
        estimated_cost_usd=sum(costs) if len(costs) == len(rows) and rows else None,
        cost_known_subtotal_usd=sum(costs) if costs else None, cost_known_questions=len(costs),
        cost_scope="generation only; judge usage reported separately; no default pricing assumed",
        judge_usage={key: sum(r.get("semantic", {}).get("usage", {}).get(key, 0) or 0 for r in rows)
                     for key in ("input_tokens", "output_tokens", "attempts")},
        repair_frequency=len(repair) / len(initial) if initial else None,
        initial_generation_latency=distribution(initial), additional_repair_latency=distribution(repair),
        failure_categories=dict(Counter(f for r in rows for f in r["evaluation"]["failure_categories"])),
        cold_start_latency=distribution([r["response"]["metrics"]["total_seconds"] for r in rows if r["process_phase"] == "cold"]),
        warm_latency=distribution([r["response"]["metrics"]["total_seconds"] for r in rows if r["process_phase"] == "warm"]),
        cold_start_note="Cold means first pipeline call in each process, not a cleared OS disk cache.")
    for group in ("category", "difficulty"):
        result[f"by_{group}"] = {}
        for value in sorted({r[group] for r in rows}):
            subset = [r for r in rows if r[group] == value]
            judged = [r["semantic"] for r in subset if r.get("semantic", {}).get("status") == "evaluated"]
            result[f"by_{group}"][value] = dict(count=len(subset),
                status_distribution=dict(Counter(r["response"]["status"] for r in subset)),
                status_accuracy=sum(r["evaluation"]["status_correct"] for r in subset) / len(subset),
                latency=distribution([r["response"]["metrics"]["total_seconds"] for r in subset]),
                semantic_evaluated_questions=len(judged))
            for field in ("accuracy", "completeness", "semantic_citation_support"):
                values = [r[field] for r in judged if r.get(field) is not None]
                result[f"by_{group}"][value][field] = statistics.mean(values) if values else None
            valid = [r["evaluation"]["citation_validation"] for r in subset if r["evaluation"]["citation_validation"] is not None]
            result[f"by_{group}"][value]["citation_validation_pass_rate"] = sum(valid) / len(valid) if valid else None
    return result


def compare(baseline, optimized):
    """Pair identical questions and references; never label unjudged quality as equal."""
    left = {r["question_id"]: r for r in baseline}
    right = {r["question_id"]: r for r in optimized}
    common = sorted(left.keys() & right.keys())
    if not common:
        raise ValueError("No common questions")
    for key in common:
        if left[key]["case_sha256"] != right[key]["case_sha256"]:
            raise ValueError("Question rubrics differ between runs")
    delta = [right[key]["response"]["metrics"]["total_seconds"] - left[key]["response"]["metrics"]["total_seconds"] for key in common]
    degraded = [key for key in common if
                (left[key]["evaluation"]["status_correct"] and not right[key]["evaluation"]["status_correct"])
                or (left[key]["evaluation"]["citation_validation"] is True and right[key]["evaluation"]["citation_validation"] is False)]
    semantic_pairs = [(left[k].get("semantic", {}), right[k].get("semantic", {})) for k in common]
    semantic_deltas = {}
    semantic_regressions = []
    for field in ("accuracy", "completeness", "semantic_citation_support"):
        values = [b[field] - a[field] for a,b in semantic_pairs if a.get(field) is not None and b.get(field) is not None]
        semantic_deltas[field] = distribution(values)
        for key in common:
            a, b = left[key].get("semantic", {}), right[key].get("semantic", {})
            if a.get(field) is not None and b.get(field) is not None and b[field] < a[field] - 0.05:
                semantic_regressions.append({"question_id": key, "metric": field, "delta": b[field] - a[field]})
    coverage_regressions = [key for key in common if
        left[key]["evaluation"].get("reference_chunk_recall") is not None and
        right[key]["evaluation"].get("reference_chunk_recall") is not None and
        right[key]["evaluation"]["reference_chunk_recall"] < left[key]["evaluation"]["reference_chunk_recall"]]
    return dict(paired_questions=len(common), unpaired_baseline=len(left) - len(common),
                unpaired_optimized=len(right) - len(common), latency_delta_seconds=distribution(delta),
                paired_cold_latency_delta=distribution([right[k]["response"]["metrics"]["total_seconds"] - left[k]["response"]["metrics"]["total_seconds"]
                    for k in common if left[k]["process_phase"] == right[k]["process_phase"] == "cold"]),
                paired_warm_latency_delta=distribution([right[k]["response"]["metrics"]["total_seconds"] - left[k]["response"]["metrics"]["total_seconds"]
                    for k in common if left[k]["process_phase"] == right[k]["process_phase"] == "warm"]),
                structural_regressions=degraded, semantic_score_deltas=semantic_deltas,
                judge_flagged_regressions=semantic_regressions, reference_coverage_regressions=coverage_regressions,
                quality_gate=("reject_structural_regression" if degraded else "hold_for_quality_review" if semantic_regressions or coverage_regressions
                              else "requires_semantic_and_repeated_run_review"),
                note="Separate latency from quality. Repeat cold and warm runs; model judgments are unverified.")
