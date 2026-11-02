import json

import numpy as np
import pytest

from src.generation import ResearchGenerator
from src.retrieval import ResearchRetriever, RetrievalConfig
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.vector_search import VectorSearch
from test_generation import Client, Retriever, passage


def retriever_for(tmp_path, rows):
    path = tmp_path / "chunks.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return ResearchRetriever(RetrievalConfig(chunks_path=path))


def test_metadata_filters_are_case_insensitive_and_composable(tmp_path):
    rows = [
        {"chunk_id": "P001-p001-c001", "paper_id": "P001", "pdf_filename": "p1.pdf",
         "pdf_page": 1, "text": "SelfCheckGPT compares stochastic samples.",
         "needs_review": False, "review_flags": [], "year": 2023,
         "authors": "Potsawee Manakul; Adian Liusie", "section": "Methods"},
        {"chunk_id": "P001-p002-c001", "paper_id": "P001", "pdf_filename": "p1.pdf",
         "pdf_page": 2, "text": "SelfCheckGPT has limitations.",
         "needs_review": False, "review_flags": [], "year": 2022,
         "authors": "Another Author", "section": "Limitations"},
        {"chunk_id": "P002-p001-c001", "paper_id": "P002", "pdf_filename": "p2.pdf",
         "pdf_page": 1, "text": "FActScore measures atomic facts.",
         "needs_review": False, "review_flags": [], "year": 2023,
         "authors": "Sewon Min", "section": "Methods"},
    ]
    retriever = retriever_for(tmp_path, rows)

    assert [r["chunk_id"] for r in retriever.search(
        "SelfCheckGPT", mode="bm25", rerank=False, year=2023)] == ["P001-p001-c001"]
    assert [r["chunk_id"] for r in retriever.search(
        "SelfCheckGPT", mode="bm25", rerank=False, author="manakul")] == ["P001-p001-c001"]
    assert [r["chunk_id"] for r in retriever.search(
        "SelfCheckGPT", mode="bm25", rerank=False, section="methods")] == ["P001-p001-c001"]
    assert [r["chunk_id"] for r in retriever.search(
        "SelfCheckGPT", mode="bm25", rerank=False, year=2023,
        author="manakul", section="Methods")] == ["P001-p001-c001"]
    assert retriever.search(
        "SelfCheckGPT", mode="bm25", rerank=False, section="Discussion") == []


def test_hybrid_and_vector_backends_apply_metadata_filters():
    class Backend:
        def __init__(self):
            self.calls = []

        def search(self, question, count, **filters):
            self.calls.append(filters)
            return []

    bm25, vector = Backend(), Backend()
    assert HybridSearch(bm25, vector, RetrievalConfig()).search(
        "q", year=2023, author="Manakul", section="Methods") == []
    assert bm25.calls[0]["year"] == 2023
    assert vector.calls[0]["author"] == "Manakul"
    assert vector.calls[0]["section"] == "Methods"

    rows = [
        {"chunk_id": "P001-p001-c001", "paper_id": "P001", "pdf_filename": "p1.pdf",
         "pdf_page": 1, "text": "Methods text.", "needs_review": False,
         "review_flags": [], "year": 2023, "authors": "Manakul", "section": "Methods"},
        {"chunk_id": "P001-p002-c001", "paper_id": "P001", "pdf_filename": "p1.pdf",
         "pdf_page": 2, "text": "Limitations text.", "needs_review": False,
         "review_flags": [], "year": 2022, "authors": "Other", "section": "Limitations"},
    ]

    class Encoder:
        def encode_query(self, question):
            return np.array([1.0, 0.0], dtype=np.float32)

    search = VectorSearch(rows, np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32), Encoder())
    assert [row["chunk_id"] for row in search.search("q", section="Methods")] == [
        "P001-p001-c001"]


def test_invalid_metadata_filters_fail_closed(tmp_path):
    retriever = retriever_for(tmp_path, [{
        "chunk_id": "P001-p001-c001", "paper_id": "P001",
        "pdf_filename": "p1.pdf", "pdf_page": 1, "text": "A passage.",
        "needs_review": False, "review_flags": [],
    }])

    with pytest.raises(ValueError, match="year"):
        retriever.search("q", mode="bm25", rerank=False, year="2023")
    with pytest.raises(ValueError, match="author"):
        retriever.search("q", mode="bm25", rerank=False, author=" ")


def test_generator_forwards_metadata_filters_to_evidence_selection():
    backend = Retriever([passage(authors="Potsawee Manakul", year=2023,
                                 section="Methods")])
    result = ResearchGenerator(backend, Client()).answer(
        "How does SelfCheckGPT detect hallucinations?",
        year=2023, author="Manakul", section="Methods")

    assert result.status == "complete"
    assert backend.calls[0]["year"] == 2023
    assert backend.calls[0]["author"] == "Manakul"
    assert backend.calls[0]["section"] == "Methods"
    assert result.evidence[0].year == 2023
    assert result.evidence[0].section == "Methods"
    assert result.citations[0].year == 2023
    assert result.citations[0].section == "Methods"
