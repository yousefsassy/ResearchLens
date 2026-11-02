"""Application service shared by FastAPI and Streamlit.

The RAG implementation stays in `src/`; this module only handles lazy startup,
serial access, metadata display, health reporting, and feedback.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.feedback import FeedbackStore
from app.schemas import AskRequest, FeedbackRequest, HealthResponse, PaperSummary
from src.generation import GenerationConfig, ResearchGenerator
from src.generation.schemas import GenerationResponse


class ResearchService:
    def __init__(self, generator_factory: Callable[[], ResearchGenerator] | None = None,
                 feedback_store: FeedbackStore | None = None):
        self._generator_factory = generator_factory or self._default_generator
        self._generator: ResearchGenerator | None = None
        self._lock = threading.Lock()
        self._papers: list[PaperSummary] | None = None
        self.feedback = feedback_store or FeedbackStore()

    @staticmethod
    def _default_generator() -> ResearchGenerator:
        from src.retrieval import ResearchRetriever
        return ResearchGenerator(
            retriever=ResearchRetriever(),
            config=GenerationConfig.from_env(),
        )

    def generator(self) -> ResearchGenerator:
        if self._generator is None:
            self._generator = self._generator_factory()
        return self._generator

    def warmup(self) -> HealthResponse:
        """Load the retriever and embedding model without spending API tokens."""
        generator = self.generator()
        retriever = getattr(generator, "retriever", None)
        encoder = getattr(retriever, "encoder", None)
        if encoder is not None and hasattr(encoder, "encode_query"):
            encoder.encode_query("ResearchLens warm-up query")
        return self.health()

    def ask(self, request: AskRequest) -> GenerationResponse:
        # The retriever and generator are documented as serial, so one lock
        # protects both the FastAPI threadpool and Streamlit sessions.
        with self._lock:
            return self.generator().answer(
                request.question,
                request.paper_ids,
                request.answer_type,
                year=request.year,
                author=request.author,
                section=request.section,
            )

    def papers(self) -> list[PaperSummary]:
        if self._papers is None:
            from src.generation.papers import load_catalog
            from src.ingestion.metadata import load_paper_metadata

            manifest = load_paper_metadata()
            catalog = load_catalog(GenerationConfig().catalog_path)
            papers = []
            for paper_id, metadata in manifest.items():
                paper = catalog.get(paper_id)
                papers.append(PaperSummary(
                    paper_id=paper_id,
                    title=metadata["title"],
                    authors=metadata["authors"],
                    year=metadata["year"],
                    category=metadata["category"],
                    pdf_filename=metadata["pdf_filename"],
                    aliases=paper.aliases if paper is not None else [],
                ))
            self._papers = papers
        return self._papers

    def record_feedback(self, feedback: FeedbackRequest) -> None:
        self.feedback.add(feedback)

    def health(self) -> HealthResponse:
        generator = self._generator
        retriever = getattr(generator, "retriever", None)
        index_valid = None
        chunks = None
        if retriever is not None:
            chunks = len(getattr(retriever, "chunks", [])) or None
            try:
                index_valid = bool(retriever.status()["index"]["valid"])
            except (AttributeError, KeyError, OSError, TypeError, ValueError):
                index_valid = False
        model = None
        if generator is not None:
            model = getattr(getattr(generator, "config", None), "model", None)
        return HealthResponse(
            status="ok" if generator is not None else "degraded",
            chunks=chunks,
            index_valid=index_valid,
            generator_loaded=generator is not None,
            retriever_loaded=retriever is not None,
            model=model,
        )

    def close(self) -> None:
        if self._generator is not None:
            self._generator.close()
