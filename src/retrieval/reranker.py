"""Lazy cross-encoder scoring; outputs are uncalibrated relevance scores."""
import time
import numpy as np
from .config import prepare_model_cache
from .common import rank_results, validate_query


class CrossEncoderReranker:
    def __init__(self, config, model=None):
        self.config, self._model = config, model
        self.last_latency_seconds = 0.0

    @property
    def model(self):
        if self._model is None:
            prepare_model_cache(self.config)
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.config.reranker_model,
                revision=self.config.reranker_revision, device=self.config.device,
                max_length=self.config.max_seq_length, cache_folder=str(self.config.model_cache_dir))
        return self._model

    def rerank(self, question: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        question = validate_query(question, top_k)
        started = time.perf_counter()
        try:
            if not candidates:
                return []
            scores = np.asarray(self.model.predict(
                [(question, row["text"]) for row in candidates],
                batch_size=self.config.rerank_batch_size, show_progress_bar=False)).reshape(-1)
            if len(scores) != len(candidates) or not np.isfinite(scores).all():
                raise ValueError("reranker returned invalid scores")
            rows = [{**row, "retrieval_rank": row.get("rank"), "rerank_score": float(score)}
                    for row, score in zip(candidates, scores)]
            return rank_results(rows, "rerank_score", top_k)
        finally:
            self.last_latency_seconds = time.perf_counter() - started
