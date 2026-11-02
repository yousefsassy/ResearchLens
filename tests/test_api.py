import json

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.feedback import FeedbackStore
from app.schemas import FeedbackRequest
from app.service import ResearchService
from src.generation.schemas import GenerationResponse


class FakeRetriever:
    chunks = [{"chunk_id": "x"}] * 3

    def status(self):
        return {"index": {"valid": True}}


class FakeGenerator:
    def __init__(self):
        self.calls = []
        self.retriever = FakeRetriever()
        self.config = type("Config", (), {"model": "fake-model"})()
        self.closed = False

    def answer(self, question, paper_ids=None, answer_type="auto", **filters):
        self.calls.append((question, paper_ids, answer_type, filters))
        return GenerationResponse(
            question=question,
            status="complete",
            answer="Grounded answer [C1]",
            paper_ids=paper_ids or [],
            metrics={"model": "fake-model", "request_id": "req-1"},
        )

    def close(self):
        self.closed = True


@pytest.fixture
def fake():
    return FakeGenerator()


@pytest.fixture
def client(fake, tmp_path):
    service = ResearchService(
        generator_factory=lambda: fake,
        feedback_store=FeedbackStore(tmp_path / "feedback.jsonl"),
    )
    with TestClient(create_app(service)) as api:
        yield api, service, fake


def test_health_and_papers(client):
    api, _, _ = client
    health = api.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["chunks"] == 3
    assert health.json()["index_valid"] is True

    papers = api.get("/papers")
    assert papers.status_code == 200
    body = papers.json()
    assert len(body) == 8
    assert {paper["paper_id"] for paper in body} >= {"P006", "P007", "P008"}


def test_ask_forwards_question_scope_and_filters(client):
    api, _, fake = client
    response = api.post("/ask", json={
        "question": "What are the four steps of Chain-of-Verification?",
        "paper_ids": ["P008"],
        "answer_type": "qa",
        "year": 2023,
        "author": "Dhuliawala",
        "section": "CHAIN-OF-VERIFICATION",
    })

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert fake.calls == [(
        "What are the four steps of Chain-of-Verification?",
        ["P008"],
        "qa",
        {"year": 2023, "author": "Dhuliawala", "section": "CHAIN-OF-VERIFICATION"},
    )]


def test_invalid_requests_are_rejected(client):
    api, _, _ = client
    assert api.post("/ask", json={"question": "x"}).status_code == 422
    assert api.post("/ask", json={
        "question": "Compare one paper",
        "paper_ids": ["P002"],
        "answer_type": "comparison",
    }).status_code == 422
    assert api.post("/ask", json={
        "question": "Compare three papers",
        "paper_ids": ["P001", "P002", "P003"],
    }).status_code == 422
    assert api.post("/ask", json={
        "question": "Question",
        "year": 0,
    }).status_code == 422


def test_feedback_is_persisted_without_question_text(client, tmp_path):
    api, service, _ = client
    response = api.post("/feedback", json={
        "rating": "up",
        "request_id": "req-1",
        "status": "complete",
        "comment": "Clear citation.",
    })
    assert response.status_code == 200
    assert response.json() == {"stored": True}
    records = [json.loads(line) for line in service.feedback.path.read_text(encoding="utf-8").splitlines()]
    assert records[0]["rating"] == "up"
    assert records[0]["request_id"] == "req-1"
    assert "question" not in records[0]


def test_service_returns_safe_error_when_generator_fails(tmp_path):
    class Broken:
        def answer(self, *args, **kwargs):
            raise RuntimeError("private provider body")

        def close(self):
            pass

    service = ResearchService(
        generator_factory=lambda: Broken(),
        feedback_store=FeedbackStore(tmp_path / "feedback.jsonl"),
    )
    api = TestClient(create_app(service))
    response = api.post("/ask", json={"question": "A valid question"})
    assert response.status_code == 503
    assert "private provider body" not in response.text
