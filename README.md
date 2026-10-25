# ResearchLens

ResearchLens retrieves evidence from research papers on LLM hallucinations. Member 2 provides passage retrieval and citation metadata; Member 3 will add answer generation and the UI.

## Start here

Run commands from this directory (the inner `ResearchLens` folder), using Python 3.11:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Preserve the existing `data/processed/chunks.jsonl` and matching `data/indexes/`. For a new checkout without an index, follow the [build and integration guide](docs/retrieval_design.md). Recommended usage explicitly sets `mode="hybrid", rerank=False`; the public API default still enables reranking.

## Handoff map

| Location | Purpose |
|---|---|
| `src/ingestion/`, `data/raw/` | Member 1 pipeline and original PDFs; preserved |
| `src/retrieval/`, `scripts/` | Retrieval API, index builder, query and smoke tools |
| `tests/` | Automated behavior checks |
| [Design](docs/retrieval_design.md) | Setup, API example, models and configuration |
| [Results](docs/retrieval_results.md) | Verified index, tests, saved preliminary comparison |
| [Reranker diagnostics](docs/reranker_diagnostics.md) | Failure analysis and preserved diagnostic evidence |
| [Label review](eval/relevance_policy_review.md) | Current per-question relevance proposals and approval steps |
| `eval/results/` | Saved pilot and smoke outputs; preserve |
| `tmp/` | Diagnostic replay and PDF inspection images; preserve as supporting evidence |

The current corpus has five papers and 638 chunks. Thirty papers remains a project scope target, not the current dataset.

All 20 evaluation questions remain pending human approval. No approved dataset or final benchmark is available. The original draft and reviewed candidate serve different provenance purposes and are both retained.

## Transfer and checks

Git ignores `data/processed/`, `data/indexes/`, `eval/results/` and `.cache/`. A Git checkout alone does not contain these local artifacts. Transfer the agreed corpus, matching index, and saved results separately; transfer cached models or allow first-use downloads. Keep `tmp/reranker_diagnostic_replay.json` with the diagnostic report. No files were deleted or moved for this handoff.

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```
