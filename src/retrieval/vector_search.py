"""Exact cosine search over normalized NumPy vectors."""
from collections import OrderedDict

import numpy as np
from .common import candidate_indices, make_result, rank_results, validate_query
from .embeddings import normalize
from src.profiling import measure


class VectorSearch:
    def __init__(self, chunks: list[dict], embeddings: np.ndarray, encoder):
        self.chunks = chunks
        self.embeddings = normalize(embeddings)
        if len(chunks) != len(self.embeddings):
            raise ValueError("chunk/embedding row count mismatch")
        self.encoder = encoder
        self._query_cache = OrderedDict()
        self._cached_encoder = encoder

    def search(self, question: str, top_k: int = 5, paper_ids=None,
               exclude_flagged: bool = False) -> list[dict]:
        question = validate_query(question, top_k)
        indices = candidate_indices(self.chunks, paper_ids, exclude_flagged)
        if not indices:
            return []
        if self.encoder is not self._cached_encoder:
            self._query_cache.clear()
            self._cached_encoder = self.encoder
        query = self._query_cache.get(question)
        if query is None:
            query = normalize(np.asarray(self.encoder.encode_query(question))[None, :])[0]
            if query.shape[0] != self.embeddings.shape[1]:
                raise ValueError("query/index embedding dimension mismatch")
            self._query_cache[question] = query
            if len(self._query_cache) > 32:
                self._query_cache.popitem(last=False)
        self._query_cache.move_to_end(question)
        if query.shape[0] != self.embeddings.shape[1]:
            raise ValueError("query/index embedding dimension mismatch")
        with measure("vector_similarity_and_ranking"):
            scores = self.embeddings[indices] @ query
            results = [make_result(self.chunks[i], score, "vector")
                       for i, score in zip(indices, scores)]
            return rank_results(results, "retrieval_score", top_k)
