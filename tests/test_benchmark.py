import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval.benchmark import main, read_rows, run, estimate_cost, BudgetClient
from eval.benchmark_data import DEFAULT_DATASET, digest, load_benchmark
from eval.benchmark_scoring import compare, evaluate, summarize
from eval.benchmark_judge import LLMJudge, validate_judgment
from src.generation import GenerationConfig, ResearchGenerator
from src.generation.schemas import Metrics, GenerationResponse
from src.profiling import collect, measure
from test_generation import Client, Retriever, passage
from testRAG import display, main as question_main


@pytest.fixture
def cases():
    return load_benchmark()


def response():
    return ResearchGenerator(Retriever([passage()]), Client()).answer("SelfCheckGPT")


def test_clean_default_output_and_optional_modes(capsys):
    result = response()
    display(result)
    output = capsys.readouterr().out
    assert output.count("Status:") == 1 and output.count("Question:") == 1
    assert "C1: P002, page 1, S1" in output
    assert "LLM attempts: 1" in output and "validation" in output
    assert "Interpretation" not in output and "Limitations:" not in output
    assert result.evidence[0].text not in output and '"source_id"' not in output
    display(result, verbose=True)
    output = capsys.readouterr().out
    assert output.count("Interpretation:") == 1 and result.evidence[0].chunk_id in output
    assert result.evidence[0].text not in output
    display(result, debug=True, profile={"initial_generation_request": {"seconds": .2, "calls": 1}})
    assert "initial_generation_request: 0.2000s" in capsys.readouterr().out


def test_cli_debug_enables_diagnostics_and_requires_live(capsys, monkeypatch):
    loader = Mock()
    monkeypatch.setattr("testRAG.load_dotenv", loader)
    factory = Mock()
    with pytest.raises(SystemExit):
        question_main(["a question"], factory)
    factory.assert_not_called()
    loader.assert_not_called()
    factory.return_value.answer.return_value = response()
    assert question_main(["--live", "--debug", "SelfCheckGPT"], factory) == 0
    assert factory.call_args.kwargs["config"].debug_citations
    factory.return_value.close.assert_called_once()
    loader.assert_called_once()


