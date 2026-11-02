"""FastAPI wrapper around the existing ResearchLens generation service."""
from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (AskRequest, FeedbackRequest, FeedbackResponse,
                         HealthResponse, PaperSummary)
from app.service import InvalidPaperScope, ResearchService
from src.generation.schemas import ErrorInfo, GenerationResponse

ERROR_STATUS = {
    "invalid_input": 422, "retrieval_unavailable": 503, "missing_api_key": 503,
    "service_unavailable": 503, "service_busy": 503, "openai_api_error": 502,
    "openai_timeout": 504, "invalid_model_output": 502, "incomplete_generation": 502,
    "attempt_limit": 502,
}


def _cors_origins() -> list[str]:
    configured = os.environ.get(
        "RESEARCHLENS_CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def create_app(service: ResearchService | None = None) -> FastAPI:
    service = service or ResearchService()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        service.warmup()
        try:
            yield
        finally:
            service.close()

    app = FastAPI(
        title="ResearchLens API",
        version="0.1.0",
        description="Citation-grounded question answering over the ResearchLens corpus.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health(response: Response) -> HealthResponse:
        result = service.health()
        response.status_code = 200 if result.status == "ok" else 503
        return result

    @app.get("/papers", response_model=list[PaperSummary])
    def papers() -> list[PaperSummary]:
        try:
            return service.papers()
        except (OSError, ValueError, KeyError):
            raise HTTPException(status_code=503, detail="The paper catalog is unavailable.") from None

    @app.post("/ask", response_model=GenerationResponse)
    def ask(request: AskRequest, response: Response) -> GenerationResponse:
        try:
            result = service.ask(request)
        except InvalidPaperScope as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        except Exception:
            # Do not leak provider bodies, prompts, evidence, or credentials.
            result = GenerationResponse(question=request.question, status="error",
                error=ErrorInfo(code="service_unavailable", message="Research service is unavailable."))
        if result.status == "error":
            response.status_code = ERROR_STATUS.get(result.error.code if result.error else "", 500)
        return result

    @app.post("/feedback", response_model=FeedbackResponse)
    def feedback(request: FeedbackRequest) -> FeedbackResponse:
        try:
            service.record_feedback(request)
        except (OSError, ValueError):
            raise HTTPException(status_code=503, detail="Feedback storage is unavailable.") from None
        return FeedbackResponse(stored=True)

    return app


app = create_app()
