"""Reciprocal Rank Fusion: scores are combined by rank, never raw scale."""
from .common import rank_results, validate_query
from src.profiling import timed


@timed("rrf_fusion")
def reciprocal_rank_fusion(rankings: dict[str, list[dict]], constant: int = 60,
                           top_k: int = 5) -> list[dict]:
    if type(constant) is not int or constant < 1:
        raise ValueError("RRF constant must be a positive integer")
    merged = {}
    for name, rows in rankings.items():
        seen = set()
        for rank, row in enumerate(rows, 1):
            key = row["chunk_id"]
            if key in seen:
                continue
            seen.add(key)
            if key not in merged:
                merged[key] = {**row, "retrieval_score": 0.0, "rerank_score": None,
                               "vector_rank": None, "bm25_rank": None,
                               "vector_score": None, "bm25_score": None}
            merged[key][f"{name}_rank"] = rank
            merged[key][f"{name}_score"] = row["retrieval_score"]
            merged[key]["retrieval_score"] += 1.0 / (constant + rank)
    for row in merged.values():
        row["rrf_score"] = row["retrieval_score"]
    return rank_results(list(merged.values()), "retrieval_score", top_k)


class HybridSearch:
    def __init__(self, bm25, vector, config):
        self.bm25, self.vector, self.config = bm25, vector, config

    def search(self, question: str, top_k: int = 5, paper_ids=None,
               exclude_flagged: bool = False) -> list[dict]:
        validate_query(question, top_k)
        if paper_ids is not None and not isinstance(paper_ids, str):
            paper_ids = tuple(paper_ids)
        filters = dict(paper_ids=paper_ids, exclude_flagged=exclude_flagged)
        return reciprocal_rank_fusion({
            "bm25": self.bm25.search(question, self.config.bm25_candidates, **filters),
            "vector": self.vector.search(question, self.config.vector_candidates, **filters)},
            self.config.rrf_constant, top_k)
