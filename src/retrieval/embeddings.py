"""Lazy BGE encoding and checked, reusable NumPy index persistence."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from .common import corpus_fingerprint
from .config import RetrievalConfig, prepare_model_cache
from src.profiling import measure, timed


def normalize(vectors: np.ndarray) -> np.ndarray:
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2 or not matrix.shape[1] or not np.isfinite(matrix).all():
        raise ValueError("embeddings must be a finite 2D matrix with nonzero dimensions")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("zero-length embedding")
    return matrix / norms


class BGEEncoder:
    def __init__(self, config: RetrievalConfig):
        self.config = config
        self._model = None

    @property
    def model(self):
        if self._model is None:
            with measure("bge_model_loading"):
                prepare_model_cache(self.config)
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.config.embedding_model,
                    revision=self.config.embedding_revision, device=self.config.device,
                    cache_folder=str(self.config.model_cache_dir))
            self._model.max_seq_length = self.config.max_seq_length
        return self._model

    @property
    def device(self) -> str:
        return str(self.model.device)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return normalize(self.model.encode(texts, batch_size=self.config.embedding_batch_size,
            convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False))

    @timed("query_embedding_including_model_load")
    def encode_query(self, question: str) -> np.ndarray:
        return self.encode_documents([self.config.query_instruction + question])[0]


def index_signature(chunks: list[dict], config: RetrievalConfig) -> dict:
    return {"schema_version": 1, "corpus_fingerprint": corpus_fingerprint(chunks),
            "chunk_ids": [c["chunk_id"] for c in chunks],
            "model_name": config.embedding_model, "model_revision": config.embedding_revision,
            "query_instruction": config.query_instruction, "max_seq_length": config.max_seq_length,
            "normalized": True, "dtype": "float32"}


@timed("vector_index_loading")
def load_index(chunks: list[dict], config: RetrievalConfig) -> tuple[np.ndarray, dict]:
    directory = Path(config.index_dir)
    metadata = json.loads((directory / "index_metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("Index metadata must be an object; rebuild index")
    if type(metadata.get("dimensions")) is not int or metadata["dimensions"] < 1:
        raise ValueError("Invalid embedding dimensions; rebuild index")
    expected = index_signature(chunks, config)
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Index is stale or misaligned; run scripts/build_index.py")
    path = directory / "embeddings.npy"
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata.get("embeddings_sha256"):
        raise ValueError("Embedding file checksum mismatch; rebuild index")
    matrix = np.load(path, allow_pickle=False)
    if matrix.shape != (len(chunks), metadata.get("dimensions")) or matrix.dtype != np.float32:
        raise ValueError("Embedding shape/dtype mismatch; rebuild index")
    if not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-5):
        raise ValueError("Embeddings are not finite unit vectors; rebuild index")
    return matrix, metadata


def build_index(chunks: list[dict], config: RetrievalConfig, encoder=None,
                force: bool = False) -> tuple[np.ndarray, dict, bool]:
    """Reuse a valid cache; metadata is committed last to detect interrupted writes."""
    if not force:
        try:
            matrix, metadata = load_index(chunks, config)
            return matrix, metadata, True
        except (OSError, ValueError, KeyError, TypeError):
            pass  # An absent/invalid cache is regenerated, never silently used.
    started = time.perf_counter()
    encoder = encoder or BGEEncoder(config)
    matrix = normalize(encoder.encode_documents([chunk["text"] for chunk in chunks]))
    if len(matrix) != len(chunks):
        raise ValueError("Encoder returned the wrong number of rows")
    directory = Path(config.index_dir)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / "embeddings.npy.tmp"
    with temporary.open("wb") as output:
        np.save(output, matrix, allow_pickle=False)
    metadata = {**index_signature(chunks, config), "dimensions": int(matrix.shape[1]),
                "configuration": config.to_dict(), "device": encoder.device,
                "build_seconds": time.perf_counter() - started,
                "embeddings_sha256": hashlib.sha256(temporary.read_bytes()).hexdigest()}
    meta_tmp = directory / "index_metadata.json.tmp"
    meta_tmp.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    temporary.replace(directory / "embeddings.npy")
    meta_tmp.replace(directory / "index_metadata.json")
    return matrix, metadata, False
