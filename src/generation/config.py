"""Explicit configuration; importing this module never reads secrets or .env."""
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field, SecretStr

from .schemas import StrictModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GenerationConfig(StrictModel):
    api_key: SecretStr = Field(default_factory=lambda: SecretStr(""), repr=False, exclude=True)
    model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    catalog_path: Path = PROJECT_ROOT / "data/papers_generation.json"
    max_tokens: int = Field(default=4096, ge=1)
    context_chars: int = Field(default=24000, ge=1)
    connect_timeout: float = Field(default=5.0, gt=0)
    request_timeout: float = Field(default=60.0, gt=0)
    max_attempts: int = Field(default=2, ge=1, le=2)
    # Shared across questions by the client, including failed inference attempts.
    attempt_limit: int = Field(default=25, ge=1, le=25)

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        values = {**dotenv_values(env_file or PROJECT_ROOT / ".env"), **os.environ}
        return cls(
            api_key=SecretStr(values.get("OPENROUTER_API_KEY") or ""),
            model=values.get("OPENROUTER_MODEL") or cls.model_fields["model"].default,
            max_tokens=int(values.get("RESEARCHLENS_MAX_TOKENS") or 4096),
            context_chars=int(values.get("RESEARCHLENS_CONTEXT_CHARS") or 24000),
        )
