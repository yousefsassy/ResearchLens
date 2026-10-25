"""Public Member 3 interface. Reuse one instance across questions."""
import time
from .bm25_search import BM25Search
from .common import load_chunks, validate_query
from .config import RetrievalConfig
from .embeddings import BGEEncoder, load_index
from .hybrid_search import HybridSearch
from .reranker import CrossEncoderReranker
from .vector_search import VectorSearch


class ResearchRetriever:
    def __init__(self, config: RetrievalConfig | None = None):
        self.config = config or RetrievalConfig()
        self.chunks = load_chunks(self.config.chunks_path)
        self.encoder = BGEEncoder(self.config)
        self.reranker = CrossEncoderReranker(self.config)
        self._bm25 = self._vector = None
        self.last_timings = {}

    @property
    def bm25(self):
        if self._bm25 is None:
            self._bm25 = BM25Search(self.chunks)
        return self._bm25

    @property
    def vector(self):
        if self._vector is None:
            matrix, _ = load_index(self.chunks, self.config)
            self._vector = VectorSearch(self.chunks, matrix, self.encoder)
        return self._vector

    def search(self, question: str, top_k: int = 5, mode: str = "hybrid",
               rerank: bool = True, paper_ids=None, exclude_flagged: bool = False) -> list[dict]:
        question = validate_query(question, top_k)
        if mode not in {"bm25", "vector", "hybrid"}:
            raise ValueError("mode must be bm25, vector, or hybrid")
        if rerank and top_k > self.config.rerank_candidates:
            raise ValueError("top_k exceeds rerank_candidates; increase the configuration limit")
        started = time.perf_counter()
        count = self.config.rerank_candidates if rerank else top_k
        backend = self.bm25 if mode == "bm25" else self.vector if mode == "vector" else HybridSearch(
            self.bm25, self.vector, self.config)
        results = backend.search(question, count, paper_ids, exclude_flagged)
        retrieved = time.perf_counter()
        if rerank:
            results = self.reranker.rerank(question, results, top_k)
        self.last_timings = {"retrieval_seconds": retrieved - started,
                             "rerank_seconds": self.reranker.last_latency_seconds if rerank else 0.0,
                             "total_seconds": time.perf_counter() - started}
        return results[:top_k]

    def status(self) -> dict:
        try:
            _, metadata = load_index(self.chunks, self.config)
            index = {"valid": True, "metadata": metadata}
        except (OSError, ValueError, KeyError, TypeError) as error:
            index = {"valid": False, "reason": str(error)}
        return {"configuration": self.config.to_dict(), "chunk_count": len(self.chunks),
                "index": index, "last_timings": self.last_timings,
                "embedding_model_loaded": self.encoder._model is not None,
                "reranker_loaded": self.reranker._model is not None}
