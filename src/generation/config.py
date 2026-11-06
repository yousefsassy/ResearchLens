
"""Configuration for ResearchLens generation using OpenAI."""
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field

from .schemas import StrictModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GenerationConfig(StrictModel):
    model: str = Field(default="gpt-5.4-nano", min_length=1)
    catalog_path: Path = PROJECT_ROOT / "data/papers_generation.json"

    max_tokens: int = Field(default=2048, ge=1)
    context_chars: int = Field(default=12000, ge=1)
    request_timeout: float = Field(default=180.0, gt=0)
    max_attempts: int = Field(default=1, ge=1, le=2)
    attempt_limit: int = Field(default=25, ge=1, le=25)
    debug_citations: bool = Field(default=False, description="Development-only citation diagnostics on stderr.")

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        values = {
            **dotenv_values(env_file or PROJECT_ROOT / ".env"),
            **os.environ,
        }
        return cls(
            model="gpt-5.4-nano",
            max_tokens=int(2048),
            context_chars=int(12000),
            request_timeout=float(180),
            debug_citations=str(values.get("RESEARCHLENS_DEBUG_CITATIONS", "")).strip().lower()
            in {"1", "true", "yes", "on"},
        )
