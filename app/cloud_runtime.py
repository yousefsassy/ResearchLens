"""Standalone adapter: reuse ResearchService without starting FastAPI or HTTP.

Local allowance files are shared by sessions but may disappear on cloud restart.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import HTTPException

from app.client import APIClientError
from app.schemas import FeedbackResponse
from app.security import DemoGuard

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CloudSettings:
    artifact_url: str
    artifact_sha256: str
    expires_at: datetime
    max_questions: int = 20
    use_local_artifacts: bool = False

    @classmethod
    def from_env(cls):
        if len(os.environ.get('RESEARCHLENS_DEMO_PASSWORD', '')) < 12:
            raise APIClientError('Configure a private RESEARCHLENS_DEMO_PASSWORD of at least 12 characters in Streamlit secrets.')
        if not os.environ.get('OPENAI_API_KEY', '').strip():
            raise APIClientError('Configure OPENAI_API_KEY in Streamlit server secrets.')
        try:
            expires = datetime.fromisoformat(os.environ.get('RESEARCHLENS_DEMO_EXPIRES_AT', '').replace('Z', '+00:00'))
            maximum = int(os.environ.get('RESEARCHLENS_CLOUD_MAX_QUESTIONS', '20'))
            if expires.tzinfo is None or not 1 <= maximum <= 100:
                raise ValueError('Invalid demo settings')
        except ValueError:
            raise APIClientError('Set RESEARCHLENS_DEMO_EXPIRES_AT to an explicit UTC event end and CLOUD_MAX_QUESTIONS to 1–100.') from None
        if datetime.now(timezone.utc) >= expires:
            raise APIClientError('This demonstration has ended. The owner must review billing and update the event end before reopening it.')
        return cls(os.environ.get('RESEARCHLENS_ARTIFACT_URL', ''),
            os.environ.get('RESEARCHLENS_ARTIFACT_SHA256', ''), expires, maximum,
            os.environ.get('RESEARCHLENS_USE_LOCAL_ARTIFACTS', '').lower() == 'true')


@dataclass
class CloudRuntime:
    service: object
    guard: DemoGuard

    def close(self):
        self.service.close()


def build_runtime(settings, *, root=ROOT, service_factory=None, provision=None):
    # Set before Sentence Transformers / torch imports; no model download fallback.
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ.setdefault('OMP_NUM_THREADS', '2')
    os.environ.setdefault('MKL_NUM_THREADS', '2')
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    if provision is None:
        from app.cloud_artifacts import ensure_runtime
        provision = ensure_runtime
    provision(root, settings.artifact_url, settings.artifact_sha256,
              use_local=settings.use_local_artifacts)
    service = None
    try:
        if service_factory is None:
            from app.service import ResearchService
            from app.feedback import FeedbackStore
            from src.retrieval.config import RetrievalConfig
            from src.retrieval.retriever import ResearchRetriever
            config = RetrievalConfig(chunks_path=root / 'data/processed/chunks.jsonl',
                index_dir=root / 'data/indexes', model_cache_dir=root / '.cache/huggingface', device='cpu')
            service = ResearchService(retriever_factory=lambda: ResearchRetriever(config),
                feedback_store=FeedbackStore(root / 'data/feedback/cloud-feedback.jsonl'))
        else:
            service = service_factory()
        if service.warmup().status != 'ok':
            raise APIClientError('Research service initialization failed. Check the verified artifacts, CPU dependencies and server key configuration.')
        guard = DemoGuard(budget_path=root / 'data/demo/cloud-budget.json',
                          max_questions=settings.max_questions, ask_per_minute=3,
                          feedback_per_minute=20)
        return CloudRuntime(service, guard)
    except Exception:
        if service is not None:
            service.close()
        raise APIClientError('Research service initialization failed. Check the verified artifacts, CPU dependencies and server key configuration.') from None


class DirectResearchClient:
    """Same methods as ResearchAPIClient, with per-call server-side demo checks."""
    def __init__(self, runtime, *, authorized, expires_at, clock=None):
        self.runtime = runtime
        self.authorized = authorized
        self.expires_at = expires_at
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _admit(self, endpoint):
        if not self.authorized():
            raise APIClientError('Demonstration authorization required.')
        if self.clock() >= self.expires_at:
            raise APIClientError('This demonstration has ended. Contact the project team.')
        try:
            self.runtime.guard.reserve(endpoint)
        except HTTPException as error:
            # Guard diagnostics are fixed strings and never contain raw credentials.
            raise APIClientError(str(error.detail)) from None

    def health(self):
        return self.runtime.service.health()

    def papers(self):
        try:
            return self.runtime.service.papers()
        except Exception:
            raise APIClientError('The paper catalog is unavailable.') from None

    def ask(self, request):
        self._admit('ask')
        try:
            return self.runtime.service.ask(request)
        except Exception:
            raise APIClientError('Research service could not complete this question. Check server configuration; no automatic retry was sent.') from None

    def record_feedback(self, request):
        self._admit('feedback')
        try:
            self.runtime.service.record_feedback(request)
        except Exception:
            raise APIClientError('Feedback storage is unavailable.') from None
        return FeedbackResponse(stored=True)
