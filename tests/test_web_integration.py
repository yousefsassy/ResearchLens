"""HTTP/application regressions. All inference is mocked; sockets stay local."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient
import pytest

from app.api import create_app
from app.client import APIClientError, ResearchAPIClient
from app.feedback import FeedbackStore
from app.schemas import AskRequest, FeedbackRequest
from app.service import ResearchService
from src.generation import GenerationConfig, ResearchGenerator
from src.generation.client import OpenAIClient
from src.generation.schemas import Clarification, ErrorInfo, GenerationResponse
from test_generation import Client, Retriever, passage
from test_generation_client import success


def grounded():
    return ResearchGenerator(Retriever([passage()]), Client()).answer("How does SelfCheckGPT work?")


class Generator:
    def __init__(self, result=None, index_valid=True):
        self.result = result or grounded()
        self.calls = []
        self.retriever = SimpleNamespace(chunks=[passage()],
            status=lambda: {"index": {"valid": index_valid}})
        self.config = GenerationConfig()
        self.close = Mock()

    def answer(self, question, paper_ids=None, answer_type="auto", **filters):
        self.calls.append((question, paper_ids, answer_type, filters))
        return self.result.model_copy(update={"question": question})


def service_for(generator, tmp_path, **kwargs):
    return ResearchService(generator_factory=lambda: generator,
        feedback_store=FeedbackStore(tmp_path / "feedback.jsonl"), **kwargs)


@pytest.mark.parametrize("payload", [
    {"question": "What causes hallucination?"},
    {"question": "SelfCheckGPT methods", "paper_ids": ["P002"]},
    {"question": "SelfCheckGPT methods", "paper_ids": ["P002"], "year": 2023,
     "author": " Manakul ", "section": " Methods "},
    {"question": "Compare P002 and P003", "paper_ids": ["P002", "P003"], "answer_type": "comparison"},
])
def test_http_forwards_optional_scope_and_filters(tmp_path, payload):
    gen = Generator()
    with TestClient(create_app(service_for(gen, tmp_path))) as api:
        response = api.post("/ask", json=payload)
        assert response.status_code == 200 and response.json()["schema_version"] == "1.0"
        question, scope, kind, filters = gen.calls[-1]
        request = AskRequest(**payload)
        assert (question, scope, kind) == (request.question, request.paper_ids, request.answer_type)
        assert filters == {"year": request.year, "author": request.author, "section": request.section}


@pytest.mark.parametrize("status", ["complete", "partial", "abstained", "needs_clarification"])
def test_expected_rag_outcomes_remain_http_200(tmp_path, status):
    result = grounded()
    result.status = status
    if status == "partial": result.limitations = ["One requested component is missing."]
    if status in {"abstained", "needs_clarification"}:
        result.claims, result.citations = [], []
        result.answer = "I don't have sufficient usable evidence." if status == "abstained" else ""
        result.abstained = status == "abstained"
    if status == "needs_clarification":
        result.clarification = Clarification(question="Which paper?", candidate_paper_ids=["P002"])
    with TestClient(create_app(service_for(Generator(result), tmp_path))) as api:
        response = api.post("/ask", json={"question": "A valid question"})
        assert response.status_code == 200 and response.json()["status"] == status
        assert response.json()["error"] is None


@pytest.mark.parametrize("code,status", [("missing_api_key",503),("retrieval_unavailable",503),
    ("openai_api_error",502),("openai_timeout",504),("invalid_model_output",502),("incomplete_generation",502)])
def test_http_preserves_structured_infrastructure_errors(tmp_path, code, status):
    result = GenerationResponse(question="Fixture", status="error",
        error=ErrorInfo(code=code, message="Safe diagnostic", retryable=True))
    with TestClient(create_app(service_for(Generator(result), tmp_path))) as api:
        response = api.post("/ask", json={"question": "A valid question"})
        assert response.status_code == status
        assert response.json()["error"] == result.error.model_dump()
        assert response.json()["abstained"] is False


@pytest.mark.parametrize("updates", [{"question":"  "},{"paper_ids":["P999"]},
    {"paper_ids":[]},{"year":True},{"year":"2023"},{"year":0},{"year":2023.5},
    {"answer_type":"comparison"},{"answer_type":"comparison","paper_ids":["P002"]},
    {"category":"new-filter"}])
def test_invalid_requests_do_not_reach_generation(tmp_path, updates):
    gen = Generator()
    with TestClient(create_app(service_for(gen, tmp_path))) as api:
        assert api.post("/ask",json={"question":"A valid question",**updates}).status_code == 422
        assert not gen.calls


def test_bad_index_degrades_health_but_papers_remain_available(tmp_path):
    with TestClient(create_app(service_for(Generator(index_valid=False), tmp_path))) as api:
        health = api.get("/health")
        assert health.status_code == 503 and health.json()["index_valid"] is False
        assert health.json()["status"] == "degraded"
        assert len(api.get("/papers").json()) == 8
        response = api.post("/ask",json={"question":"A valid question"})
        assert response.status_code == 503 and response.json()["error"]["code"] == "retrieval_unavailable"


def test_missing_generation_catalog_is_not_reported_healthy(tmp_path):
    gen=Generator()
    config=GenerationConfig(catalog_path=tmp_path / "absent-catalog.json")
    with TestClient(create_app(service_for(gen,tmp_path,config=config))) as api:
        assert api.get("/health").status_code==503
        assert api.get("/papers").status_code==503
        assert api.post("/ask",json={"question":"A valid question"}).status_code==503
        assert not gen.calls


def configured_service(tmp_path, sdk):
    backend = Retriever([passage()])
    backend.chunks = backend.rows
    backend.status = lambda: {"index":{"valid":True}}
    backend.encoder = SimpleNamespace(encode_query=Mock())
    factory = Mock(return_value=backend)
    owner = OpenAIClient(GenerationConfig(), client=sdk)
    service = ResearchService(retriever_factory=factory, client_factory=Mock(return_value=owner),
        feedback_store=FeedbackStore(tmp_path / "feedback.jsonl"))
    return service,backend,factory,owner


def test_35_questions_have_independent_budgets_and_shared_resources(tmp_path):
    sdk = Mock()
    sdk.responses.create.return_value = success(output_text=json.dumps(Client().result))
    service, backend, factory, owner = configured_service(tmp_path,sdk)
    with TestClient(create_app(service)) as api:
        for _ in range(35):
            response = api.post("/ask",json={"question":"SelfCheckGPT methods"})
            assert response.status_code == 200 and response.json()["status"] == "complete"
            assert response.json()["metrics"]["attempts"] == 1
        assert api.get("/health").status_code == 200
        sdk.close.assert_not_called()
    assert sdk.responses.create.call_count == 35 and owner.attempts_used == 0
    factory.assert_called_once()
    backend.encoder.encode_query.assert_called_once()
    sdk.close.assert_called_once()
    service.close()
    sdk.close.assert_called_once()


def test_repairs_use_at_most_two_attempts_per_question(tmp_path):
    sdk = Mock()
    bad = Client().result
    bad["claims"][0]["citations"][0]["quote"] = "Invented quote"
    sdk.responses.create.side_effect = [success(output_text=json.dumps(value))
        for _ in range(3) for value in (bad, Client().result)]
    service,*_ = configured_service(tmp_path,sdk)
    with TestClient(create_app(service)) as api:
        for _ in range(3):
            response=api.post("/ask",json={"question":"SelfCheckGPT methods"})
            assert response.status_code == 200 and response.json()["metrics"]["attempts"] == 2
    assert sdk.responses.create.call_count == 6


def test_missing_credentials_are_degraded_without_any_request(tmp_path):
    service, backend, *_ = configured_service(tmp_path,Mock())
    service._client_factory = lambda config: SimpleNamespace(client=None,close=Mock())
    with TestClient(create_app(service)) as api:
        assert api.get("/health").status_code == 503
        result=api.post("/ask",json={"question":"SelfCheckGPT methods"})
        assert result.status_code == 503 and result.json()["error"]["code"] == "missing_api_key"


def test_busy_requests_have_bounded_wait(tmp_path):
    service=service_for(Generator(),tmp_path,acquire_timeout=.01)
    with TestClient(create_app(service)) as api:
        service._lock.acquire()
        try:
            started=time.perf_counter()
            response=api.post("/ask",json={"question":"A valid question"})
            assert time.perf_counter()-started < 1
            assert response.status_code == 503 and response.json()["error"]["code"] == "service_busy"
        finally: service._lock.release()


def test_actual_sdk_timeout_class_maps_to_504(tmp_path):
    from openai import APITimeoutError
    sdk=Mock();sdk.responses.create.side_effect=APITimeoutError(request=httpx.Request("POST","https://example.test"))
    service,*_=configured_service(tmp_path,sdk)
    with TestClient(create_app(service)) as api:
        response=api.post("/ask",json={"question":"SelfCheckGPT methods"})
        assert response.status_code == 504 and response.json()["error"]["code"] == "openai_timeout"
    assert sdk.responses.create.call_count == 1


def test_internal_value_error_is_not_mislabeled_as_bad_user_input(tmp_path):
    gen=Generator()
    gen.answer=Mock(side_effect=ValueError("private internal failure"))
    with TestClient(create_app(service_for(gen,tmp_path))) as api:
        response=api.post("/ask",json={"question":"A valid question"})
        assert response.status_code==503
        assert response.json()["error"]["code"]=="service_unavailable"
        assert "private" not in response.text


def test_feedback_is_idempotent_even_after_store_recreation(tmp_path):
    feedback=FeedbackRequest(submission_id="submission-1",request_id="answer-1",rating="up")
    service=service_for(Generator(),tmp_path)
    with TestClient(create_app(service)) as api:
        for _ in range(2): assert api.post("/feedback",json=feedback.model_dump()).status_code == 200
    FeedbackStore(service.feedback.path).add(feedback)
    lines=service.feedback.path.read_text().splitlines()
    assert len(lines)==1 and json.loads(lines[0])["request_id"]=="answer-1"


@pytest.mark.parametrize("exception", [httpx.ConnectError("private details"),httpx.ReadTimeout("private details")])
def test_http_client_transport_failures_are_safe_and_never_retried(exception):
    calls=[]
    def respond(request): calls.append(request);raise exception
    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client=ResearchAPIClient(client=transport)
        with pytest.raises(APIClientError) as error: client.ask(AskRequest(question="A valid question"))
    assert len(calls)==1 and "private" not in str(error.value)


@pytest.mark.parametrize("status,body",[(200,{"broken":True}),(502,{"detail":"private provider payload"}),
                                      (422,{"detail":"private validation value"})])
def test_http_client_rejects_malformed_or_unstructured_errors(status,body):
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(status,json=body))) as transport:
        with pytest.raises(APIClientError) as error:
            ResearchAPIClient(client=transport).ask(AskRequest(question="A valid question"))
        assert "private" not in str(error.value)


def test_ui_client_import_does_not_load_backend_or_credentials():
    code="""
