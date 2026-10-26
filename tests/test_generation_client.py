import json

import httpx
import pytest
from pydantic import ValidationError

from src.generation.client import GenerationFailure, OllamaClient
from src.generation.config import GenerationConfig

MODEL = GenerationConfig().model
ANSWER = {"status": "complete", "claims": [{"text": "Reported claim.", "kind": "reported",
          "citations": [{"source_id": "S1", "quote": "source words"}]}], "limitations": []}


def success(**updates):
    return {"model": MODEL, "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(ANSWER)},
            "prompt_eval_count": 100, "eval_count": 20, **updates}


def tags():
    return {"models": [{"name": MODEL, "details": {"format": "gguf"}}]}


def client_for(responses, *, listing=None, attempt_limit=25, max_attempts=1):
    requests, sleeps = [], []

    def handle(request):
        requests.append(request)
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        if request.method == "GET":
            assert request.url.path == "/api/tags"
            return httpx.Response(200, json=listing if listing is not None else tags())
        assert request.url.path == "/api/chat"
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    http = httpx.Client(transport=httpx.MockTransport(handle))
    config = GenerationConfig(attempt_limit=attempt_limit, max_attempts=max_attempts)
    return OllamaClient(config, http=http, sleep=sleeps.append), requests, sleeps


def test_local_request_schema_and_native_token_metrics():
    client, requests, _ = client_for([httpx.Response(200, json=success())])
    output, metrics = client.complete([{"role": "user", "content": "Question"}])
    body = json.loads(requests[1].content)
    assert body["model"] == "qwen3:8b"
    assert body["format"]["additionalProperties"] is False
    assert body["format"]["properties"]["claims"]
    assert body["think"] is False and body["stream"] is False
    assert body["options"] == {"num_predict": 2048, "num_ctx": 8192, "temperature": 0}
    assert "provider" not in body and "api_key" not in body
    assert output.status == "complete"
    assert metrics.provider == "ollama" and metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 20 and metrics.reasoning_tokens == 0
    assert metrics.cost_usd == 0 and metrics.accounting_complete


@pytest.mark.parametrize("url", [
    "https://openrouter.ai", "http://192.168.1.10:11434", "http://localhost.evil.test:11434",
    "http://user:password@localhost:11434", "http://localhost:11434/v1", "file:///tmp/socket",
    "http://localhost:bad", "http://localhost:11434?token=secret",
])
def test_remote_or_invalid_base_urls_rejected(url):
    with pytest.raises(ValueError):
        GenerationConfig(ollama_base_url=url)


@pytest.mark.parametrize("listing,code", [
    ({"models": []}, "model_not_installed"),
    ({"models": None}, "ollama_unavailable"),
    ({}, "ollama_unavailable"),
    ({"models": [{"name": MODEL, "remote_host": "https://ollama.com", "details": {"format": "gguf"}}]}, "local_model_required"),
    ({"models": [{"name": MODEL, "details": {"format": "cloud"}}]}, "local_model_required"),
])
def test_missing_models_never_generate_or_pull(listing, code):
    client, requests, _ = client_for([], listing=listing)
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == code
    assert all(r.method == "GET" for r in requests)
    assert error.value.metrics.attempts == 0


def test_tags_network_failure_is_sanitized():
    def fail(request):
        raise httpx.ConnectError("private runtime details")
    client = OllamaClient(GenerationConfig(), http=httpx.Client(transport=httpx.MockTransport(fail)))
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "ollama_unavailable"
    assert "private" not in str(error.value)


@pytest.mark.parametrize("status,code", [(400, "ollama_error"), (404, "model_not_installed"),
                                        (429, "ollama_error"), (500, "ollama_error")])
def test_runtime_errors_are_sanitized_without_default_retry(status, code):
    client, requests, sleeps = client_for([httpx.Response(status, json={"error": "private runtime path"})])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == code
    assert "private" not in str(error.value) and len(requests) == 2 and not sleeps


@pytest.mark.parametrize("failure,code", [(httpx.ReadTimeout("slow"), "request_timeout"),
                                         (httpx.ConnectError("offline"), "ollama_unavailable")])
def test_transport_failures_do_not_duplicate_expensive_local_jobs(failure, code):
    client, _, sleeps = client_for([failure], max_attempts=2)
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == code and error.value.metrics.attempts == 1
    assert not error.value.metrics.accounting_complete and not sleeps


def test_explicit_retry_budget_on_server_error():
    client, requests, sleeps = client_for([httpx.Response(503, json={"error": "busy"}),
                                          httpx.Response(200, json=success())], max_attempts=2)
    _, metrics = client.complete([])
    assert metrics.attempts == 2 and len(sleeps) == 1 and not metrics.accounting_complete
    assert len([r for r in requests if r.method == "POST"]) == 2


def test_shared_attempt_cap_includes_failed_inference():
    client, requests, _ = client_for([httpx.Response(500, json={"error": "busy"})], attempt_limit=1)
    with pytest.raises(GenerationFailure):
        client.complete([])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "attempt_limit"
    assert len([r for r in requests if r.method == "POST"]) == 1


@pytest.mark.parametrize("payload", [
    [], {}, success(done=False), success(done_reason="length"), success(model="other-model"),
    success(message={"content": ""}), success(message={"content": "not JSON"}),
    success(message={"content": json.dumps({**ANSWER, "extra": "invented"})}),
    success(message={"content": json.dumps({"status": "complete", "claims": [], "limitations": []})}),
])
def test_invalid_or_truncated_output_is_withheld_without_repair(payload):
    client, requests, sleeps = client_for([httpx.Response(200, json=payload)])
    with pytest.raises(GenerationFailure) as error:
        client.complete([])
    assert error.value.error.code == "invalid_model_output"
    assert not sleeps and len(requests) == 2


def test_missing_native_usage_counts_remain_unknown():
    payload = success()
    payload.pop("prompt_eval_count")
    payload.pop("eval_count")
    client, _, _ = client_for([httpx.Response(200, json=payload)])
    _, metrics = client.complete([])
    assert metrics.prompt_tokens is None and metrics.completion_tokens is None
    assert metrics.cost_usd == 0 and not metrics.accounting_complete


def test_config_ignores_obsolete_hosted_credentials(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("OPENROUTER_API_KEY=unused-secret\nOPENROUTER_MODEL=hosted-model\n")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    config = GenerationConfig.from_env(path)
    assert config.model == "qwen3:8b" and "unused-secret" not in repr(config)
    assert "api_key" not in config.model_dump()
    with pytest.raises(ValidationError):
        GenerationConfig(max_tokens=8192, num_ctx=8192)
