"""Offline evaluator regressions; no generation or judge API requests."""
import copy
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval.benchmark import main, read_rows, run
from eval.benchmark_data import BenchmarkCase, DEFAULT_CORPUS, DEFAULT_DATASET, load_benchmark
from eval.benchmark_judge import LLMJudge, evaluation_outcome, judgment_schema, validate_judgment
from eval.benchmark_scoring import evaluate, summarize
from eval.full_benchmark import build_sections, case_info
from src.generation import ResearchGenerator
from src.generation.schemas import GenerationResponse, ErrorInfo
from test_generation import Client, Retriever, passage
from test_semantic_regressions import fixture, transport


def judged(verdict=None, raw_text=None, status="completed", usage=True, output=None):
    case, response, default = fixture()
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        status=status, output_text=raw_text if raw_text is not None else json.dumps(default if verdict is None else verdict),
        usage=SimpleNamespace(input_tokens=10, output_tokens=5) if usage else None,
        output=output or [])
    return LLMJudge("mock-judge", 1, client).evaluate(case, response), client


def test_request_schema_uses_separate_inventory_ids_and_verdicts():
    case, response, verdict = fixture()
    schema = judgment_schema(case, response)
    defs = schema["$defs"]
    assert defs["claimsItem"]["properties"]["item_id"]["enum"] == ["1"]
    assert defs["citationsItem"]["properties"]["item_id"]["enum"] == ["C1", "C2"]
    point_branches = defs["pointsItem"]["anyOf"]
    assert all(branch["properties"]["item_id"]["enum"] == [p.point_id for p in case.important_points]
               for branch in point_branches)
    assert "covered" not in defs["claimsItem"]["properties"]["verdict"]["enum"]
    assert all("supported" not in branch["properties"]["verdict"]["enum"] for branch in point_branches)
    assert response.evidence[0].chunk_id in defs["claimsItem"]["properties"]["evidence_chunk_ids"]["items"]["enum"]
    scored, client = judged(verdict)
    assert scored["status"] == "evaluated"
    sent = client.responses.create.call_args.kwargs
    assert sent["text"]["format"]["schema"] == schema
    assert json.loads(sent["input"])["output_requirements"]["counts"]["citations"] == 2


@pytest.mark.parametrize("kind,stage,code", [
    ("merged_citations", "judgment_validation", "citations_item_ids"),
    ("duplicate_claim", "judgment_validation", "claims_item_ids"),
    ("unknown_claim_ref", "judgment_validation", "claims_verdict_or_reference"),
    ("wrong_citation_ref", "judgment_validation", "citation_source_mismatch"),
    ("unknown_citation_ref", "judgment_validation", "citations_verdict_or_reference"),
    ("unknown_point_ref", "judgment_validation", "points_verdict_or_reference"),
    ("evidence_excerpt", "judgment_validation", "invalid_answer_excerpt"),
    ("missing_excerpt", "judgment_validation", "missing_answer_excerpt"),
    ("blank_reason", "judgment_validation", "claims_empty_reason"),
    ("missing_evidence", "judgment_validation", "claims_missing_evidence"),
    ("wrong_enum", "output_schema", "invalid_schema"),
    ("missing_field", "output_schema", "invalid_schema"),
    ("wrong_type", "output_schema", "invalid_schema"),
    ("extra_field", "output_schema", "invalid_schema"),
])
def test_invalid_judgments_fail_closed_with_diagnostics(kind, stage, code):
    case, response, verdict = fixture()
    chunk = response.evidence[0].chunk_id
    if kind == "merged_citations": verdict["citations"].pop()
    elif kind == "duplicate_claim": verdict["claims"].append(copy.deepcopy(verdict["claims"][0]))
    elif kind == "unknown_claim_ref": verdict["claims"][0]["evidence_chunk_ids"] = ["S1"]
    elif kind == "wrong_citation_ref":
        other = next(r.chunk_id for r in case.reference_sources if r.chunk_id != chunk)
        verdict["citations"][0]["evidence_chunk_ids"] = [other]
    elif kind == "unknown_citation_ref": verdict["citations"][0]["evidence_chunk_ids"] = ["C1"]
    elif kind == "unknown_point_ref": verdict["points"][0]["evidence_chunk_ids"] = ["P002"]
    elif kind == "evidence_excerpt": verdict["points"][0].update(verdict="covered", answer_quotes=["Not in the answer"])
    elif kind == "missing_excerpt": verdict["points"][0].update(verdict="covered", answer_quotes=[])
    elif kind == "blank_reason": verdict["claims"][0]["reason"] = "   "
    elif kind == "missing_evidence": verdict["claims"][0]["evidence_chunk_ids"] = []
    elif kind == "wrong_enum": verdict["claims"][0]["verdict"] = "covered"
    elif kind == "missing_field": del verdict["points"][0]["answer_quotes"]
    elif kind == "wrong_type": verdict["claims"][0]["item_id"] = 1
    elif kind == "extra_field": verdict["private-unknown-key"] = "private-value"
    scored, client = judged(verdict)
    assert scored["status"] == "judge_error"
    assert scored["evaluation_outcome"] == "judge_output_validation_failure"
    assert (scored["error_stage"], scored["error_code"]) == (stage, code)
    assert "accuracy" not in scored
    assert client.responses.create.call_count == 1  # No repair or automatic retry.
    assert "private" not in json.dumps(scored)


