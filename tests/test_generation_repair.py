import copy
import json

import pytest

from src.generation import ResearchGenerator
from src.generation.client import GenerationFailure
from src.generation.schemas import Metrics
from test_generation import Client, Retriever, passage


class SequenceClient:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.messages = []

    def complete(self, messages):
        self.messages.append(messages)
        result = next(self.outputs)
        if isinstance(result, Exception):
            raise result
        return result, Metrics(attempts=1, prompt_tokens=10, completion_tokens=5,
                               reasoning_tokens=2, cost_usd=0.01, model="mock",
                               provider="mock", request_id=str(len(self.messages)))


def invalid(kind):
    output = copy.deepcopy(Client().result)
    claim = output["claims"][0]
    if kind == "source":
        claim["citations"][0]["source_id"] = "S999"
    elif kind == "quote":
        claim["citations"][0]["quote"] = "Compares stochastic samples."
    else:
        claim["kind"] = "synthesis"
    return output


def test_first_attempt_does_not_retry():
    client = SequenceClient([Client().result])
    result = ResearchGenerator(Retriever([passage()]), client).answer("SelfCheckGPT")
    assert result.status == "complete"
    assert len(client.messages) == result.metrics.attempts == 1


@pytest.mark.parametrize("kind", ["source", "quote", "comparison"])
def test_successful_repair_supplies_context_and_exact_error(kind):
    from src.generation.citations import validate_and_render
    from src.generation.schemas import ModelAnswer

    original = invalid(kind)
    repaired = copy.deepcopy(Client().result)
    rows = [passage()]
    question = "SelfCheckGPT"
    if kind == "comparison":
        question = "Compare P002 and P003 methods"
        rows.append(passage("P003", text="FActScore evaluates atomic facts."))
        repaired["claims"][0]["kind"] = "synthesis"
        repaired["claims"][0]["text"] = "SelfCheckGPT uses sample consistency while FActScore evaluates atomic facts."
        repaired["claims"][0]["citations"].append({"source_id": "S2", "quote": "evaluates atomic facts"})
    client = SequenceClient([original, repaired])
    result = ResearchGenerator(Retriever(rows), client).answer(question)
    assert result.status == "complete" and result.error is None
    assert result.claims[0].text == repaired["claims"][0]["text"]
    payload = json.loads(client.messages[1][1]["content"])
    assert payload["question"] == question
    assert payload["original_model_output"] == original
    assert payload["evidence"] == json.loads(client.messages[0][1]["content"])["evidence"]
    with pytest.raises(ValueError) as error:
        validate_and_render(ModelAnswer.model_validate(original), result.evidence, result.answer_type, result.paper_ids)
    assert payload["validation_error"] == str(error.value)
    assert payload["output_schema"] == ModelAnswer.model_json_schema()
    assert result.metrics.attempts == 2
    assert (result.metrics.prompt_tokens, result.metrics.completion_tokens, result.metrics.reasoning_tokens) == (20, 10, 4)
    assert result.metrics.cost_usd == 0.02 and result.metrics.request_id == "2"


@pytest.mark.parametrize("repair", [invalid("source"), invalid("quote"), {},
    GenerationFailure("openai_api_error", "Request failed.", metrics=Metrics(
        attempts=1, prompt_tokens=7, completion_tokens=3, accounting_complete=False))])
def test_failed_repair_is_structured_and_never_retries_again(repair, capsys):
    client = SequenceClient([invalid("quote"), repair])
    result = ResearchGenerator(Retriever([passage()]), client).answer("SelfCheckGPT")
    assert len(client.messages) == 2
    assert result.status == "error" and result.error
    assert not result.answer and not result.claims and not result.citations
    assert result.metrics.attempts == 2
    if isinstance(repair, GenerationFailure):
        assert result.error.code == "openai_api_error"
        assert result.metrics.prompt_tokens == 17
        assert not result.metrics.accounting_complete
    else:
        assert result.error.code == "invalid_model_output"
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


@pytest.mark.parametrize("output", [{}, GenerationFailure("attempt_limit", "Limit reached.")])
def test_initial_schema_or_generation_failure_does_not_repair(output):
    client = SequenceClient([output])
    result = ResearchGenerator(Retriever([passage()]), client).answer("SelfCheckGPT")
    assert result.status == "error" and result.error
    assert len(client.messages) == 1


def test_generation_and_validation_timing_are_accumulated_separately(monkeypatch):
    import src.generation.generator as module

    elapsed = [0.0]
    monkeypatch.setattr(module.time, "perf_counter", lambda: elapsed[0])
    strict_validate = module.validate_and_render

    def validate(*args):
        elapsed[0] += 2
        return strict_validate(*args)

    monkeypatch.setattr(module, "validate_and_render", validate)

    class TimedClient(SequenceClient):
        def complete(self, messages):
            elapsed[0] += 3
            return super().complete(messages)

    result = ResearchGenerator(Retriever([passage()]), TimedClient([
        invalid("quote"), Client().result])).answer("SelfCheckGPT")
    assert result.metrics.generation_seconds == 6
    assert result.metrics.validation_seconds == 4
    assert result.metrics.total_seconds == 10


def test_unknown_usage_is_not_presented_as_complete_total():
    total = Metrics(attempts=1, prompt_tokens=10, cost_usd=0.01)
    ResearchGenerator._merge_metrics(total, Metrics(attempts=1, accounting_complete=False))
    assert total.attempts == 2 and total.prompt_tokens is None and total.cost_usd is None
    assert not total.accounting_complete


def test_repair_with_missing_comparison_citation_is_rejected():
    client = SequenceClient([invalid("comparison"), invalid("comparison")])
    rows = [passage(), passage("P003", text="FActScore evaluates atomic facts.")]
    result = ResearchGenerator(Retriever(rows), client).answer("Compare P002 and P003")
    assert result.status == "error" and result.error.code == "invalid_model_output"
    assert not result.claims and not result.citations
    assert len(client.messages) == 2


def test_exhausted_attempt_budget_preserves_initial_usage():
    client = SequenceClient([invalid("quote"), GenerationFailure("attempt_limit", "Limit reached.")])
    result = ResearchGenerator(Retriever([passage()]), client).answer("SelfCheckGPT")
    assert result.error.code == "attempt_limit"
    assert result.metrics.attempts == 1 and result.metrics.prompt_tokens == 10
    assert result.metrics.cost_usd == 0.01
