"""Versioned public responses and the smaller, untrusted model-output contract."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class SourceQuote(StrictModel):
    source_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class Claim(StrictModel):
    text: str = Field(min_length=1)
    kind: Literal["reported", "synthesis"]
    citations: list[SourceQuote] = Field(min_length=1)


class ModelAnswer(StrictModel):
    status: Literal["complete", "partial", "abstained"]
    claims: list[Claim]
    limitations: list[str]

    @model_validator(mode="after")
    def consistent_status(self):
        if self.status == "abstained" and self.claims:
            raise ValueError("abstention must not contain factual claims")
        if self.status != "abstained" and not self.claims:
            raise ValueError("an answer requires cited claims")
        if self.status in {"partial", "abstained"} and not any(x.strip() for x in self.limitations):
            raise ValueError("partial answers and abstentions require a reason")
        return self


class Evidence(StrictModel):
    source_id: str
    chunk_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    pdf_filename: str = Field(min_length=1)
    title: str | None = None
    pdf_page: int = Field(ge=1)
    text: str = Field(min_length=1)
    needs_review: bool
    review_flags: list[str]
    retrieval_score: float | None = None
    rerank_score: float | None = None
    bm25_score: float | None = None
    vector_score: float | None = None
    rrf_score: float | None = None
    rank: int | None = None


class Citation(StrictModel):
    citation_id: str
    claim_index: int = Field(ge=1)
    source_id: str
    quote: str
    chunk_id: str
    paper_id: str
    pdf_filename: str
    title: str | None
    pdf_page: int


class ErrorInfo(StrictModel):
    code: str
    message: str
    retryable: bool = False


class Clarification(StrictModel):
    question: str
    candidate_paper_ids: list[str]


class Metrics(StrictModel):
    interpretation_seconds: float = 0.0
    retrieval_seconds: float = 0.0
    generation_seconds: float = 0.0
    validation_seconds: float = 0.0
    total_seconds: float = 0.0
    model: str | None = None
    provider: str | None = None
    request_id: str | None = None
    attempts: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    cost_usd: float | None = None
    accounting_complete: bool = True


class GenerationResponse(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    question: str
    answer_type: Literal["qa", "comparison"] = "qa"
    status: Literal["complete", "partial", "abstained", "needs_clarification", "error"]
    answer: str = ""
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    paper_ids: list[str] = Field(default_factory=list)
    abstained: bool = False
    limitations: list[str] = Field(default_factory=list)
    clarification: Clarification | None = None
    error: ErrorInfo | None = None
    metrics: Metrics = Field(default_factory=Metrics)
