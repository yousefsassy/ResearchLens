"""Serial, dependency-injected orchestration. Phase 2 imports stay lazy."""
import time

from pydantic import ValidationError

from .citations import validate_and_render
from .client import GenerationFailure, OpenRouterClient
from .config import GenerationConfig
from .evidence import select_evidence
from .papers import interpret, load_catalog
from .prompts import build_messages
from .schemas import ErrorInfo, GenerationResponse


class ResearchGenerator:
    def __init__(self, retriever=None, client=None, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig.from_env()
        self.retriever = retriever
        self.client = client or OpenRouterClient(self.config)
        self.catalog = load_catalog(self.config.catalog_path)

    def close(self):
        if hasattr(self.client, "close"):
            self.client.close()

    def _get_retriever(self):
        if self.retriever is None:
            from src.retrieval import ResearchRetriever
            self.retriever = ResearchRetriever()
        return self.retriever

    def answer(self, question: str, paper_ids=None, answer_type: str = "auto") -> GenerationResponse:
        started = time.perf_counter()
        response = GenerationResponse(question=question if isinstance(question, str) else "", status="error")
        try:
            interpreted = interpret(question, paper_ids, answer_type, self.catalog)
        except ValueError as error:
            response.error = ErrorInfo(code="invalid_input", message=str(error))
            response.metrics.total_seconds = time.perf_counter() - started
            return response
        response.answer_type = interpreted.answer_type
        response.paper_ids = interpreted.paper_ids
        response.metrics.interpretation_seconds = time.perf_counter() - started
        if interpreted.clarification:
            response.status = "needs_clarification"
            response.clarification = interpreted.clarification
            response.metrics.total_seconds = time.perf_counter() - started
            return response
        stage = time.perf_counter()
        try:
            selection = select_evidence(self._get_retriever(), question, interpreted,
                                        self.catalog, self.config.context_chars)
            response.evidence = selection.passages
            response.limitations = selection.gaps
        except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError):
            response.error = ErrorInfo(code="retrieval_unavailable", message=(
                "Retrieval is unavailable or returned invalid evidence. Check local dependencies, "
                "the agreed chunks, matching index, BGE cache, and catalog."))
        response.metrics.retrieval_seconds = time.perf_counter() - stage
        if response.error:
            response.metrics.total_seconds = time.perf_counter() - started
            return response
        if not response.evidence:
            response.status, response.abstained = "abstained", True
            response.answer = "I don't have sufficient usable evidence to answer this question."
            response.limitations.append("No usable unflagged passages were selected.")
            response.metrics.total_seconds = time.perf_counter() - started
            return response
        stage = time.perf_counter()
        timings = response.metrics
        try:
            output, metrics = self.client.complete(build_messages(question, interpreted, response.evidence, selection.gaps))
            response.metrics = metrics.model_copy()
            # Injected clients must follow the same untrusted-output contract.
            from .schemas import ModelAnswer
            output = ModelAnswer.model_validate(output)
        except GenerationFailure as error:
            response.error = error.error
            response.metrics = error.metrics.model_copy()
            output = None
        except (ValidationError, ValueError, TypeError):
            response.error = ErrorInfo(code="invalid_model_output", message="Model returned an invalid answer contract.")
            output = None
        response.metrics.interpretation_seconds = timings.interpretation_seconds
        response.metrics.retrieval_seconds = timings.retrieval_seconds
        response.metrics.generation_seconds = time.perf_counter() - stage
        if output is not None:
            stage = time.perf_counter()
            try:
                answer, citations = validate_and_render(output, response.evidence, response.answer_type, response.paper_ids)
                response.status = output.status
                response.answer, response.citations, response.claims = answer, citations, output.claims
                response.abstained = output.status == "abstained"
                response.limitations = list(dict.fromkeys([*response.limitations, *output.limitations]))
                # Hard retrieval gaps override an optimistic model completion label.
                if response.status == "complete" and selection.gaps:
                    response.status = "partial"
                if response.status == "complete" and response.answer_type == "comparison":
                    cited_papers = {c.paper_id for c in citations}
                    missing = set(response.paper_ids) - cited_papers
                    if missing:
                        response.status = "partial"
                        response.limitations.append("No cited answer claims for: " + ", ".join(sorted(missing)))
            except ValueError:
                response.error = ErrorInfo(code="invalid_model_output", message="Citation references or supporting quotes failed validation.")
            response.metrics.validation_seconds = time.perf_counter() - stage
        response.metrics.total_seconds = time.perf_counter() - started
        return response
