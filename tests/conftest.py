import json
from dataclasses import replace
import numpy as np
import pytest
from src.retrieval.config import RetrievalConfig


@pytest.fixture
def chunks():
    texts = ["SelfCheckGPT detects hallucinations using sample consistency.",
             "FActScore measures atomic facts and factual precision.",
             "Retrieval supplies external knowledge to language models.",
             "Bananas are yellow fruit."]
    return [{"chunk_id": f"P00{i+1}-p001-c001", "paper_id": f"P00{i+1}",
             "pdf_filename": f"paper{i+1}.pdf", "pdf_page": 1, "text": text,
             "needs_review": i == 1, "review_flags": ["table"] if i == 1 else [],
             "chunk_index": 1, "char_count": len(text), "extra": {"preserve": True}}
            for i, text in enumerate(texts)]


@pytest.fixture
def config(tmp_path, chunks):
    path = tmp_path / "chunks.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in chunks), encoding="utf-8")
    return replace(RetrievalConfig(), chunks_path=path, index_dir=tmp_path / "indexes")


class FakeEncoder:
    _model = None
    device = "fake-cpu"
    def encode_documents(self, texts):
        return np.asarray([[1, i] for i in range(len(texts))], dtype=np.float32)
    def encode_query(self, text):
        return np.array([1, 0], dtype=np.float32)


@pytest.fixture
def encoder():
    return FakeEncoder()
