"""Explicit configuration; importing this module never reads secrets or .env."""
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import Field, model_validator

from .schemas import StrictModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GenerationConfig(StrictModel):
    model: str = Field(default="qwen3:8b", min_length=1)
    ollama_base_url: str = "http://127.0.0.1:11434"
    catalog_path: Path = PROJECT_ROOT / "data/papers_generation.json"
    max_tokens: int = Field(default=2048, ge=1)
    context_chars: int = Field(default=12000, ge=1)
    connect_timeout: float = Field(default=5.0, gt=0)
    request_timeout: float = Field(default=180.0, gt=0)
    num_ctx: int = Field(default=8192, ge=1024)
    max_attempts: int = Field(default=1, ge=1, le=2)
    # Shared across questions by the client, including failed inference attempts.
    attempt_limit: int = Field(default=25, ge=1, le=25)

    @model_validator(mode="after")
    def local_endpoint(self):
        url = urlsplit(self.ollama_base_url)
        if (url.scheme not in {"http", "https"} or url.hostname not in {"localhost", "127.0.0.1", "::1"}
                or url.username is not None or url.password is not None
                or url.path not in {"", "/"} or url.query or url.fragment):
            raise ValueError("ollama_base_url must be a loopback HTTP endpoint without credentials or a path")
        _ = url.port
        if self.max_tokens >= self.num_ctx:
            raise ValueError("max_tokens must be smaller than num_ctx to leave room for evidence")
        return self

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        values = {**dotenv_values(env_file or PROJECT_ROOT / ".env"), **os.environ}
        return cls(
            model=values.get("OLLAMA_MODEL") or cls.model_fields["model"].default,
            ollama_base_url=values.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434",
            max_tokens=int(values.get("RESEARCHLENS_MAX_TOKENS") or 2048),
            context_chars=int(values.get("RESEARCHLENS_CONTEXT_CHARS") or 12000),
            num_ctx=int(values.get("OLLAMA_NUM_CTX") or 8192),
            request_timeout=float(values.get("OLLAMA_TIMEOUT_SECONDS") or 180),
        )
