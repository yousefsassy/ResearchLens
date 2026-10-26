"""Local Ollama generation with installed weights and strict output validation."""
import time

import httpx
from pydantic import ValidationError

from .config import GenerationConfig
from .schemas import ErrorInfo, Metrics, ModelAnswer


class GenerationFailure(Exception):
    """Expose stable, sanitized errors rather than raw runtime responses."""

    def __init__(self, code: str, message: str, retryable: bool = False, metrics: Metrics | None = None):
        super().__init__(message)
        self.error = ErrorInfo(code=code, message=message, retryable=retryable)
        self.metrics = metrics or Metrics()


class OllamaClient:
    def __init__(self, config: GenerationConfig, *, http: httpx.Client | None = None,
                 sleep=time.sleep):
        self.config = config
        # Ignore proxy environment variables; never redirect local evidence remotely.
        self.http = http or httpx.Client(
            timeout=httpx.Timeout(config.request_timeout, connect=config.connect_timeout),
            trust_env=False, follow_redirects=False)
        self._owns_http = http is None
        self.sleep = sleep
        self.attempts_used = 0
        self.base_url = config.ollama_base_url.rstrip("/")

    def close(self):
        if self._owns_http:
            self.http.close()

    def _verify_model(self, metrics: Metrics):
        try:
            response = self.http.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json()["models"]
            row = next((m for m in models if m.get("name") == self.config.model
                        or m.get("model") == self.config.model), None)
            if row is None:
                raise GenerationFailure("model_not_installed",
                    "The configured model is not installed in local Ollama. Select an existing model with OLLAMA_MODEL.", metrics=metrics)
            if row.get("remote_host") or row.get("remote_model") or row.get("details", {}).get("format") != "gguf":
                raise GenerationFailure("local_model_required",
                    "Generation requires installed local GGUF weights; cloud-backed models are not permitted.", metrics=metrics)
        except GenerationFailure:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
            raise GenerationFailure("ollama_unavailable",
                "Cannot reach or inspect local Ollama. Start Ollama and check OLLAMA_BASE_URL.", True, metrics) from None

    def complete(self, messages: list[dict]) -> tuple[ModelAnswer, Metrics]:
        metrics = Metrics(model=self.config.model, provider="ollama", cost_usd=0.0)
        if self.attempts_used >= self.config.attempt_limit:
            raise GenerationFailure("attempt_limit", "The shared inference-attempt limit has been reached.", metrics=metrics)
        self._verify_model(metrics)
        body = {
            "model": self.config.model, "messages": messages, "stream": False,
            "think": False, "format": ModelAnswer.model_json_schema(),
            "options": {"num_predict": self.config.max_tokens, "num_ctx": self.config.num_ctx, "temperature": 0},
            "keep_alive": "5m",
        }
        for attempt in range(self.config.max_attempts):
            if self.attempts_used >= self.config.attempt_limit:
                raise GenerationFailure("attempt_limit", "The shared inference-attempt limit has been reached.", metrics=metrics)
            self.attempts_used += 1
            metrics.attempts += 1
            try:
                response = self.http.post(f"{self.base_url}/api/chat", json=body)
            except httpx.TimeoutException:
                metrics.accounting_complete = False
                raise GenerationFailure("request_timeout",
                    "Local generation timed out. Model loading and CPU inference can be slow; increase OLLAMA_TIMEOUT_SECONDS if needed.",
                    True, metrics) from None
            except httpx.TransportError:
                metrics.accounting_complete = False
                raise GenerationFailure("ollama_unavailable", "Connection to local Ollama failed. Check that the service is running.", True, metrics) from None
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("expected object")
            except (ValueError, TypeError):
                payload = {}
            self._account(payload, metrics)
            if response.status_code != 200 or payload.get("error"):
                status = response.status_code
                if status in {500, 502, 503, 504} and attempt + 1 < self.config.max_attempts and self.attempts_used < self.config.attempt_limit:
                    self.sleep(1.0)
                    continue
                code = "model_not_installed" if status == 404 else "ollama_error"
                message = ("The selected model is unavailable in local Ollama. Check OLLAMA_MODEL and installed weights."
                           if status == 404 else "Local Ollama rejected generation. Check available memory and the model's runtime settings.")
                raise GenerationFailure(code, message, status >= 500, metrics)
            try:
                if payload.get("done") is not True or payload.get("done_reason") != "stop":
                    raise ValueError("incomplete generation")
                if payload.get("model") != self.config.model:
                    raise ValueError("unexpected model")
                output = ModelAnswer.model_validate_json(payload["message"]["content"])
            except (ValueError, TypeError, KeyError, ValidationError):
                raise GenerationFailure("invalid_model_output",
                    "Local model returned an incomplete or invalid structured answer. No unvalidated answer was published.", metrics=metrics) from None
            return output, metrics
        raise AssertionError("unreachable")

    @staticmethod
    def _account(payload: dict, metrics: Metrics):
        # These are native token counts, not billable API usage.
        for source, target in (("prompt_eval_count", "prompt_tokens"), ("eval_count", "completion_tokens")):
            value = payload.get(source)
            if type(value) is int and value >= 0:
                setattr(metrics, target, (getattr(metrics, target) or 0) + value)
            else:
                metrics.accounting_complete = False
        message = payload.get("message")
        if isinstance(message, dict) and not message.get("thinking"):
            metrics.reasoning_tokens = 0
