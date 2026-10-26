import json
from pathlib import Path

import pytest

from eval.generation_eval import (EvalCase, capture, load_cases, response_hash, score_report)
from src.generation import ResearchGenerator
from src.generation.schemas import Metrics, ModelAnswer


def case_data():
    return {"question_id": "G1", "question": "How does SelfCheckGPT work?", "category": "paper_specific",
            "paper_ids": ["P002"], "expected_status": "complete", "required_components": {"C1": "Explain consistency"},
            "human_verified": True, "reviewer": "human-reviewer", "fixed_evidence": [{
                "chunk_id": "P002-p001-c001", "paper_id": "P002", "pdf_filename": "P002_selfcheckgpt.pdf",
                "pdf_page": 1, "text": "SelfCheckGPT uses consistency.", "needs_review": False, "review_flags": []}]}


class Client:
    def complete(self, messages):
        return ModelAnswer(status="complete", claims=[{"text": "It uses consistency.", "kind": "reported",
            "citations": [{"source_id": "S1", "quote": "uses consistency"}]}], limitations=[]), Metrics(
                attempts=1, prompt_tokens=100, completion_tokens=20, cost_usd=0.0)


def test_draft_dataset_counts_and_approval_gate():
    path = Path("eval/generation_questions.draft.jsonl")
    cases = load_cases(path, allow_draft=True)
    assert len(cases) == 20 and not any(c.human_verified for c in cases)
    assert sum(c.category == "comparison" for c in cases) == 4
    with pytest.raises(ValueError, match="Human approval"):
        load_cases(path)


def captured(tmp_path):
    case = EvalCase.model_validate(case_data())
    dataset = tmp_path / "questions.jsonl"
    dataset.write_text(case.model_dump_json() + "\n")
    output = tmp_path / "report.json"
    generator = ResearchGenerator(client=Client())
    report = capture([case], generator, "fixed", output, dataset)
    review = {"human_verified": True, "reviewer": "reviewer", "response_sha256": report["rows"][0]["response_sha256"],
              "supported_claim_indices": [1], "supported_citation_ids": ["C1"],
              "adequately_cited_claim_indices": [1], "correct_component_ids": ["C1"]}
    return report, review, generator, dataset, output


def test_fixed_capture_and_human_scoring(tmp_path):
    report, review, generator, dataset, output = captured(tmp_path)
    assert generator.retriever is None and report["run_complete"]
    assert "api_key" not in report["config"]
    assert json.loads(output.read_text())["rows"][0]["response"]["citations"][0]["pdf_page"] == 1
    scores = score_report(report, {"G1": review})
    assert scores["faithfulness"] == 1 and scores["correctness"] == 1
    assert scores["citation_accuracy"] == 1 and scores["pilot_quality_gates_passed"]
    with pytest.raises(ValueError, match="output exists"):
        capture([EvalCase.model_validate(case_data())], generator, "fixed", output, dataset)


def test_no_semantic_score_without_human_review(tmp_path):
    report, _, _, _, _ = captured(tmp_path)
    scores = score_report(report, {})
    assert scores["faithfulness"] is None and scores["correctness"] is None
    assert not scores["final_quality_claims_allowed"] and not scores["pilot_quality_gates_passed"]


def test_incomplete_or_unapproved_runs_cannot_pass_gates(tmp_path):
    report, review, _, _, _ = captured(tmp_path)
    report["run_complete"] = False
    assert not score_report(report, {"G1": review})["pilot_quality_gates_passed"]
    report["run_complete"] = True
    report["approved_dataset"] = False
    assert not score_report(report, {"G1": review})["final_quality_claims_allowed"]


@pytest.mark.parametrize("change", ["quote", "review_claim", "review_component"])
def test_stale_or_invalid_reviews_rejected(tmp_path, change):
    report, review, _, _, _ = captured(tmp_path)
    if change == "quote":
        report["rows"][0]["response"]["citations"][0]["quote"] = "changed text"
    elif change == "review_claim":
        review["supported_claim_indices"] = [999]
    else:
        review["correct_component_ids"] = ["unknown"]
    with pytest.raises(ValueError):
        score_report(report, {"G1": review})


def test_errors_are_not_successful_abstention(tmp_path):
    report, review, _, _, _ = captured(tmp_path)
    row = report["rows"][0]
    row["case"]["expected_status"] = "abstained"
    row["case"]["required_components"] = {}
    row["response"].update(status="error", claims=[], citations=[], answer="", abstained=False,
                           error={"code": "request_failed", "message": "timeout", "retryable": True})
    row["response_sha256"] = response_hash(row["response"])
    scores = score_report(report, {})
    assert scores["abstention_recall"] == 0 and scores["success_rate"] == 0