@pytest.mark.parametrize("text", ["{broken", "```json\n{}\n```", "", "null"])
def test_malformed_or_unexpected_output_is_not_repaired(text):
    scored, _ = judged(raw_text=text)
    assert scored["evaluation_outcome"] == "judge_output_validation_failure"
    assert scored["error_code"] in {"malformed_json", "invalid_schema"}


def test_refusal_truncation_and_missing_usage_are_distinct():
    refused, _ = judged(output=[SimpleNamespace(content=[SimpleNamespace(type="refusal")])])
    assert refused["error_stage"] == "refusal"
    incomplete, _ = judged(status="incomplete")
    assert incomplete["error_stage"] == "incomplete_response"
    valid, _ = judged(usage=False)
    assert valid["status"] == "evaluated" and valid["usage"]["input_tokens"] is None


def test_api_failure_is_separate_from_invalid_judgment_and_budget():
    import httpx
    from openai import APIConnectionError
    case, response, _ = fixture()
    client = Mock()
    client.responses.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "https://example.test"), message="private details")
    judge = LLMJudge("mock", 1, client)
    scored = judge.evaluate(case, response)
    assert scored["evaluation_outcome"] == "judge_api_failure" and "private" not in str(scored)
    assert judge.evaluate(case, response)["evaluation_outcome"] == "judge_unavailable"
    assert client.responses.create.call_count == 1


def test_successful_judgment_preserves_scoring_definitions():
    case, response, verdict = fixture()
    verdict["points"][0].update(verdict="partial", answer_quotes=[response.claims[0].text])
    score, _ = judged(verdict)
    assert score["accuracy"] == score["semantic_citation_support"] == 1
    assert score["completeness"] == .5 / len(case.important_points)


def test_empty_answer_inventories_are_valid_and_scores_remain_null():
    case, response, _ = fixture()
    response = GenerationResponse(question=case.question, status="abstained", abstained=True,
                                  answer="I don't have sufficient evidence.")
    verdict = {"claims": [], "citations": [], "points": [
        dict(item_id=p.point_id, verdict="missing", reason="Absent", evidence_chunk_ids=[], answer_quotes=[])
        for p in case.important_points]}
    schema = judgment_schema(case, response)
    assert schema["properties"]["claims"]["maxItems"] == 0
    score = LLMJudge("mock", 1, transport(verdict)).evaluate(case, response)
    assert score["status"] == "evaluated"
    assert score["accuracy"] is None and score["semantic_citation_support"] is None
    assert score["completeness"] == 0


def test_summary_denominators_and_reports_keep_generation_independent():
    case, response, verdict = fixture()
    successful, _ = judged(verdict)
    rows = []
    semantics = [successful, {"status": "evaluated", "accuracy": None, "completeness": 0,
                             "semantic_citation_support": None},
                 {"status": "judge_error", "error_stage": "judgment_validation"},
                 {"status": "judge_error", "error_stage": "provider_request"},
                 {"status": "budget_exhausted"}, {"status": "not_evaluated"}]
    for semantic in semantics:
        rows.append(dict(question_id=case.question_id, question=case.question, response=response.model_dump(),
                         evaluation=evaluate(case, response), semantic=semantic, profile={},
                         category="test", difficulty="easy", process_phase="warm"))
    summary = summarize(rows)
    assert summary["status_distribution"] == {"complete": 6}
    assert summary["semantic_evaluated_questions"] == 2 and summary["semantic_coverage"] == 2/6
    assert summary["semantic_metric_denominators"] == {"accuracy": 1, "completeness": 2, "semantic_citation_support": 1}
    assert summary["accuracy"] == 1 and summary["completeness"] == 0
    assert summary["evaluation_outcome_distribution"] == {
        "successfully_judged": 2, "judge_output_validation_failure": 1, "judge_api_failure": 1,
        "judge_unavailable": 1, "not_evaluated": 1}
    report, _ = build_sections(summary, rows)
    assert "1/6 non-null question scores" in report and "2/6 non-null question scores" in report
    assert case_info(rows[2])["status"] == "complete"
    assert case_info(rows[2])["evaluation_outcome"] == "judge_output_validation_failure"


