from dataclasses import replace
import json
import numpy as np
import pytest
from src.retrieval.embeddings import BGEEncoder, build_index, load_index, normalize


def test_shape_alignment_and_cache(config, chunks, encoder):
    vectors, metadata, cached = build_index(chunks, config, encoder)
    assert not cached
    assert vectors.shape == (4, 2)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)
    assert metadata["chunk_ids"] == [r["chunk_id"] for r in chunks]
    assert np.allclose(vectors[2], np.array([1, 2]) / np.sqrt(5))
    class FailEncoder:
        def encode_documents(self, texts):
            raise AssertionError("valid cache should not re-encode")
    assert build_index(chunks, config, FailEncoder())[2]


@pytest.mark.parametrize("change", ["text", "order", "metadata", "model", "revision", "instruction"])
def test_stale_index(config, chunks, encoder, change):
    build_index(chunks, config, encoder)
    if change == "text": chunks[0]["text"] += " updated"
    if change == "order": chunks.reverse()
    if change == "metadata": chunks[0]["needs_review"] = True
    if change == "model": config = replace(config, embedding_model="other")
    if change == "revision": config = replace(config, embedding_revision="other")
    if change == "instruction": config = replace(config, query_instruction="other")
    with pytest.raises(ValueError, match="stale"):
        load_index(chunks, config)
    assert not build_index(chunks, config, encoder)[2]


def test_corrupt_file(config, chunks, encoder):
    build_index(chunks, config, encoder)
    (config.index_dir / "embeddings.npy").write_bytes(b"invalid")
    with pytest.raises(ValueError, match="checksum"):
        load_index(chunks, config)
    assert not build_index(chunks, config, encoder)[2]


@pytest.mark.parametrize("vectors", [[[0, 0]], [[float("nan"), 1]], [1, 2]])
def test_bad_embeddings(vectors):
    with pytest.raises(ValueError): normalize(vectors)


def test_query_instruction_only(config):
    class Model:
        device = "cpu"
        calls = []
        def encode(self, texts, **kwargs):
            self.calls.append(texts)
            return np.ones((len(texts), 2))
    encoder = BGEEncoder(config)
    encoder._model = Model()
    encoder.encode_documents(["passage"])
    encoder.encode_query("question")
    assert encoder.model.calls == [["passage"], [config.query_instruction + "question"]]


@pytest.mark.parametrize("metadata", [[], {"dimensions": 0}, {"dimensions": "384"}])
def test_invalid_index_metadata(config, chunks, encoder, metadata):
    build_index(chunks, config, encoder)
    (config.index_dir / "index_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError): load_index(chunks, config)
    assert not build_index(chunks, config, encoder)[2]


def test_model_loaded_once_and_pinned(config, monkeypatch):
    import sys
    from types import SimpleNamespace
    calls = []
    class Model:
        device = "cpu"
        def __init__(self, name, **kwargs): calls.append((name, kwargs))
        def encode(self, texts, **kwargs): return np.ones((len(texts), 2))
    monkeypatch.setenv("HF_XET_CACHE", "test-original")
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Model))
    encoder = BGEEncoder(config)
    encoder.encode_query("one")
    encoder.encode_query("two")
    assert len(calls) == 1
    assert calls[0][1]["revision"] == config.embedding_revision
    assert calls[0][1]["cache_folder"] == str(config.model_cache_dir)
    assert encoder.model.max_seq_length == config.max_seq_length
