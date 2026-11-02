"""Deterministic reliability regressions; no API calls or model downloads."""
import copy
import json
import os
from unittest.mock import Mock

import pytest

from src.generation import GenerationConfig, ResearchGenerator
from src.generation.citations import validate_and_render
from src.generation.client import GenerationFailure, OpenAIClient
from src.generation.evidence import select_evidence
from src.generation.papers import interpret, load_catalog
from src.generation.prompts import build_messages
from src.generation.schemas import Evidence, ModelAnswer
from test_generation import Client, Retriever, passage
from test_generation_repair import SequenceClient, invalid


@pytest.fixture
def catalog():
    return load_catalog(GenerationConfig().catalog_path)


@pytest.mark.parametrize("question,expected", [
    ("Compare the evaluation units and findings of SelfCheckGPT and FActScore.", ["methods", "findings"]),
    ("Compare the use of external knowledge in SelfCheckGPT and FActScore.", ["methods"]),
    ("Compare FActScore's treatment of factual recall with TruthfulQA's treatment of informativeness.", ["methods"]),
    ("How do TruthfulQA and SelfCheckGPT construct evaluation data?", ["methods"]),
    ("Compare source-relative support in FActScore with Knowledge F1 in the conversation paper.", ["methods"]),
    ("How do TruthfulQA and SelfCheckGPT differ as failure types?", ["methods"]),
    ("Compare SelfCheckGPT and FActScore in terms of methodology, findings, and limitations.", ["methods", "findings", "limitations"]),
])
def test_requested_comparison_dimensions_do_not_expand_to_unasked_topics(question, expected, catalog):
    result = interpret(question, None, "auto", catalog)
    assert result.answer_type == "comparison" and result.aspects == expected


def test_narrow_comparison_is_not_partial_for_unrequested_findings_and_limitations():
    output = {"status": "complete", "claims": [{
        "text": "SelfCheckGPT uses sample consistency while FActScore uses external knowledge.",
        "kind": "synthesis", "citations": [
            {"source_id": "S1", "quote": "compares stochastic samples"},
            {"source_id": "S2", "quote": "uses external knowledge"}]}], "limitations": []}
    rows = [passage(), passage("P003", text="The FActScore method uses external knowledge to assess atomic facts.")]
    backend, client = Retriever(rows), Client(output)
    result = ResearchGenerator(backend, client).answer("Compare the use of external knowledge in SelfCheckGPT and FActScore.")
    assert result.status == "complete" and not result.limitations
    assert {c.paper_id for c in result.citations} == {"P002", "P003"}
    assert all("What are the limitations" not in call["question"] for call in backend.calls)
    assert len(client.messages) == 1


def test_failed_retrieval_is_error_not_insufficient_evidence():
    class FailedBackend:
        def search(self, **kwargs):
            raise RuntimeError("private backend details")
    client = Client()
    result = ResearchGenerator(FailedBackend(), client).answer("How does SelfCheckGPT work?")
    assert result.status == "error" and result.error.code == "retrieval_unavailable"
    assert not result.abstained and not client.messages
    assert "private" not in result.model_dump_json()


def test_one_paper_failure_still_allows_a_qualified_single_paper_answer():
    class Backend(Retriever):
        def search(self, **kwargs):
            if kwargs["paper_ids"] == ["P003"]:
                raise OSError("private missing index")
            return super().search(**kwargs)
    result = ResearchGenerator(Backend([passage()]), Client()).answer("Compare P002 and P003 methods")
    assert result.status == "partial" and not result.abstained and result.error is None
    assert {c.paper_id for c in result.citations} == {"P002"}
    assert any("P003" in gap and "retrieval failed" in gap for gap in result.limitations)


@pytest.mark.parametrize("section,keep_neighbor", [(None, True), ("Limitations", False)])
def test_numeric_neighbor_recovery_respects_optional_section_filter(section, keep_neighbor, catalog):
    anchor = passage(index=4, text="**0.5** ): The sentence contains some inaccurate information. "
                     "Accurate sentences receive a value of zero.", section="Limitations", year=2023, authors="Manakul")
    neighbor = passage(index=3, text="The method assigns evaluation labels using independent human reviewers. "
                       "The annotation procedure is described here.", section="Methods", year=2023, authors="Manakul")
    backend = Retriever([anchor])
    backend.chunks = [neighbor, anchor]
    result = select_evidence(backend, "SelfCheckGPT annotation values",
        interpret("SelfCheckGPT annotation values", None, "auto", catalog), catalog, 12000,
        year=2023, author="Manakul", section=section)
    assert (neighbor["chunk_id"] in {e.chunk_id for e in result.passages}) is keep_neighbor
    if section:
        assert all(section.casefold() in e.section.casefold() for e in result.passages)


