"""Shared CLI options keep experiment settings comparable."""
import argparse
from dataclasses import replace
from pathlib import Path
from .config import RetrievalConfig


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    defaults = RetrievalConfig()
    parser.add_argument("--chunks", type=Path, default=defaults.chunks_path)
    parser.add_argument("--index-dir", type=Path, default=defaults.index_dir)
    parser.add_argument("--device", default=None, help="cpu, cuda, or automatic when omitted")
    parser.add_argument("--vector-candidates", type=int, default=defaults.vector_candidates)
    parser.add_argument("--bm25-candidates", type=int, default=defaults.bm25_candidates)
    parser.add_argument("--rerank-candidates", type=int, default=defaults.rerank_candidates)
    parser.add_argument("--embedding-batch-size", type=int, default=defaults.embedding_batch_size)
    parser.add_argument("--rerank-batch-size", type=int, default=defaults.rerank_batch_size)


def config_from_args(args) -> RetrievalConfig:
    return replace(RetrievalConfig(), chunks_path=args.chunks, index_dir=args.index_dir,
        device=args.device, vector_candidates=args.vector_candidates,
        bm25_candidates=args.bm25_candidates, rerank_candidates=args.rerank_candidates,
        embedding_batch_size=args.embedding_batch_size, rerank_batch_size=args.rerank_batch_size)