def test_benchmark_schema_references_diversity_and_preserved_questions(cases):
    assert len(cases) >= 100
    assert len({c.question_id for c in cases}) == len(cases)
    assert len({c.question.casefold() for c in cases}) == len(cases)
    assert {"definitions", "methodology", "experimental_setup", "findings", "limitations", "single_paper_factual",
            "comparison", "multi_hop", "quantitative", "clarification", "unanswerable", "partial", "false_premise", "scope_restriction"} <= {c.category for c in cases}
    assert {c.difficulty for c in cases} == {"easy", "intermediate", "difficult"}
    assert sum(len(c.reference_sources) > 1 for c in cases) >= 10
    for paper in ("P001", "P002", "P003", "P004", "P005"):
        assert sum(paper in (c.paper_ids or []) for c in cases) >= 12
    original = [json.loads(line) for line in Path("eval/generation_questions.draft.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(c.question_id, c.question) for c in cases[:20]] == [(c["question_id"], c["question"]) for c in original]
    assert not any(c.human_verified for c in cases)


def test_reference_integrity_rejects_changed_quote(tmp_path):
    data = [json.loads(line) for line in DEFAULT_DATASET.read_text(encoding="utf-8").splitlines()]
    data[0]["reference_sources"][0]["quote"] = "invented reference text"
    target = tmp_path / "bad.jsonl"
    target.write_text("\n".join(json.dumps(row) for row in data), encoding="utf-8")
    with pytest.raises(ValueError, match="quote changed"):
        load_benchmark(target)


def test_mock_runner_resume_subsets_and_serialization(cases, tmp_path, capsys):
    directory = tmp_path / "run"
    result = run(cases[:3], directory, mode="mock")
    assert result["question_count"] == 3 and result["run_complete"]
    assert result["semantic_method"] == "not_evaluated" and result["accuracy"] is None
    assert result["citation_validation_pass_rate"] == 1
    rows = read_rows(directory)
    assert all(digest(row["response"]) == row["response_sha256"] for row in rows)
    before = (directory / "results.jsonl").read_bytes()
    run(cases[:3], directory, mode="mock", resume=True)
    assert (directory / "results.jsonl").read_bytes() == before
    assert {r["process_phase"] for r in rows} == {"cold", "warm"}
    assert "initial_generation_request" in rows[0]["profile"]
    assert "evidence_filtering_selection_exclusive" in rows[0]["profile"]
    with pytest.raises(ValueError, match="same dataset"):
        run(cases[:2], directory, mode="mock", resume=True)
    with pytest.raises(ValueError, match="already exists"):
        run(cases[:3], directory, mode="mock")


def test_incremental_resume_after_interrupt(cases, tmp_path):
    directory = tmp_path / "interrupted"
    generator = Mock()
    generator.answer.side_effect = [response(), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        run(cases[:3], directory, mode="mock", generator=generator)
    assert len(read_rows(directory)) == 1
    result = run(cases[:3], directory, mode="mock", resume=True)
    assert result["question_count"] == 3
    assert len(read_rows(directory)) == 3


def test_resume_preserves_and_recovers_truncated_final_record(cases, tmp_path):
    directory = tmp_path / "partial-write"
    run(cases[:1], directory, mode="mock")
    path = directory / "results.jsonl"
    before = path.read_bytes()
    with path.open("ab") as stream:
        stream.write(b'{"question_id": "interrupted')
    broken = path.read_bytes()
    with pytest.raises(ValueError, match="Corrupt"):
        read_rows(directory)
    run(cases[:1], directory, mode="mock", resume=True)
    assert path.read_bytes() == before
    assert next(directory.glob("results.interrupted-*.jsonl")).read_bytes() == broken


def test_resume_does_not_reset_reserved_live_request_budget(cases, tmp_path, monkeypatch):
    import eval.benchmark as module
    directory = tmp_path / "budget"
    constructed = []

    class FakeBudget:
        def __init__(self, config, limit, used=0, reserve=None):
            self.used = used
            self.reserve = reserve
            constructed.append(self)

        def complete(self, messages):
            self.used += 1
            self.reserve()
            raise KeyboardInterrupt()

        def close(self):
            pass

    monkeypatch.setattr(module, "BudgetClient", FakeBudget)
    # Keep retrieval deterministic; only the reserved mock request is interrupted.
    actual_generator = ResearchGenerator
    monkeypatch.setattr(module, "ResearchGenerator", lambda **kwargs:
                        actual_generator(retriever=Retriever([passage()]), client=kwargs["client"], config=kwargs["config"]))
    with pytest.raises(KeyboardInterrupt):
        run(cases[4:5], directory, mode="live", max_requests=1)
    summary = run(cases[4:5], directory, mode="live", max_requests=1, resume=True)
    assert constructed[-1].used == 1
    assert summary["question_count"] == 0 and not summary["run_complete"]
    assert summary["reserved_api_requests"]["generation"] == 1
    assert not summary["request_accounting_complete"]


def test_runner_requires_explicit_mode_and_honors_subset(tmp_path):
    with pytest.raises(SystemExit):
        main(["run", "--output", str(tmp_path / "no-mode")])
    with pytest.raises(SystemExit):
        main(["run", "--mock", "--judge-model", "never-call", "--output", str(tmp_path / "no-judge")])
    target = tmp_path / "subset"
    main(["run", "--mock", "--ids", "GEN-002", "GEN-005", "--limit", "1", "--output", str(target)])
    assert [r["question_id"] for r in read_rows(target)] == ["GEN-002"]


def test_status_and_citation_checks_do_not_claim_semantic_accuracy(cases):
    result = response()
    case = cases[4]
    checks = evaluate(case, result)
    assert checks["citation_validation"] and checks["status_correct"]
    assert checks["accuracy"] is None and checks["semantic_citation_support"] is None
    result.claims[0].citations[0].source_id = "S999"
    assert evaluate(case, result)["citation_validation"] is False
    result = response()
    result.status = "partial"
    result.limitations = ["Missing requested evidence."]
    partial = case.model_copy(update={"acceptable_statuses": ["partial"]})
    assert evaluate(partial, result)["status_correct"]


def test_profile_nested_contexts_do_not_leak():
    with collect() as outer:
        with measure("outer"):
            with collect() as inner:
                with measure("inner"):
                    pass
    assert set(outer) == {"outer"} and set(inner) == {"inner"}
    assert outer["outer"]["seconds"] >= 0 and inner["inner"]["calls"] == 1


def test_generation_profile_separates_repair_usage():
    from test_generation_repair import SequenceClient, invalid
    with collect() as profile:
        result = ResearchGenerator(Retriever([passage()]), SequenceClient([invalid("quote"), Client().result])).answer("SelfCheckGPT")
    assert result.status == "complete"
    assert profile["initial_generation_request"]["usage"]["attempts"] == 1
    assert profile["citation_repair_request"]["usage"]["attempts"] == 1
    assert profile["citation_repair_request"]["usage"]["prompt_tokens"] == 10


def test_bm25_constructs_once_and_is_quiet(chunks, monkeypatch, capsys):
    import src.retrieval.bm25_search as module
    real = module.BM25Okapi
    constructor = Mock(side_effect=real)
    monkeypatch.setattr(module, "BM25Okapi", constructor)
    with collect() as profile:
        index = module.BM25Search(chunks)
        index.search("consistency")
        index.search("facts")
    assert constructor.call_count == 1
    assert not capsys.readouterr().out
    assert profile["bm25_initialization"]["calls"] == 1
    assert profile["bm25_search"]["calls"] == 2


def test_judge_output_is_structured_grounded_and_immutable(cases):
    case, result = cases[4], response()
    chunk = result.citations[0].chunk_id
    verdict = dict(claims=[dict(item_id="1", verdict="supported", reason="Fixture support", evidence_chunk_ids=[chunk])],
                   points=[dict(item_id=p.point_id, verdict="missing", reason="Not in the fixture", evidence_chunk_ids=[], answer_quotes=[]) for p in case.important_points],
                   citations=[dict(item_id="C1", verdict="supported", reason="Fixture support", evidence_chunk_ids=[chunk])])
    transport = Mock()
    transport.responses.create.return_value = SimpleNamespace(status="completed", output_text=json.dumps(verdict),
        usage=SimpleNamespace(input_tokens=100, output_tokens=50))
    judge = LLMJudge("mock-judge", 1, transport)
    original = result.model_dump_json()
    scored = judge.evaluate(case, result)
    assert scored["status"] == "evaluated" and not scored["verified"]
    assert scored["accuracy"] == 1 and scored["completeness"] == 0
    assert result.model_dump_json() == original
    assert scored["response_sha256"] == digest(result.model_dump(mode="json"))
    assert judge.evaluate(case, result)["status"] == "budget_exhausted"
    assert transport.responses.create.call_count == 1
    bad = copy.deepcopy(verdict)
    bad["citations"][0]["evidence_chunk_ids"] = ["invented"]
    with pytest.raises(ValueError, match="reference"):
        validate_judgment(bad, case, result)


def test_judge_failure_sanitized(cases):
    transport = Mock()
    transport.responses.create.side_effect = RuntimeError("secret provider payload")
    result = LLMJudge("mock-judge", 1, transport).evaluate(cases[4], response())
    assert result["status"] == "judge_error" and "secret" not in str(result)


def test_live_budget_wrapper_never_exceeds_limit(monkeypatch):
    transport = Mock()
    monkeypatch.setattr("src.generation.client.OpenAI", lambda **kwargs: transport)
    monkeypatch.setattr("src.generation.client.OpenAIClient.complete", lambda self, messages: ({}, Metrics(attempts=1)))
    reservations = []
    client = BudgetClient(GenerationConfig(), 2, reserve=lambda: reservations.append(1))
    client.complete([])
    client.complete_repair([])
    from src.generation.client import GenerationFailure
    with pytest.raises(GenerationFailure):
        client.complete([])
    assert client.used == 2 and len(reservations) == 2


def test_cost_only_with_explicit_matching_pricing():
    metrics = Metrics(prompt_tokens=1000, completion_tokens=500)
    rates = dict(model="fixture", as_of="2026-10-30", input_per_million_usd=2, output_per_million_usd=4)
    assert estimate_cost(metrics, None, "fixture") is None
    assert estimate_cost(metrics, rates, "other") is None
    assert estimate_cost(metrics, rates, "fixture") == .004


def test_comparison_pairs_identical_cases_and_keeps_quality_separate(cases, tmp_path):
    run(cases[:2], tmp_path / "one", mode="mock")
    before = read_rows(tmp_path / "one")
    after = copy.deepcopy(before)
    after[0]["response"]["metrics"]["total_seconds"] += 1
    after[0]["evaluation"]["citation_validation"] = False
    result = compare(before, after)
    assert result["structural_regressions"] == [before[0]["question_id"]]
    assert result["quality_gate"] == "reject_structural_regression"
    assert result["semantic_score_deltas"]["accuracy"]["count"] == 0
    after[0]["case_sha256"] = "changed"
    with pytest.raises(ValueError):
        compare(before, after)