def test_optional_filters_no_matches_abstain_without_a_model_call():
    from src.retrieval.common import candidate_indices
    class FilteredBackend(Retriever):
        def search(self, **kwargs):
            self.calls.append(kwargs)
            indices = candidate_indices(self.rows, kwargs["paper_ids"], True,
                kwargs.get("year"), kwargs.get("author"), kwargs.get("section"))
            return [self.rows[i] for i in indices]
    client = Client()
    backend = FilteredBackend([passage(year=2023, authors="Manakul", section="Methods")])
    result = ResearchGenerator(backend, client).answer("SelfCheckGPT", year=1900)
    assert result.status == "abstained" and result.abstained
    assert result.error is None and not client.messages
    assert result.metrics.attempts == 0


def test_initial_prompt_and_repair_use_real_source_quote_spans(catalog):
    row = passage(text="The _n_ -gram method uses samples.\n\nMeasured accuracy is 81.2%, not 100%.")
    backend = Retriever([row])
    interpreted = interpret("How does SelfCheckGPT work?", None, "auto", catalog)
    selected = select_evidence(backend, "SelfCheckGPT", interpreted, catalog, 12000)
    payload = json.loads(build_messages("SelfCheckGPT", interpreted, selected.passages, [])[1]["content"])
    candidates = payload["verbatim_quote_candidates"]["S1"]
    assert candidates and all(quote in row["text"] for quote in candidates)
    assert any("_n_ -gram" in quote for quote in candidates)
    assert any("81.2%, not 100%" in quote for quote in candidates)


def test_failed_repair_preserves_only_strictly_valid_claims_as_partial():
    output = copy.deepcopy(Client().result)
    output["claims"].append({"text": "Unsupported fabricated result.", "kind": "reported",
                             "citations": [{"source_id": "S1", "quote": "A result absent from the source."}]})
    client = SequenceClient([output, copy.deepcopy(output)])
    result = ResearchGenerator(Retriever([passage(year=2023, authors="Manakul", section="Methods")]), client).answer("SelfCheckGPT")
    assert result.status == "partial" and result.error is None and not result.abstained
    assert len(result.claims) == len(result.citations) == 1
    assert "fabricated" not in result.answer and "Unsupported" not in result.answer
    assert any("omitted" in limitation for limitation in result.limitations)
    citation = result.citations[0]
    assert citation.paper_id == "P002" and citation.pdf_page == 1
    assert citation.year == 2023 and citation.authors == "Manakul" and citation.section == "Methods"
    validated = ModelAnswer(status="partial", claims=result.claims, limitations=result.limitations)
    answer, citations = validate_and_render(validated, result.evidence, result.answer_type, result.paper_ids)
    assert answer == result.answer and citations == result.citations
    assert len(client.messages) == result.metrics.attempts == 2


def test_failed_repair_does_not_keep_a_one_sided_synthesis():
    output = copy.deepcopy(Client().result)
    output["claims"].append({"text": "An unsupported cross-paper comparison.", "kind": "synthesis",
                             "citations": [{"source_id": "S1", "quote": "compares stochastic samples"}]})
    result = ResearchGenerator(Retriever([passage(), passage("P003", text="The FActScore method evaluates atomic facts.")]),
        SequenceClient([output, output])).answer("Compare P002 and P003 methods")
    assert result.status == "partial" and len(result.claims) == 1
    assert result.claims[0].kind == "reported"
    assert "unsupported cross-paper" not in result.answer
    assert any("P003" in gap for gap in result.limitations)


@pytest.mark.parametrize("question", [
    "What launch procedure is prescribed?",
    "What exact GPU model did the authors use?",
    "What was the unreported GalacticScore result?",
])
def test_irrelevant_nonempty_retrieval_can_abstain_without_publishing_claims(question):
    output = {"status": "abstained", "claims": [],
              "limitations": ["These passages do not support the requested information."]}
    client = Client(output)
    result = ResearchGenerator(Retriever([passage()]), client).answer(question, paper_ids=["P002"])
    assert result.evidence and len(client.messages) == 1
    assert result.status == "abstained" and result.abstained and result.error is None
    assert "sufficient usable evidence" in result.answer
    assert not result.claims and not result.citations


def test_partially_supported_question_preserves_specific_missing_component():
    output = copy.deepcopy(Client().result)
    output.update(status="partial", limitations=["The supplied passages do not identify the GPU model."])
    result = ResearchGenerator(Retriever([passage()]), Client(output)).answer(
        "How does SelfCheckGPT work and what GPU model did it use?")
    assert result.status == "partial" and result.claims and not result.abstained
    assert output["limitations"][0] in result.limitations
    assert "GPU" not in result.answer


