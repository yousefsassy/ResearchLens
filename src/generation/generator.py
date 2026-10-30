"""Serial, dependency-injected orchestration. Phase 2 imports stay lazy."""
import ast
import json
import re
import sys
import time

from pydantic import ValidationError

from .citations import validate_and_render
from .client import GenerationFailure, OpenAIClient
from .config import GenerationConfig
from .evidence import select_evidence
from .papers import interpret, load_catalog
from .prompts import build_messages, build_repair_messages
from .schemas import ErrorInfo, GenerationResponse, ModelAnswer
from src.profiling import measure, record_usage, record_validation_failure


class ResearchGenerator:
    def __init__(self, retriever=None, client=None, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig.from_env()
        self.retriever = retriever
        self.client = client or OpenAIClient(self.config)
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
            response.error = ErrorInfo(
                code="retrieval_unavailable",
                message=(
                    "Retrieval is unavailable or returned invalid evidence. "
                    "Check local dependencies, the agreed chunks, matching index, "
                    "BGE cache, and catalog."
                )
            )
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
        messages = build_messages(question, interpreted, response.evidence, selection.gaps)
        repair_validation = "not_run"
        for attempt in range(2):
            stage = time.perf_counter()
            try:
                # Existing injected clients need only implement complete(messages).
                complete = (getattr(self.client, "complete_repair", self.client.complete)
                            if attempt else self.client.complete)
                with measure("citation_repair_request" if attempt else "initial_generation_request"):
                    output, metrics = complete(messages)
                record_usage("citation_repair_request" if attempt else "initial_generation_request", metrics)
                self._merge_metrics(response.metrics, metrics)
            except GenerationFailure as error:
                record_usage("citation_repair_request" if attempt else "initial_generation_request", error.metrics)
                self._merge_metrics(response.metrics, error.metrics)
                response.error = error.error
                break
            except (ValidationError, ValueError, TypeError):
                response.error = ErrorInfo(code="invalid_model_output", message="Model returned an invalid answer contract.")
                break
            finally:
                response.metrics.generation_seconds += time.perf_counter() - stage

            stage = time.perf_counter()
            try:
                # Injected clients must follow the same untrusted-output contract.
                output = ModelAnswer.model_validate(output)
            except (ValidationError, ValueError, TypeError):
                response.error = ErrorInfo(code="invalid_model_output", message="Model returned an invalid answer contract.")
                response.metrics.validation_seconds += time.perf_counter() - stage
                break
            validation_error = None
            try:
                answer, citations = validate_and_render(output, response.evidence, response.answer_type, response.paper_ids)
                if attempt:
                    repair_validation = "passed"
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
            except ValueError as error:
                validation_error = str(error)
                if attempt:
                    repair_validation = "failed"
            finally:
                response.metrics.validation_seconds += time.perf_counter() - stage
            if validation_error is not None:
                record_validation_failure(attempt, validation_error)
                self._citation_diagnostic(attempt, validation_error)
                if attempt == 0:
                    messages = build_repair_messages(
                        question, interpreted, response.evidence, selection.gaps,
                        output, validation_error,
                    )
                    continue
                response.error = ErrorInfo(
                    code="invalid_model_output",
                    message="Citation references or supporting quotes failed validation."
                )
            break
        if attempt == 1 and self.config.debug_citations:
            # Do not log provider exceptions, schema payloads, prompts, or evidence.
            print("[citation-debug] " + json.dumps({
                "repair_attempted": True,
                "repair_validation": repair_validation,
            }), file=sys.stderr)
        response.metrics.total_seconds = time.perf_counter() - started
        return response

    def _citation_diagnostic(self, attempt, error):
        """Display only validator diagnostics; JSON escapes untrusted text."""
        if not self.config.debug_citations:
            return
        claim = re.match(r"Claim (\d+)", error)
        source = re.match(r"Claim \d+, source ([^:]+):", error)
        unknown = re.match(r"Claim \d+: unknown source ID (.+)$", error)
        source_id = source.group(1) if source else None
        if unknown:
            # The validator formats unknown IDs with repr(), not executable code.
            try:
                source_id = ast.literal_eval(unknown.group(1))
            except (SyntaxError, ValueError):
                pass
        print("[citation-debug] " + json.dumps({
            "attempt": "citation-repair" if attempt else "initial generation",
            "validation": "failed",
            "validation_error": error,
            "claim_index": int(claim.group(1)) if claim else None,
            "source_id": source_id,
            "repair_attempted": bool(attempt),
            "repair_validation": "failed" if attempt else "pending",
        }), file=sys.stderr)

    @staticmethod
    def _merge_metrics(total, current):
        """Accumulate request accounting without overwriting orchestration timers."""
        first = total.attempts == 0
        for field in ("prompt_tokens", "completion_tokens", "reasoning_tokens", "cost_usd"):
            previous, value = getattr(total, field), getattr(current, field)
            if first:
                setattr(total, field, value)
            elif current.attempts:
                # Unknown usage must not be represented as a known total.
                setattr(total, field, previous + value if previous is not None and value is not None else None)
        total.attempts += current.attempts
        total.accounting_complete &= current.accounting_complete
        for field in ("model", "provider", "request_id"):
            if getattr(current, field) is not None:
                setattr(total, field, getattr(current, field))
