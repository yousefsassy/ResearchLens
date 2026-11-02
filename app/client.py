"""Small HTTP adapter; only the server-to-server demo token is used here."""
import os
from urllib.parse import urlsplit

import httpx
from pydantic import TypeAdapter, ValidationError

from app.schemas import AskRequest, FeedbackRequest, FeedbackResponse, HealthResponse, PaperSummary
from src.generation.schemas import GenerationResponse


class APIClientError(Exception):
    """A safe, user-facing transport or protocol diagnostic."""


class ResearchAPIClient:
    def __init__(self, base_url=None, client=None, *, api_token=None):
        base_url = (base_url or os.environ.get("RESEARCHLENS_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        try:
            parsed = urlsplit(base_url)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
                    or parsed.password or parsed.query or parsed.fragment):
                raise ValueError("Invalid API URL")
            _ = parsed.port
        except ValueError:
            raise APIClientError("RESEARCHLENS_API_URL must be a valid HTTP URL without credentials, query or fragment.") from None
        self.base_url = base_url
        self._token = api_token if api_token is not None else os.environ.get("RESEARCHLENS_API_TOKEN", "")
        if self._token and parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1", "testserver"}:
            raise APIClientError("Authenticated remote API connections require HTTPS.")
        self._owned = client is None
        self._client = client or httpx.Client(base_url=base_url,
            timeout=httpx.Timeout(400, connect=5, pool=5), transport=httpx.HTTPTransport(retries=0))

    def close(self):
        if self._owned:
            self._client.close()

    def _request(self, method, path, **kwargs):
        if method == "POST" and self._token:
            kwargs["headers"] = {**kwargs.get("headers", {}), "Authorization": "Bearer " + self._token}
        try:
            return self._client.request(method, self.base_url + path, **kwargs)
        except httpx.TimeoutException:
            raise APIClientError("The backend timed out. The question may still be processing; no automatic retry was sent.") from None
        except httpx.HTTPError:
            raise APIClientError("Cannot reach the ResearchLens API. Check that FastAPI is running and the API URL is correct.") from None

    @staticmethod
    def _parse(response, model):
        try:
            return TypeAdapter(model).validate_json(response.content)
        except (ValidationError, ValueError, TypeError):
            raise APIClientError("The backend returned an invalid response. No unvalidated answer was displayed.") from None

    @staticmethod
    def _http_error(response):
        messages = {401: "The frontend API authentication is not configured correctly.",
                    403: "The backend denied this request.",
                    429: "The demonstration rate limit or question allowance has been reached. Contact the demo owner.",
                    422: "Invalid request. Check the question, paper IDs and optional filters.",
                    502: "The generation provider failed. No answer is available.",
                    503: "The backend is not ready or is busy. Check its index, configuration and logs.",
                    504: "The generation provider timed out. No automatic retry was sent."}
        raise APIClientError(messages.get(response.status_code, "The backend could not complete this request."))

    def health(self):
        response = self._request("GET", "/health", timeout=10)
        if response.status_code not in {200, 503}:
            self._http_error(response)
        return self._parse(response, HealthResponse)

    def papers(self):
        response = self._request("GET", "/papers", timeout=10)
        if response.status_code != 200:
            self._http_error(response)
        return self._parse(response, list[PaperSummary])

    def ask(self, request: AskRequest):
        response = self._request("POST", "/ask", json=request.model_dump(mode="json"))
        if response.status_code == 200:
            result = self._parse(response, GenerationResponse)
            if result.status == "error":
                raise APIClientError("The backend returned an inconsistent answer status.")
            return result
        if response.status_code in {422, 500, 502, 503, 504}:
            try:
                result = self._parse(response, GenerationResponse)
            except APIClientError:
                self._http_error(response)
            if result.status == "error" and result.error is not None:
                return result
        self._http_error(response)

    def record_feedback(self, feedback: FeedbackRequest):
        response = self._request("POST", "/feedback", json=feedback.model_dump(mode="json"), timeout=10)
        if response.status_code != 200:
            self._http_error(response)
        result = self._parse(response, FeedbackResponse)
        if not result.stored:
            raise APIClientError("Feedback was not saved. Please try again.")
        return result
