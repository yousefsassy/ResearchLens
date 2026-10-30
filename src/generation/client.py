
"""OpenAI Responses API client for ResearchLens."""
import json
import time

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from .config import GenerationConfig
from .schemas import ErrorInfo, Metrics, ModelAnswer


class GenerationFailure(Exception):
    def __init__(self, code, message, retryable=False, metrics=None):
        super().__init__(message)
        self.error = ErrorInfo(
            code=code,
            message=message,
            retryable=retryable,
        )
        self.metrics = metrics or Metrics()


class OpenAIClient:
    def __init__(self, config: GenerationConfig, client=None):
        self.config = config
        self.client = client or OpenAI(
            timeout=config.request_timeout,
            max_retries=0,
        )
        self.attempts_used = 0

    def close(self):
        self.client.close()

    def complete(self, messages: list[dict]):
        return self._complete(messages, self.config.max_attempts)

    def complete_repair(self, messages: list[dict]):
        """Allow exactly one additional request, without transport retries."""
        return self._complete(messages, 1)

    def _complete(self, messages: list[dict], max_attempts: int):
        metrics = Metrics(
            model=self.config.model,
            provider="openai",
        )

        if self.attempts_used >= self.config.attempt_limit:
            raise GenerationFailure(
                "attempt_limit",
                "The inference-attempt limit has been reached.",
                metrics=metrics,
            )

        instructions = "\n".join(
            m["content"] for m in messages
            if m["role"] == "system"
        )
        user_input = "\n".join(
            m["content"] for m in messages
            if m["role"] == "user"
        )

        schema = ModelAnswer.model_json_schema()
        # The API already receives this exact schema via text.format. Avoid
        # duplicating it in the user payload; leave injected-client prompts intact.
        try:
            payload = json.loads(user_input)
            if isinstance(payload, dict) and payload.get("output_schema") == schema:
                del payload["output_schema"]
                user_input = json.dumps(payload, ensure_ascii=False)
        except (ValueError, TypeError):
            pass

        for attempt in range(max_attempts):
            if self.attempts_used >= self.config.attempt_limit:
                raise GenerationFailure(
                    "attempt_limit",
                    "The inference-attempt limit has been reached.",
                    metrics=metrics,
                )

            self.attempts_used += 1
            metrics.attempts += 1

            try:
                response = self.client.responses.create(
                    model=self.config.model,
                    instructions=instructions,
                    input=user_input,
                    max_output_tokens=self.config.max_tokens,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "research_answer",
                            "schema": schema,
                            "strict": True,
                        }
                    },
                )

                metrics.request_id = response.id

                if response.usage:
                    metrics.prompt_tokens = (
                        (metrics.prompt_tokens or 0)
                        + response.usage.input_tokens
                    )
                    metrics.completion_tokens = (
                        (metrics.completion_tokens or 0)
                        + response.usage.output_tokens
                    )
                    details = response.usage.output_tokens_details
                    metrics.reasoning_tokens = (
                        (metrics.reasoning_tokens or 0)
                        + (getattr(details, "reasoning_tokens", 0) or 0)
                    )
                else:
                    metrics.accounting_complete = False

                if response.status != "completed":
                    raise GenerationFailure(
                        "incomplete_generation",
                        "The model did not complete its response.",
                        metrics=metrics,
                    )

                output = ModelAnswer.model_validate_json(
                    response.output_text
                )
                return output, metrics

            except (ValidationError, ValueError, json.JSONDecodeError):
                raise GenerationFailure(
                    "invalid_model_output",
                    "The model returned an invalid structured answer.",
                    metrics=metrics,
                ) from None

            except OpenAIError:
                metrics.accounting_complete = False
                if (
                    attempt + 1 < max_attempts
                    and self.attempts_used < self.config.attempt_limit
                ):
                    time.sleep(1)
                    continue

                metrics.accounting_complete = False
                raise GenerationFailure(
                    "openai_api_error",
                    "OpenAI request failed. Check the API key, model access, and quota.",
                    retryable=True,
                    metrics=metrics,
                ) from None
