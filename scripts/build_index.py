"""Build or validate the corpus embedding cache."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval.cli import add_config_arguments, config_from_args
from src.retrieval.common import load_chunks
from src.retrieval.embeddings import build_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = config_from_args(args)
    started = time.perf_counter()
    chunks = load_chunks(config.chunks_path)
    matrix, metadata, reused = build_index(chunks, config, force=args.force)
    paths = [config.index_dir / name for name in ("embeddings.npy", "index_metadata.json")]
    print(json.dumps({"chunks": len(chunks), "dimensions": matrix.shape[1],
        "device_at_build": metadata["device"], "reused": reused,
        "build_seconds": metadata["build_seconds"], "command_seconds": time.perf_counter() - started,
        "storage_bytes": sum(path.stat().st_size for path in paths),
        "output_paths": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()
