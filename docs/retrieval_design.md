# Retrieval design

## Architecture

```text
chunks.jsonl -> validation -> BM25
                          -> BGE embeddings -> checked NumPy index
question -> BM25 + cosine search -> RRF -> optional cross-encoder -> passages + citations
```

The API returns evidence, not generated answers. Exact cosine search is appropriate for the current small corpus; no vector database is required. Hybrid RRF merges unique chunk IDs using `sum(1 / (60 + branch_rank))`, with ranks starting at one. It does not add incompatible raw BM25 and cosine scores. Ties use chunk IDs.

## Models and methods

| Component | Implementation |
|---|---|
| Keyword | `rank-bm25` Okapi; Unicode alphanumeric tokens, no stemming |
| Vector | `BAAI/bge-small-en-v1.5`; normalized 384-dimensional float32 embeddings |
| Fusion | Reciprocal Rank Fusion of BM25 and vector candidate lists |
| Optional reranker | `cross-encoder/ms-marco-MiniLM-L6-v2`; replaces fused ordering |

Pinned revisions:
- BGE: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- Cross-encoder: `233902d25c440f23af6f7d6e94d2946bac0bee0a`

BGE queries use `Represent this sentence for searching relevant passages: `; documents do not. Both models use a 512-token limit, so long inputs can be truncated. Cross-encoder scores are not probabilities.

## Setup and index

Use Python 3.11 and install [requirements.txt](../requirements.txt) in a virtual environment; see [README](../README.md). Requirements include NumPy, rank-bm25, sentence-transformers, pytest, and the existing PDF extraction dependencies. Sentence-transformers installs its neural dependencies, including PyTorch.

Models download on first neural use to `.cache/huggingface` by default. Hybrid without reranking needs BGE; enabling reranking additionally needs the cross-encoder. A cached model and valid index support offline use. On this machine, setting `$env:HF_HUB_DISABLE_XET = "1"` before downloads resolved Xet cache-space errors.

Preserve the agreed `data/processed/chunks.jsonl`. On a new checkout only, create an absent index:

```powershell
.venv\Scripts\python.exe scripts/build_index.py --device cpu
```

The builder reuses a valid index; `--force` forces replacement. It writes `data/indexes/embeddings.npy` and `index_metadata.json`. Loading validates corpus fingerprint, ordered IDs, model settings, dimensions, checksum, finite values, and unit norms. A corpus or metadata change invalidates the index. Do not run concurrent builders. After an intentional corpus change, rebuild and create a new retriever instance; revalidate evaluation labels.

If processed data is absent, obtain Member 1's agreed outputs. The existing ingestion sequence is `python -m src.ingestion.extract`, then `clean`, then `chunk` under the same module prefix; it writes processed files and should not be used to overwrite the agreed corpus casually.

## Member 3 API

Run from the inner project directory or put that directory on Python's import path:

```python
from src.retrieval import ResearchRetriever

retriever = ResearchRetriever()  # Reuse for serial requests.

def retrieve_evidence(question: str, top_k: int = 5) -> list[dict]:
    return retriever.search(
        question=question,
        top_k=top_k,
        mode="hybrid",
        rerank=False,
    )

for passage in retrieve_evidence("How does SelfCheckGPT detect hallucinations?"):
    print(passage["text"])
    print(passage["chunk_id"], passage["pdf_filename"], passage["pdf_page"])
    print(passage["needs_review"], passage["review_flags"])
```

**Pass `rerank=False` explicitly:** the unchanged public API defaults to `True`. The provisional recommendation follows the [saved pilot](retrieval_results.md).

Equivalent query command:

```powershell
.venv\Scripts\python.exe scripts/test_retrieval.py --question "How does SelfCheckGPT detect hallucinations?" --mode hybrid --no-rerank --top-k 5
```

Each JSON-serializable result preserves `chunk_id`, `paper_id`, `pdf_filename`, `pdf_page`, `text`, `chunk_index`, `char_count`, `needs_review`, and `review_flags`, plus rank and method-specific scores. PDF pages are one-based PDF page positions, not printed page numbers. Keep citation fields with the text supplied to generation.

`paper_ids=["P002"]` restricts sources; `None` searches all, an empty list matches none. `exclude_flagged=True` removes either flagged or review-needed chunks; by default these remain visible. Flags are not a complete detector of extraction errors.

Reuse instances serially: `last_timings` is mutable, not a concurrent request log. `status()` checks index validity without loading model weights. Defaults resolve data paths relative to the project, not the caller's working directory. Missing/stale data raises errors; there is no synthetic-vector fallback. Empty questions are invalid. Empty or fewer-than-k results are possible and must be handled by the generation/UI layer.

## Configuration

Use `RetrievalConfig` from `src.retrieval` when explicit settings are needed; pass it to `ResearchRetriever(config)`.

| Setting | Default | Effect |
|---|---|---|
| `bm25_candidates`, `vector_candidates` | 50 each | Independent hybrid branch limits |
| `rrf_constant` | 60 | Fusion rank weighting |
| `rerank_candidates` | 30 | Candidate budget when reranking |
| `embedding_batch_size`, `rerank_batch_size` | 32, 16 | Inference batching |
| `max_seq_length` | 512 | Token limit |
| `device` | `None` | Automatic; optionally `cpu` or `cuda` |
| `chunks_path`, `index_dir` | Project data paths | Corpus and index |
| `model_cache_dir` | Project `.cache/huggingface` | Model cache |

With reranking, top-k cannot exceed `rerank_candidates`. Without it, branch limits and filtering can still reduce returned results. BM25-only with reranking disabled needs neither model weights nor an embedding index.

Evaluation policy and approval commands live in [the label review](../eval/relevance_policy_review.md); measured results and limitations live in [the results report](retrieval_results.md).
