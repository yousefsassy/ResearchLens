import pytest
from src.retrieval.bm25_search import BM25Search, tokenize


def test_keyword_ranking_and_filters(chunks):
    search = BM25Search(chunks)
    assert search.search("SelfCheckGPT hallucinations")[0]["paper_id"] == "P001"
    assert search.search("FActScore")[0]["needs_review"]
    assert search.search("FActScore", exclude_flagged=True) == []
    assert search.search("SelfCheckGPT", paper_ids=["P002"]) == []
    assert search.search("nonexistentword") == []
    assert search.search("???") == []
    assert tokenize("SelfCheckGPT, FACT-score!") == ["selfcheckgpt", "fact", "score"]


def test_zero_score_match_is_not_unrelated(chunks):
    chunks[0]["text"] = "word"
    chunks[1]["text"] = "different"
    result = BM25Search(chunks[:2]).search("word")
    assert len(result) == 1
    assert result[0]["bm25_score"] == 0


def test_empty_token_corpus(chunks):
    for chunk in chunks: chunk["text"] = "!!!"
    assert BM25Search(chunks).search("anything") == []


def test_empty_question(chunks):
    with pytest.raises(ValueError): BM25Search(chunks).search(" ")
