"""Project-relative defaults and explicit experiment settings."""
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class RetrievalConfig:
    chunks_path: Path = PROJECT_ROOT / "data/processed/chunks.jsonl"
    index_dir: Path = PROJECT_ROOT / "data/indexes"
    model_cache_dir: Path = PROJECT_ROOT / ".cache/huggingface"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_revision: str = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    reranker_revision: str = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
    query_instruction: str = "Represent this sentence for searching relevant passages: "
    device: str | None = None
    embedding_batch_size: int = 32
    rerank_batch_size: int = 16
    max_seq_length: int = 512
    vector_candidates: int = 50
    bm25_candidates: int = 50
    rerank_candidates: int = 30
    rrf_constant: int = 60

    def __post_init__(self):
        for name in ("embedding_batch_size", "rerank_batch_size", "max_seq_length",
                     "vector_candidates", "bm25_candidates", "rerank_candidates", "rrf_constant"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")

    def to_dict(self) -> dict:
        return {key: str(value) if isinstance(value, Path) else value
                for key, value in asdict(self).items()}


def prepare_model_cache(config: RetrievalConfig) -> None:
    """Set Xet's separate cache before model libraries initialize their globals.

    The model cache argument alone does not override HF_HOME's Xet directory.
    Call before importing sentence-transformers; this setting is process-wide.
    """
    import os
    os.environ["HF_XET_CACHE"] = str(Path(config.model_cache_dir) / "xet")
