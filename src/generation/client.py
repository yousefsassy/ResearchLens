"""Small synchronous OpenRouter transport with fail-closed free routing."""
import math
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime

import httpx
from pydantic import ValidationError

from .config import GenerationConfig
from .schemas import ErrorInfo, Metrics, ModelAnswer

BASE_URL = "https://openrouter.ai/api/v1"


class GenerationFailure(Exception):
    """Only sanitized messages are exposed; never include raw provider bodies."""

    def __init__(self, code: str, message: str, retryable: bool = False, metrics: Metrics | None = None):
        super().__init__(message)
        self.error = ErrorInfo(code=code, message=message, retryable=retryable)
        self.metrics = metrics or Metrics()


class OpenRouterClient:
    def __init__(self, config: GenerationConfig, *, http: httpx.Client | None = None,
                 sleep=time.sleep):
        self.config = config
        self.http = http or httpx.Client(
            timeout=httpx.Timeout(config.request_timeout, connect=config.connect_timeout),
            follow_redirects=False)
        self._owns_http = http is None
        self.sleep = sleep
        self.attempts_used = 0

    def close(self):
        if self._owns_http:
            self.http.close()

    def _verify_model(self, metrics: Metrics) -> set[str]:
        if not self.config.model.endswith(":free"):
            raise GenerationFailure("free_policy", "Only explicit :free model IDs are permitted.", metrics=metrics)
        try:
            response = self.http.get(f"{BASE_URL}/models")
            response.raise_for_status()
            models = response.json()["data"]
            row = next(m for m in models if m["id"] == self.config.model)
            pricing = row["pricing"]
            if any(Decimal(str(pricing[key])) != 0 for key in ("prompt", "completion")):
                raise ValueError("nonzero pricing")
            # Fail closed on other nonzero billed modalities/operations as well.
            if any(Decimal(str(value)) != 0 for value in pricing.values()):
                raise ValueError("additional priced operation")
            return set(row["supported_parameters"])
        except (httpx.HTTPError, ValueError, TypeError, KeyError, StopIteration, InvalidOperation):
            raise GenerationFailure("model_unavailable", "Cannot verify a zero-priced model in the OpenRouter catalog.",
                                    metrics=metrics) from None

    def complete(self, messages: list[dict]) -> tuple[ModelAnswer, Metrics]:
        metrics = Metrics(model=self.config.model)
        if not self.config.api_key.get_secret_value().strip():
            raise GenerationFailure("missing_api_key", "Set OPENROUTER_API_KEY in your environment or local .env.", metrics=metrics)
        if self.attempts_used >= self.config.attempt_limit:
            raise GenerationFailure("attempt_limit", "The shared inference-attempt limit has been reached.", metrics=metrics)
        supported = self._verify_model(metrics)
        if "structured_outputs" in supported:
            response_format = {"type": "json_schema", "json_schema": {
                "name": "researchlens_answer", "strict": True, "schema": ModelAnswer.model_json_schema()}}
        elif "response_format" in supported:
            # Explicitly selected JSON-only alternative; same local validator.
            response_format = {"type": "json_object"}
        else:
            raise GenerationFailure("unsupported_model", "Selected model does not advertise JSON output support.", metrics=metrics)
        body = {
            "model": self.config.model, "messages": messages, "stream": False,
            "max_tokens": self.config.max_tokens, "response_format": response_format,
            "provider": {"require_parameters": True, "max_price": {"prompt": 0, "completion": 0}},
        }
        if "reasoning" in supported:
            body["reasoning"] = {"effort": "low", "exclude": True}
        headers = {"Authorization": "Bearer " + self.config.api_key.get_secret_value(),
                   "Content-Type": "application/json", "X-Title": "ResearchLens"}
        for attempt in range(self.config.max_attempts):
            if self.attempts_used >= self.config.attempt_limit:
                raise GenerationFailure("attempt_limit", "The shared inference-attempt limit has been reached.", metrics=metrics)
            self.attempts_used += 1
            metrics.attempts += 1
            try:
                response = self.http.post(f"{BASE_URL}/chat/completions", headers=headers, json=body)
            except (httpx.TimeoutException, httpx.TransportError):
                metrics.accounting_complete = False
                if attempt + 1 < self.config.max_attempts and self.attempts_used < self.config.attempt_limit:
                    self.sleep(1.0)
                    continue
                raise GenerationFailure("request_failed", "OpenRouter request timed out or could not connect.", True, metrics) from None
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("expected object")
            except (ValueError, TypeError):
                payload = {}
            self._account(payload, metrics)
            provider_error = payload.get("error")
            status = response.status_code
            if isinstance(provider_error, dict):
                try:
                    status = int(provider_error.get("code", 502))
                except (ValueError, TypeError):
                    status = 502
            if response.is_error or provider_error:
                error, retry, delay = self._error(status, response, provider_error)
                if retry and attempt + 1 < self.config.max_attempts and self.attempts_used < self.config.attempt_limit:
                    self.sleep(delay)
                    continue
                raise GenerationFailure(error.code, error.message, error.retryable, metrics)
            try:
                choice = payload["choices"][0]
                message = choice["message"]
                if choice.get("finish_reason") != "stop" or message.get("refusal"):
                    raise ValueError("incomplete or refused output")
                output = ModelAnswer.model_validate_json(message["content"])
            except (ValueError, TypeError, KeyError, IndexError, ValidationError):
                raise GenerationFailure("invalid_model_output", "Model returned an incomplete or invalid structured answer.", metrics=metrics) from None
            return output, metrics
        raise AssertionError("unreachable")

    @staticmethod
    def _account(payload: dict, metrics: Metrics):
        for source, target in (("id", "request_id"), ("provider", "provider")):
            if isinstance(payload.get(source), str):
                setattr(metrics, target, payload[source])
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            metrics.accounting_complete = False
            return
        details = usage.get("completion_tokens_details")
        values = {"prompt_tokens": usage.get("prompt_tokens"),
                  "completion_tokens": usage.get("completion_tokens"),
                  "reasoning_tokens": details.get("reasoning_tokens") if isinstance(details, dict) else None,
                  "cost_usd": usage.get("cost")}
        for name, value in values.items():
            valid = (type(value) in (float, int) and math.isfinite(value) and value >= 0)
            if name != "cost_usd":
                valid = valid and type(value) is int
            if valid:
                setattr(metrics, name, (getattr(metrics, name) or 0) + value)
            elif name != "reasoning_tokens":
                metrics.accounting_complete = False

    @staticmethod
    def _error(status: int, response: httpx.Response, provider_error) -> tuple[ErrorInfo, bool, float]:
        # The body is used only for classification, never surfaced or logged.
        raw = str(provider_error or "").casefold()
        if status == 429:
            daily = any(word in raw for word in ("daily", "per day", "per-day", "quota"))
            delay = _retry_after(response.headers.get("Retry-After"))
            if daily or delay > 30:
                return ErrorInfo(code="quota_exhausted", message="Free request quota exhausted or retry wait exceeds 30 seconds."), False, 0
            return ErrorInfo(code="rate_limited", message="Free endpoint is rate limited.", retryable=True), True, delay
        if status in {408, 500, 502, 503, 504}:
            delay = _retry_after(response.headers.get("Retry-After"))
            return ErrorInfo(code="provider_unavailable", message="The free provider is temporarily unavailable.", retryable=True), delay <= 30, min(delay, 30)
        code = {400: "invalid_request", 401: "authentication_failed", 402: "credits_required",
                403: "access_denied", 404: "invalid_model"}.get(status, "api_error")
        return ErrorInfo(code=code, message="OpenRouter rejected the request; check model configuration and account access."), False, 0


def _retry_after(value: str | None) -> float:
    if value is None:
        return 1.0
    try:
        seconds = float(value)
        return max(0.0, seconds) if math.isfinite(seconds) else 31.0
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 31.0
