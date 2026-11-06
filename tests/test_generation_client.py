import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from openai import APIConnectionError

from src.generation.client import GenerationFailure, OpenAIClient
from src.generation.config import GenerationConfig


ANSWER = {"status": "complete", "claims": [{"text": "Reported claim.", "kind": "reported",
          "citations": [{"source_id": "S1", "quote": "source words"}]}], "limitations": []}


def success(**updates):
    return SimpleNamespace(**{"id": "resp_mock", "status": "completed",
        "output_text": json.dumps(ANSWER), "usage": SimpleNamespace(input_tokens=100,
        output_tokens=20, output_tokens_details=SimpleNamespace(reasoning_tokens=5)), **updates})


def client_for(responses, **config):
    transport = Mock()
    transport.responses.create.side_effect = responses
    return OpenAIClient(GenerationConfig(**config), client=transport), transport


def test_request_schema_and_token_metrics():
    client, transport = client_for([success()])
    output, metrics = client.complete([{"role": "system", "content": "rules"},
                                       {"role": "user", "content": "question"}])
    body = transport.responses.create.call_args.kwargs
    assert body["instructions"] == "rules" and body["input"] == "question"
    assert body["text"]["format"]["strict"] is True
    assert body["text"]["format"]["schema"]["additionalProperties"] is False
    assert output.status == "complete"
    assert (metrics.attempts, metrics.prompt_tokens, metrics.completion_tokens, metrics.reasoning_tokens) == (1, 100, 20, 5)


@pytest.mark.parametrize("output", ["not JSON", "{}", json.dumps({**ANSWER, "extra": 1})])
def test_invalid_schema_is_structured_and_not_retried(output):
    client, transport = client_for([success(output_text=output)], max_attempts=2)
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "invalid_model_output"
    assert error.value.metrics.prompt_tokens == 100
    assert transport.responses.create.call_count == 1


def test_repair_never_retries_transport_errors():
    failure = APIConnectionError(request=httpx.Request("POST", "https://example.test"))
    client, transport = client_for([failure, success()], max_attempts=2)
    with pytest.raises(GenerationFailure) as error:
        client.complete_repair([])
    assert error.value.error.code == "openai_api_error"
    assert error.value.metrics.attempts == 1
    assert not error.value.metrics.accounting_complete
    assert transport.responses.create.call_count == 1


def test_shared_attempt_cap_applies_to_repair():
    client, transport = client_for([success()], attempt_limit=1)
    client.complete([])
    with pytest.raises(GenerationFailure) as error:
        client.complete_repair([])
    assert error.value.error.code == "attempt_limit"
    assert error.value.metrics.attempts == 0
    assert transport.responses.create.call_count == 1


def test_transport_retry_preserves_incomplete_accounting(monkeypatch):
    monkeypatch.setattr("src.generation.client.time.sleep", lambda _: None)
    failure = APIConnectionError(request=httpx.Request("POST", "https://example.test"))
    client, transport = client_for([failure, success()], max_attempts=2)
    _, metrics = client.complete([])
    assert metrics.attempts == 2 and not metrics.accounting_complete
    assert transport.responses.create.call_count == 2


def test_incomplete_response_preserves_usage():
    client, _ = client_for([success(status="incomplete")])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "incomplete_generation"
    assert error.value.metrics.completion_tokens == 20


def test_missing_usage_is_unknown():
    client, _ = client_for([success(usage=None)])
    _, metrics = client.complete([])
    assert metrics.prompt_tokens is None and metrics.completion_tokens is None
    assert not metrics.accounting_complete


def test_api_schema_is_not_duplicated_in_prompt_and_evidence_is_preserved():
    from src.generation.schemas import ModelAnswer
    payload = {"question": "Question", "evidence": [{"text": "Original source text", "source_id": "S1"}],
               "output_schema": ModelAnswer.model_json_schema()}
    messages = [{"role": "user", "content": json.dumps(payload)}]
    before = json.dumps(messages)
    client, transport = client_for([success()])
    client.complete(messages)
    arguments = transport.responses.create.call_args.kwargs
    sent = json.loads(arguments["input"])
    assert sent == {"question": payload["question"], "evidence": payload["evidence"]}
    assert arguments["text"]["format"]["schema"] == payload["output_schema"]
    assert json.dumps(messages) == before
