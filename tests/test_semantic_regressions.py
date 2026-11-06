import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval.benchmark_data import load_benchmark
from eval.benchmark_judge import LLMJudge, validate_judgment
from eval.benchmark_scoring import summarize
from src.generation import ResearchGenerator, GenerationConfig
from src.generation.evidence import select_evidence
from src.generation.papers import interpret, load_catalog
from src.profiling import collect
from test_generation import Client, Retriever, passage
from test_generation_repair import SequenceClient, invalid


def fixture():
    result = ResearchGenerator(Retriever([passage()]), Client()).answer("SelfCheckGPT")
    # One claim with two separate citation objects, not two claims.
    result.citations.append(result.citations[0].model_copy(update={"citation_id": "C2"}))
    case = load_benchmark()[4]
    chunk = result.evidence[0].chunk_id
    verdict = dict(
        claims=[dict(item_id="1", verdict="supported", reason="Supported", evidence_chunk_ids=[chunk])],
        points=[dict(item_id=p.point_id, verdict="missing", reason="Absent", evidence_chunk_ids=[], answer_quotes=[])
                for p in case.important_points],
        citations=[dict(item_id=c.citation_id, verdict="supported", reason="Supported", evidence_chunk_ids=[chunk])
                   for c in result.citations])
    return case, result, verdict


def transport(verdict, status="completed"):
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(status=status, output_text=json.dumps(verdict),
        usage=SimpleNamespace(input_tokens=10, output_tokens=5))
    return client


def test_unequal_claim_and_citation_counts_have_explicit_mapping():
    case, result, verdict = fixture()
    client = transport(verdict)
    assert LLMJudge("mock", 1, client).evaluate(case, result)["status"] == "evaluated"
    items = json.loads(client.responses.create.call_args.kwargs["input"])["assessment_items"]
    assert [c["item_id"] for c in items["claims"]] == ["1"]
    assert [c["item_id"] for c in items["citations"]] == ["C1", "C2"]
    assert [c["claim_id"] for c in items["citations"]] == ["1", "1"]
    verdict["citations"].pop()
    scored = LLMJudge("mock", 1, transport(verdict)).evaluate(case, result)
    assert scored["error_code"] == "citations_item_ids"


@pytest.mark.parametrize("quotes,code", [([], "missing_answer_excerpt"),
    (["SelfCheckGPT compares stochastic samples for consistency."], "invalid_answer_excerpt")])
def test_evidence_only_text_cannot_receive_completeness_credit(quotes, code):
    case, result, verdict = fixture()
    verdict["points"][0].update(verdict="covered", answer_quotes=quotes)
    scored = LLMJudge("mock", 1, transport(verdict)).evaluate(case, result)
    assert scored["error_stage"] == "judgment_validation" and scored["error_code"] == code


def test_partial_coverage_accepts_real_answer_excerpt():
    case, result, verdict = fixture()
    verdict["points"][0].update(verdict="partial", answer_quotes=[result.claims[0].text])
    assert validate_judgment(verdict, case, result).points[0].verdict == "partial"


@pytest.mark.parametrize("status,verdict,stage", [("incomplete", {}, "incomplete_response"),
                                                 ("completed", {}, "output_schema")])
def test_judge_failures_have_safe_stage(status, verdict, stage):
    case, result, _ = fixture()
    scored = LLMJudge("mock", 1, transport(verdict, status)).evaluate(case, result)
    assert scored["error_stage"] == stage and scored["usage"]["output_tokens"] == 5


def test_repair_candidates_are_verbatim_and_failures_are_profiled():
    client = SequenceClient([invalid("quote"), Client().result])
    with collect() as profile:
        result = ResearchGenerator(Retriever([passage()]), client).answer("SelfCheckGPT")
    assert result.status == "complete"
    assert profile["initial_citation_validation"]["failure_category"] == "quote_mismatch"
    payload = json.loads(client.messages[1][1]["content"])
    for source, quotes in payload["verbatim_quote_candidates"].items():
        text = next(e.text for e in result.evidence if e.source_id == source)
        assert quotes and all(q in text for q in quotes)


@pytest.mark.parametrize("flagged,budget,expected", [(False, 12000, True), (True, 12000, False), (False, 1, False)])
def test_orphan_numeric_chunk_recovers_only_usable_neighbor(flagged, budget, expected):
    anchor = passage(index=4, text="**0.5** ): The sentence contains some inaccurate information. "
                     "Accurate sentences receive a value of zero.")
    previous = passage(index=3, text="The annotation labels are Major Inaccurate (1), Minor Inaccurate (0.5), "
                       "and Accurate (0). Each sentence receives one annotation label.", needs_review=flagged)
    backend = Retriever([anchor])
    backend.chunks = [previous, anchor]
    catalog = load_catalog(GenerationConfig().catalog_path)
    result = select_evidence(backend, "SelfCheckGPT annotation values", interpret("SelfCheckGPT annotation values", None, "auto", catalog), catalog, budget)
    assert (previous["chunk_id"] in {e.chunk_id for e in result.passages}) == expected
    assert sum(len(e.text) for e in result.passages) <= budget


def test_summary_discloses_missing_semantic_coverage():
    case, result, _ = fixture()
    from eval.benchmark_scoring import evaluate
    rows = [dict(response=result.model_dump(), evaluation=evaluate(case, result), semantic={"status": status},
                 profile={}, category="test", difficulty="easy", process_phase="warm") for status in ["judge_error", "not_evaluated"]]
    summary = summarize(rows)
    assert summary["accuracy"] is None and summary["semantic_coverage"] == 0
    assert summary["semantic_status_distribution"] == {"judge_error": 1, "not_evaluated": 1}
