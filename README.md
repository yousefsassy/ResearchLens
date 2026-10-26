# ResearchLens

ResearchLens retrieves evidence from research papers on LLM hallucinations. Member 2 provides passage retrieval and citation metadata; Phase 3 adds grounded hosted generation with traceable citations. Application/UI integration remains separate.

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

## Phase 3 generation

Generation uses **free OpenRouter models only**, with no paid fallback. See the
[generation guide](docs/generation_design.md) for setup, the Python/JSON interface,
paper comparisons, error behavior, and evaluation. The default model is
`nvidia/nemotron-3-super-120b-a12b:free`; pricing is verified before inference.

On Linux/macOS, after installing requirements in a Python 3.11 virtual environment:

```bash
cp .env.example .env
# Add your own OPENROUTER_API_KEY to the ignored .env.
.venv/bin/python scripts/ask_researchlens.py --live \
  --question "How does SelfCheckGPT detect hallucinations?" --paper-ids P002
```

This requires the agreed processed corpus, matching index, and BGE model cache.
Generation does not restore or regenerate them. Tests use mocked providers and
need no API key. The real-corpus test skips when processed chunks are absent.
The 20 generation evaluation cases are **drafts pending human review**; no live
generation accuracy or faithfulness benchmark is claimed.