import builtins, os, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(('openai','torch','sentence_transformers','app.service','src.retrieval','src.generation.client','src.generation.generator')):
        raise AssertionError(name)
    return original(name,*args,**kwargs)
builtins.__import__=guarded
os.environ.pop('OPENAI_API_KEY',None)
from app.client import ResearchAPIClient
assert 'openai' not in sys.modules
"""
    subprocess.run([sys.executable,"-c",code],check=True)


@pytest.mark.parametrize("url",["localhost:8000","http://localhost:bad","http://[invalid",
                                 "http://user:private@localhost:8000"])
def test_bad_api_url_is_a_safe_configuration_error(url):
    with pytest.raises(APIClientError) as error:
        ResearchAPIClient(url)
    assert "private" not in str(error.value)


def test_real_local_http_roundtrip_without_inference(tmp_path):
    import uvicorn
    sdk=Mock()
    sdk.responses.create.return_value=success(output_text=json.dumps(Client().result))
    service,*_=configured_service(tmp_path,sdk)
    sock=socket.socket();sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(create_app(service),log_level="critical"))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    try:
        for _ in range(100):
            if server.started: break
            time.sleep(.02)
        assert server.started
        with httpx.Client(timeout=5) as transport:
            client=ResearchAPIClient(f"http://127.0.0.1:{port}",client=transport)
            assert client.health().status=="ok" and len(client.papers())==8
            answer=client.ask(AskRequest(question="How does SelfCheckGPT work?"))
            assert answer.citations[0].quote=="compares stochastic samples"
            assert client.record_feedback(FeedbackRequest(submission_id="tcp-feedback",rating="up")).stored
    finally:
        server.should_exit=True;thread.join(timeout=5);sock.close()
    assert not thread.is_alive()
    assert sdk.responses.create.call_count==1
