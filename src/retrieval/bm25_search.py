"""Case-folded Unicode word tokenization with rank-bm25."""
import re
from rank_bm25 import BM25Okapi
from .common import candidate_indices, make_result, rank_results, validate_query


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)


class BM25Search:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.tokens = [tokenize(chunk["text"]) for chunk in chunks]
        self.index = BM25Okapi(self.tokens) if any(self.tokens) else None

    def search(self, question: str, top_k: int = 5, paper_ids=None,
               exclude_flagged: bool = False) -> list[dict]:
        question = validate_query(question, top_k)
        tokens = tokenize(question)
        if not tokens or self.index is None:
            return []
        scores = self.index.get_scores(tokens)
        # Keep actual lexical matches even when Okapi IDF gives a zero/negative
        # score in tiny corpora; never return unrelated zero-score documents.
        terms = set(tokens)
        results = [make_result(self.chunks[i], scores[i], "bm25")
                   for i in candidate_indices(self.chunks, paper_ids, exclude_flagged)
                   if terms.intersection(self.tokens[i])]
        return rank_results(results, "retrieval_score", top_k)