def test_salvaged_partial_preserves_original_missing_component():
    output = copy.deepcopy(Client().result)
    output.update(status="partial", limitations=["The exact GPU model is not supported."])
    output["claims"].append(invalid("quote")["claims"][0])
    result = ResearchGenerator(Retriever([passage()]), SequenceClient([output, output])).answer(
        "How does SelfCheckGPT work and what GPU model did it use?")
    assert result.status == "partial" and len(result.claims) == 1
    assert output["limitations"][0] in result.limitations


def test_quote_integrity_alone_cannot_establish_semantic_support():
    # Characterize the validation boundary: this is a fabricated claim attached
    # to a real quote. Semantic rejection still depends on the generator/review.
    output = copy.deepcopy(Client().result)
    output["claims"][0]["text"] = "The spacecraft launch procedure has three stages."
    source = Evidence(**passage(), source_id="S1")
    answer, citations = validate_and_render(ModelAnswer.model_validate(output), [source], "qa", ["P002"])
    assert citations and "spacecraft" in answer


def test_api_error_during_repair_is_never_presented_as_partial_or_abstention():
    output = copy.deepcopy(Client().result)
    output["claims"].append(invalid("quote")["claims"][0])
    result = ResearchGenerator(Retriever([passage()]), SequenceClient([
        output, GenerationFailure("openai_api_error", "Request failed.")])).answer("SelfCheckGPT")
    assert result.status == "error" and result.error.code == "openai_api_error"
    assert not result.abstained and not result.answer and not result.claims


def test_project_root_dotenv_is_loaded_without_network_or_cwd_dependence(tmp_path, monkeypatch):
    import src.generation.client as module
    root = tmp_path / "project"
    root.mkdir()
    env = root / ".env"
    env.write_text("OPENAI_API_KEY=fixture-key-not-a-real-secret\n")
    before = env.read_bytes()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    # Register restoration even when the variable was initially absent; dotenv
    # itself mutates os.environ rather than using the monkeypatch fixture.
    monkeypatch.setenv("OPENAI_API_KEY", "removed-fixture")
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setattr(module, "PROJECT_ROOT", root)
    transport = Mock()
    def constructor(**kwargs):
        assert os.environ["OPENAI_API_KEY"] == "fixture-key-not-a-real-secret"
        assert kwargs["max_retries"] == 0
        return transport
    monkeypatch.setattr(module, "OpenAI", constructor)
    client = OpenAIClient(GenerationConfig())
    assert client.client is transport and env.read_bytes() == before
    transport.responses.create.assert_not_called()


def test_process_api_key_takes_precedence_over_dotenv(tmp_path, monkeypatch):
    import src.generation.client as module
    (tmp_path / ".env").write_text("OPENAI_API_KEY=file-fixture\n")
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-fixture")
    monkeypatch.setattr(module, "OpenAI", Mock())
    OpenAIClient(GenerationConfig())
    assert os.environ["OPENAI_API_KEY"] == "environment-fixture"


def test_missing_key_is_structured_and_never_calls_sdk(tmp_path, monkeypatch):
    import src.generation.client as module
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    constructor = Mock(side_effect=AssertionError("No API client should be created"))
    monkeypatch.setattr(module, "OpenAI", constructor)
    generator = ResearchGenerator(Retriever([passage()]), config=GenerationConfig())
    result = generator.answer("SelfCheckGPT")
    assert result.status == "error" and result.error.code == "missing_api_key"
    assert not result.abstained and result.metrics.attempts == 0
    constructor.assert_not_called()
    generator.close()


@pytest.mark.parametrize("status,code", [(401, "invalid_api_key"), (429, "insufficient_quota")])
def test_authentication_and_exhausted_quota_do_not_spend_retry_budget(status, code, monkeypatch):
    import httpx
    from openai import AuthenticationError, RateLimitError
    from test_generation_client import client_for, success

    error_type = AuthenticationError if status == 401 else RateLimitError
    error = error_type("private provider details", response=httpx.Response(
        status, request=httpx.Request("POST", "https://example.test")), body={"code": code})
    client, transport = client_for([error, success()], max_attempts=2)
    sleep = Mock(side_effect=AssertionError("Permanent errors must not retry"))
    monkeypatch.setattr("src.generation.client.time.sleep", sleep)
    with pytest.raises(GenerationFailure) as failure:
        client.complete([])
    assert failure.value.error.code == "openai_api_error" and not failure.value.error.retryable
    assert transport.responses.create.call_count == failure.value.metrics.attempts == 1
    assert "private provider details" not in str(failure.value)
    sleep.assert_not_called()
