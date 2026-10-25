"""Exact cosine search over normalized NumPy vectors."""
import numpy as np
from .common import candidate_indices, make_result, rank_results, validate_query
from .embeddings import normalize


class VectorSearch:
    def __init__(self, chunks: list[dict], embeddings: np.ndarray, encoder):
        self.chunks = chunks
        self.embeddings = normalize(embeddings)
        if len(chunks) != len(self.embeddings):
            raise ValueError("chunk/embedding row count mismatch")
        self.encoder = encoder

    def search(self, question: str, top_k: int = 5, paper_ids=None,
               exclude_flagged: bool = False) -> list[dict]:
        question = validate_query(question, top_k)
        indices = candidate_indices(self.chunks, paper_ids, exclude_flagged)
        if not indices:
            return []
        query = normalize(np.asarray(self.encoder.encode_query(question))[None, :])[0]
        if query.shape[0] != self.embeddings.shape[1]:
            raise ValueError("query/index embedding dimension mismatch")
        scores = self.embeddings[indices] @ query
        results = [make_result(self.chunks[i], score, "vector")
                   for i, score in zip(indices, scores)]
        return rank_results(results, "retrieval_score", top_k)