def test_evaluator_exception_saves_valid_generation_and_continues(tmp_path):
    cases = load_benchmark()[4:6]
    generator = Mock()
    generator.client.used = 0
    generator.answer.return_value = fixture()[1]
    judge = Mock(model="mock", budget=5, attempts=0)
    judge.evaluate.side_effect = RuntimeError("private evaluator failure")
    summary = run(cases, tmp_path / "run", mode="live", judge=judge, generator=generator)
    rows = read_rows(tmp_path / "run")
    assert len(rows) == 2 and all(r["response"]["status"] == "complete" for r in rows)
    assert summary["evaluation_outcome_distribution"] == {"judge_unavailable": 2}
    assert "private" not in json.dumps(rows)


def test_inventory_diagnostics_record_missing_and_duplicate_ids_without_unknown_values():
    _, _, verdict = fixture()
    verdict["citations"][1]["item_id"] = "C1"
    scored, _ = judged(verdict)
    assert scored["inventory_diagnostics"] == {
        "expected_count": 2, "returned_count": 2, "missing_ids": ["C2"],
        "duplicate_ids": ["C1"], "unknown_id_count": 0}
    verdict["citations"][1]["item_id"] = "private-unknown-id"
    scored, _ = judged(verdict)
    assert scored["inventory_diagnostics"]["unknown_id_count"] == 1
    assert "private" not in json.dumps(scored)


def test_judge_receives_independent_response_and_cannot_mutate_generation(tmp_path):
    case, original, _ = fixture()
    snapshot = original.model_dump()
    generator = Mock()
    generator.client.used = 0
    generator.answer.return_value = original
    judge = Mock(model="mock", budget=1, attempts=0)
    def mutate(case, response):
        response.answer = "replaced by evaluator"
        raise RuntimeError("Untrusted evaluator")
    judge.evaluate.side_effect = mutate
    run([case], tmp_path / "run", mode="live", judge=judge, generator=generator)
    assert original.model_dump() == snapshot
    assert read_rows(tmp_path / "run")[0]["response"] == snapshot


def test_generation_error_skips_judge(tmp_path):
    case = load_benchmark()[4]
    generator = Mock()
    generator.client.used = 0
    generator.answer.return_value = GenerationResponse(question=case.question, status="error",
        error=ErrorInfo(code="retrieval_unavailable", message="Unavailable"))
    judge = Mock(model="mock", budget=5, attempts=0)
    summary = run([case], tmp_path / "run", mode="live", judge=judge, generator=generator)
    assert summary["status_distribution"] == {"error": 1}
    judge.evaluate.assert_not_called()
    assert read_rows(tmp_path / "run")[0]["semantic"]["reason"] == "generation_error"


def test_historical_diagnostics_and_successful_judgments_replay_offline():
    cases = {c.question_id: c for c in (BenchmarkCase.model_validate_json(line)
             for line in Path("eval/benchmark.v1.jsonl").read_text().splitlines() if line.strip())}
    rows = [json.loads(line) for line in Path("eval/results/final/results.jsonl").read_text().splitlines()]
    failures = Counter(r["semantic"].get("error_code") for r in rows if r["semantic"]["status"] == "judge_error")
    assert sum(failures.values()) == 37 and len(failures) == 6
    assert failures["citations_item_ids"] == 21
    checked = 0
    for row in rows:
        if row["semantic"]["status"] == "evaluated":
            verdict = validate_judgment(row["semantic"]["judgments"], cases[row["question_id"]],
                                       GenerationResponse.model_validate(row["response"]))
            assert verdict
            checked += 1
    assert checked == 60


