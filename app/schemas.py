"""Request and response contracts for the ResearchLens web layer."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AskRequest(RequestModel):
    question: str = Field(min_length=3, max_length=1000)
    paper_ids: list[str] | None = None
    answer_type: Literal["auto", "qa", "comparison"] = "auto"
    year: int | None = Field(default=None, ge=1)
    author: str | None = Field(default=None, max_length=200)
    section: str | None = Field(default=None, max_length=200)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("question must contain at least three characters")
        return value

    @field_validator("paper_ids")
    @classmethod
    def clean_paper_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        if len(cleaned) != len(value):
            raise ValueError("paper_ids must be nonempty and unique")
        if len(cleaned) > 2:
            raise ValueError("at most two papers are supported")
        return cleaned

    @field_validator("author", "section")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def check_comparison_scope(self):
        if self.answer_type == "comparison" and self.paper_ids is not None and len(self.paper_ids) != 2:
            raise ValueError("comparison mode requires exactly two paper_ids")
        return self


class PaperSummary(RequestModel):
    paper_id: str
    title: str
    authors: str | None = None
    year: int | None = None
    category: str | None = None
    pdf_filename: str | None = None
    aliases: list[str] = Field(default_factory=list)


class HealthResponse(RequestModel):
    status: Literal["ok", "degraded"]
    chunks: int | None = None
    index_valid: bool | None = None
    generator_loaded: bool = False
    retriever_loaded: bool = False
    model: str | None = None


class FeedbackRequest(RequestModel):
    rating: Literal["up", "down"]
    request_id: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=40)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def clean_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FeedbackResponse(RequestModel):
    stored: bool
