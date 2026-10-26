import json

import httpx
import pytest
from pydantic import SecretStr

from src.generation.client import GenerationFailure, OpenRouterClient
from src.generation.config import GenerationConfig

MODEL = GenerationConfig().model
ANSWER = {"status": "complete", "claims": [{"text": "Reported claim.", "kind": "reported",
          "citations": [{"source_id": "S1", "quote": "source words"}]}], "limitations": []}


def success(**updates):
    return {"id": "test-request", "provider": "test-provider", "choices": [{
        "finish_reason": "stop", "message": {"content": json.dumps(ANSWER)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0,
                  "completion_tokens_details": {"reasoning_tokens": 5}}, **updates}


def catalog(pricing=None, supported=None):
    return {"data": [{"id": MODEL, "pricing": pricing or {"prompt": "0", "completion": "0"},
                      "supported_parameters": supported if supported is not None else ["structured_outputs", "response_format", "reasoning"]}]}


def client_for(responses, *, model=MODEL, listing=None, attempt_limit=25):
    requests, sleeps = [], []

    def handle(request):
        requests.append(request)
        if request.method == "GET":
            assert "authorization" not in request.headers
            return httpx.Response(200, json=listing if listing is not None else catalog())
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    http = httpx.Client(transport=httpx.MockTransport(handle))
    config = GenerationConfig(api_key=SecretStr("private-key"), model=model, attempt_limit=attempt_limit)
    return OpenRouterClient(config, http=http, sleep=sleeps.append), requests, sleeps


def test_free_routing_structured_output_and_metrics():
    client, requests, _ = client_for([httpx.Response(200, json=success())])
    output, metrics = client.complete([{"role": "user", "content": "Question"}])
    body = json.loads(requests[1].content)
    assert body["model"] == MODEL and "models" not in body
    assert body["provider"] == {"require_parameters": True, "max_price": {"prompt": 0, "completion": 0}}
    assert body["response_format"]["json_schema"]["strict"]
    assert body["reasoning"]["effort"] == "low" and not body["stream"]
    assert output.status == "complete"
    assert metrics.prompt_tokens == 100 and metrics.reasoning_tokens == 5
    assert metrics.cost_usd == 0 and metrics.accounting_complete
    assert "private-key" not in repr(client.config)


def test_missing_key_and_paid_model_never_infer():
    requests = []
    http = httpx.Client(transport=httpx.MockTransport(lambda r: requests.append(r)))
    with pytest.raises(GenerationFailure) as error:
        OpenRouterClient(GenerationConfig(), http=http).complete([])
    assert error.value.error.code == "missing_api_key" and not requests
    client, requests, _ = client_for([], model="paid/model")
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "free_policy" and not requests


@pytest.mark.parametrize("listing", [
    {"data": []}, {"data": None}, {}, catalog({"prompt": "0.001", "completion": "0"}),
    catalog({"prompt": "0", "completion": "0", "internal_reasoning": "0.01"}),
    catalog({"prompt": "NaN", "completion": "0"}),
])
def test_catalog_failures_never_infer(listing):
    client, requests, _ = client_for([], listing=listing)
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "model_unavailable"
    assert all(r.method == "GET" for r in requests)


def test_catalog_network_failure_is_closed():
    def fail(request):
        raise httpx.ConnectError("private provider error")
    client = OpenRouterClient(GenerationConfig(api_key=SecretStr("secret")),
                              http=httpx.Client(transport=httpx.MockTransport(fail)))
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert "private" not in str(error.value) and error.value.metrics.attempts == 0


def test_json_only_alternative_has_no_silent_schema_fallback():
    client, requests, _ = client_for([httpx.Response(200, json=success())],
                                    listing=catalog(supported=["response_format"]))
    client.complete([])
    assert json.loads(requests[1].content)["response_format"] == {"type": "json_object"}
    client, requests, _ = client_for([], listing=catalog(supported=[]))
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "unsupported_model" and len(requests) == 1


@pytest.mark.parametrize("status,code", [(400, "invalid_request"), (401, "authentication_failed"),
    (402, "credits_required"), (403, "access_denied"), (404, "invalid_model")])
def test_permanent_errors_sanitized_without_retry(status, code):
    client, requests, sleeps = client_for([httpx.Response(status, json={"error": {"code": status, "message": "private-key"}})])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == code
    assert "private-key" not in str(error.value) and len(requests) == 2 and not sleeps


@pytest.mark.parametrize("first", [
    httpx.Response(429, headers={"Retry-After": "2"}, json={"error": {"code": 429}}),
    httpx.Response(503, json={"error": {"code": 503}}),
    httpx.Response(200, json={"error": {"code": 502}}),
    httpx.ReadTimeout("timeout"),
])
def test_transient_errors_retry_once_and_account_unknown_attempt(first):
    client, requests, sleeps = client_for([first, httpx.Response(200, json=success())])
    _, metrics = client.complete([])
    assert metrics.attempts == 2 and client.attempts_used == 2 and len(sleeps) == 1
    assert metrics.prompt_tokens == 100 and not metrics.accounting_complete
    assert len([r for r in requests if r.method == "POST"]) == 2


@pytest.mark.parametrize("headers,message", [({"Retry-After": "60"}, "busy"),
    ({}, "daily quota exceeded"), ({"Retry-After": "not-a-date"}, "busy")])
def test_daily_quota_and_long_wait_do_not_retry(headers, message):
    client, _, sleeps = client_for([httpx.Response(429, headers=headers, json={"error": {"code": 429, "message": message}})])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "quota_exhausted" and not sleeps


def test_shared_attempt_cap_includes_failures():
    client, requests, _ = client_for([httpx.Response(503, json={"error": {"code": 503}})], attempt_limit=1)
    with pytest.raises(GenerationFailure):
        client.complete([])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "attempt_limit"
    assert len([r for r in requests if r.method == "POST"]) == 1


@pytest.mark.parametrize("payload", [
    [], {}, success(choices=[]),
    success(choices=[{"finish_reason": "length", "message": {"content": json.dumps(ANSWER)}}]),
    success(choices=[{"finish_reason": "stop", "message": {"refusal": "No", "content": ""}}]),
    success(choices=[{"finish_reason": "stop", "message": {"content": "not JSON"}}]),
    success(choices=[{"finish_reason": "stop", "message": {"content": json.dumps({**ANSWER, "extra": "invented"})}}]),
])
def test_invalid_output_does_not_trigger_paid_repair(payload):
    client, requests, sleeps = client_for([httpx.Response(200, json=payload)])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "invalid_model_output" and not sleeps
    assert len(requests) == 2


def test_missing_usage_is_unknown_not_zero():
    payload = success()
    payload.pop("usage")
    client, _, _ = client_for([httpx.Response(200, json=payload)])
    _, metrics = client.complete([])
    assert metrics.cost_usd is None and metrics.prompt_tokens is None and not metrics.accounting_complete


def test_retry_usage_totals_and_metrics_on_invalid_output():
    first = success(error={"code": 503})
    second = success(choices=[])
    client, _, _ = client_for([httpx.Response(200, json=first), httpx.Response(200, json=second)])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.metrics.prompt_tokens == 200
    assert error.value.metrics.completion_tokens == 40