def test_expanded_dataset_matches_current_corpus_without_relabeling():
    cases = load_benchmark()
    assert len(cases) == 117 and not any(c.human_verified for c in cases)
    corpus = {r["chunk_id"]: r for r in map(json.loads, DEFAULT_CORPUS.read_text().splitlines())}
    assert len(corpus) == 1001 and len({r["paper_id"] for r in corpus.values()}) == 8
    flagged = {c.question_id for c in cases for r in c.reference_sources
               if corpus[r.chunk_id]["needs_review"] or corpus[r.chunk_id]["review_flags"]}
    assert flagged == {"GEN-009", "GEN-012", "GEN-013", "GEN-044", "GEN-088"}


@pytest.mark.parametrize("kind", ["duplicate_chunk", "unknown_paper", "outside_scope"])
def test_dataset_integrity_rejects_ambiguous_or_mismatched_inputs(tmp_path, kind):
    records = [json.loads(line) for line in DEFAULT_DATASET.read_text().splitlines()]
    corpus = [json.loads(line) for line in DEFAULT_CORPUS.read_text().splitlines()]
    if kind == "duplicate_chunk": corpus.append(corpus[0])
    elif kind == "unknown_paper": records[0]["paper_ids"] = ["P999"]
    else: records[0]["paper_ids"] = ["P003"]
    dataset, chunks = tmp_path / "cases.jsonl", tmp_path / "chunks.jsonl"
    dataset.write_text("\n".join(map(json.dumps, records)))
    chunks.write_text("\n".join(map(json.dumps, corpus)))
    with pytest.raises(ValueError):
        load_benchmark(dataset, chunks)


def test_comparison_refuses_different_judge_contract_versions(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "manifest.json").write_text(json.dumps({"judge_prompt_version": "1.0"}))
    (right / "manifest.json").write_text(json.dumps({"judge_prompt_version": "2.0"}))
    with pytest.raises(SystemExit) as error:
        main(["compare", "--baseline", str(left), "--optimized", str(right)])
    assert error.value.code == 2


@pytest.mark.parametrize("outcome,stop,expected", [
    ("judge_output_validation_failure", True, 1),
    ("judge_output_validation_failure", False, 2),
    ("judge_api_failure", False, 1),
])
def test_guarded_pilot_stops_after_persisting_failed_judgment(tmp_path, outcome, stop, expected):
    generator = Mock()
    generator.client.used = 0
    generator.answer.return_value = fixture()[1]
    judge = Mock(model="mock", budget=5, attempts=0)
    judge.evaluate.return_value = {"status": "judge_error", "evaluation_outcome": outcome}
    summary = run(load_benchmark()[4:6], tmp_path / "run", mode="live", judge=judge,
                  generator=generator, stop_on_judge_error=stop)
    assert summary["question_count"] == expected
    assert judge.evaluate.call_count == expected
    assert len(read_rows(tmp_path / "run")) == expected


def test_live_pilot_excerpt_failure_is_blocked_by_provider_schema_contract():
    case, response, verdict = fixture()
    branches = judgment_schema(case, response)["$defs"]["pointsItem"]["anyOf"]
    coverage = next(branch for branch in branches if "covered" in branch["properties"]["verdict"]["enum"])
    other = next(branch for branch in branches if "missing" in branch["properties"]["verdict"]["enum"])
    assert coverage["properties"]["verdict"]["enum"] == ["covered", "partial"]
    assert coverage["properties"]["answer_quotes"]["minItems"] == 1
    assert other["properties"]["verdict"]["enum"] == ["missing", "uncertain"]
    assert "minItems" not in other["properties"]["answer_quotes"]
    for branch in branches:
        assert branch["additionalProperties"] is False
        assert set(branch["required"]) == set(branch["properties"])
    # The native schema restriction complements, rather than replaces, local
    # validation. Simulate the exact failure category from live GEN-011.
    verdict["points"][0].update(verdict="partial", answer_quotes=[])
    scored, _ = judged(verdict)
    assert scored["error_code"] == "missing_answer_excerpt"
    assert scored["judgment_diagnostics"] == {
        "item_id": case.important_points[0].point_id, "verdict": "partial", "answer_quote_count": 0}
    assert "accuracy" not in scored


@pytest.mark.parametrize("verdict", ["missing", "uncertain"])
def test_uncovered_points_still_allow_empty_excerpts(verdict):
    _, _, output = fixture()
    output["points"][0].update(verdict=verdict, answer_quotes=[])
    scored, _ = judged(output)
    assert scored["status"] == "evaluated"
