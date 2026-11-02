"""FastAPI wrapper around the existing ResearchLens generation service."""
from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (AskRequest, FeedbackRequest, FeedbackResponse,
                         HealthResponse, PaperSummary)
from app.service import ResearchService
from src.generation.schemas import GenerationResponse


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
        # Warm-up is best effort: /papers and /health should still work when
        # the API key or model cache is not available yet.
        try:
            service.warmup()
        except Exception:
            pass
        yield
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
    def health() -> HealthResponse:
        return service.health()

    @app.get("/papers", response_model=list[PaperSummary])
    def papers() -> list[PaperSummary]:
        return service.papers()

    @app.post("/ask", response_model=GenerationResponse)
    def ask(request: AskRequest) -> GenerationResponse:
        try:
            return service.ask(request)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        except Exception:
            # Do not leak provider bodies, prompts, evidence, or credentials.
            raise HTTPException(
                status_code=503,
                detail="Research service is unavailable. Check the server logs.",
            ) from None

    @app.post("/feedback", response_model=FeedbackResponse)
    def feedback(request: FeedbackRequest) -> FeedbackResponse:
        try:
            service.record_feedback(request)
        except OSError:
            raise HTTPException(status_code=503, detail="Feedback storage is unavailable.") from None
        return FeedbackResponse(stored=True)

    return app


app = create_app()
