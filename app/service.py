"""Backend-owned resources and bounded, serial access to the existing RAG pipeline."""
from __future__ import annotations

import threading
from typing import Callable

from app.feedback import FeedbackStore
from app.schemas import AskRequest, FeedbackRequest, HealthResponse, PaperSummary
from src.generation import GenerationConfig, ResearchGenerator
from src.generation.client import OpenAIClient
from src.generation.schemas import ErrorInfo, GenerationResponse


class InvalidPaperScope(ValueError):
    """An explicit paper ID is absent from the trusted catalog."""


class ResearchService:
    def __init__(self, generator_factory: Callable | None = None,
                 feedback_store: FeedbackStore | None = None, *,
                 retriever_factory: Callable | None = None,
                 client_factory: Callable | None = None,
                 config: GenerationConfig | None = None, acquire_timeout: float = 1.0):
        self._generator_factory = generator_factory
        self._retriever_factory = retriever_factory
        self._client_factory = client_factory or OpenAIClient
        self._config = config or GenerationConfig.from_env()
        self._request_config = self._config.model_copy(update={"attempt_limit": 2, "max_attempts": 1})
        self._generator = self._retriever = self._owner = None
        self._initialized = self._index_ready = self._closed = False
        self._startup_error: ErrorInfo | None = None
        self._lock = threading.Lock()
        self._acquire_timeout = acquire_timeout
        self._papers: list[PaperSummary] | None = None
        self.feedback = feedback_store or FeedbackStore()

    def _initialize(self):
        """Called only under the lock; startup performs no hosted inference."""
        if self._initialized:
            return
        self._initialized = True
        try:
            self.papers()  # Catalog/manifest availability is part of readiness.
            if self._generator_factory is not None:
                self._generator = self._generator_factory()
                self._retriever = getattr(self._generator, "retriever", None)
            else:
                if self._retriever_factory is None:
                    from src.retrieval import ResearchRetriever
                    self._retriever_factory = ResearchRetriever
                self._retriever = self._retriever_factory()
            if self._retriever is None:
                raise RuntimeError("Retriever unavailable")
            if hasattr(type(self._retriever), "vector"):
                _ = self._retriever.vector
                _ = self._retriever.bm25
                self._index_ready = True
            else:
                self._index_ready = bool(self._retriever.status()["index"]["valid"])
            if not self._index_ready:
                raise RuntimeError("Index unavailable")
            encoder = getattr(self._retriever, "encoder", None)
            if encoder is not None:
                encoder.encode_query("ResearchLens warm-up query")
        except Exception:
            self._startup_error = ErrorInfo(code="retrieval_unavailable",
                message="Retrieval is unavailable. Restore the matching corpus, index, catalog and BGE cache.")
            return
        if self._generator_factory is None:
            try:
                self._owner = self._client_factory(self._config)
                if self._owner.client is None:
                    self._startup_error = ErrorInfo(code="missing_api_key",
                        message="Configure OPENAI_API_KEY on the FastAPI server.")
            except Exception:
                self._startup_error = ErrorInfo(code="service_unavailable",
                    message="Generation could not be initialized. Check the server configuration.")

    def warmup(self) -> HealthResponse:
        with self._lock:
            self._initialize()
        return self.health()

    @staticmethod
    def _error(question, code, message, retryable=False):
        return GenerationResponse(question=question, status="error",
            error=ErrorInfo(code=code, message=message, retryable=retryable))

    def ask(self, request: AskRequest) -> GenerationResponse:
        try:
            known = {paper.paper_id for paper in self.papers()}
        except (OSError, ValueError, KeyError):
            return self._error(request.question, "service_unavailable", "The paper catalog is unavailable.")
        if request.paper_ids and not set(request.paper_ids) <= known:
            raise InvalidPaperScope("Choose paper IDs from /papers.")
        if not self._lock.acquire(timeout=self._acquire_timeout):
            return self._error(request.question, "service_busy",
                "Another question is being processed. Try again when it finishes.", True)
        try:
            if self._closed:
                return self._error(request.question, "service_unavailable", "The service is shutting down.")
            self._initialize()
            if self._startup_error is not None:
                return GenerationResponse(question=request.question, status="error", error=self._startup_error)
            if self._generator_factory is not None:
                generator = self._generator
            else:
                # Borrow the shared SDK without closing it at request completion.
                client = OpenAIClient(self._request_config, client=self._owner.client)
                generator = ResearchGenerator(retriever=self._retriever, client=client,
                                              config=self._request_config)
            return generator.answer(request.question, request.paper_ids, request.answer_type,
                year=request.year, author=request.author, section=request.section)
        finally:
            self._lock.release()

    def papers(self) -> list[PaperSummary]:
        if self._papers is None:
            from src.generation.papers import load_catalog
            from src.ingestion.metadata import load_paper_metadata
            manifest = load_paper_metadata()
            catalog = load_catalog(self._config.catalog_path)
            if set(manifest) != set(catalog):
                raise ValueError("Paper catalog and manifest IDs differ")
            self._papers = [PaperSummary(paper_id=paper_id, title=m["title"], authors=m["authors"],
                year=m["year"], category=m["category"], pdf_filename=m["pdf_filename"],
                aliases=catalog[paper_id].aliases if paper_id in catalog else [])
                for paper_id, m in manifest.items()]
        return self._papers

    def record_feedback(self, feedback: FeedbackRequest) -> None:
        self.feedback.add(feedback)

    def health(self) -> HealthResponse:
        ready = (self._initialized and self._index_ready and self._startup_error is None and not self._closed)
        return HealthResponse(status="ok" if ready else "degraded",
            chunks=len(self._retriever.chunks) if self._retriever is not None else None,
            index_valid=self._index_ready if self._initialized else None,
            generator_loaded=ready, retriever_loaded=self._retriever is not None,
            model=getattr(getattr(self._generator, "config", None), "model", self._config.model))

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._owner is not None:
                self._owner.close()
            if self._generator is not None:
                self._generator.close()
