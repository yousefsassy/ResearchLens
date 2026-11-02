# Retrieval results

## Dataset and index

| Paper | PDF pages | Chunks |
|---|---:|---:|
| P001 | 58 | 290 |
| P002 | 14 | 54 |
| P003 | 25 | 96 |
| P004 | 39 | 106 |
| P005 | 20 | 92 |
| P006 | 59 | 251 |
| P007 | 16 | 61 |
| P008 | 19 | 51 |

Current corpus: **8 papers, 250 PDF pages, 1,001 chunks**, including 104 flagged chunks across 32 pages. The previous index covered 638 x 384 normalized float32 values; the expanded corpus requires a rebuild. Until that rebuild, hybrid and vector retrieval will reject the stale index, while BM25 remains usable.

Corpus fingerprint: `3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.

Earlier notes reported 612 chunks, 71 flagged pages and 245 flagged chunks, but those processed outputs were absent and could not be reproduced. The unchanged ingestion code generated the current corpus using PyMuPDF 1.28.2 and PyMuPDF4LLM 0.3.4 legacy extraction; that mode reported ignoring `use_ocr`. Extraction differences can change boundaries and flags. Fewer flags do not establish better extraction. The manifest now records title, authors, year, category, source URL, licence, filename, version, and page count for all eight papers. Chunks must be regenerated to carry this metadata; the index must then be rebuilt because the corpus fingerprint changes.

Historical 638-chunk CPU index build: 128.114 s; valid-index reuse: 0.059823 s. Saved files totalled 996,308 bytes. These observations are not new handoff measurements.

## Tests

Current suite: **216 passed** after the metadata and corpus expansion changes.

Tests cover validation, index integrity/alignment, ranking, filtering, fusion, reranking, lazy loading, citation preservation, evaluation calculations and the ablation CLI. Neural unit tests use fakes; the corpus integration test uses real BM25. Historical real-model smoke results demonstrate all four configurations, not retrieval accuracy.

Public imports, index validation, and CLI help were checked. No algorithm, configuration, metric, corpus, or label changes were made during this documentation cleanup.

## Preliminary comparison

The saved 2026-10-25 pilot uses **20 original draft questions**, not the expanded reviewed candidate. Labels were not human approved. CPU measurements use warm queries; initialization is excluded.

| Method | Recall@5 | MRR@10 | Mean seconds |
|---|---:|---:|---:|
| BM25 | 0.825 | 0.702083 | 0.006727 |
| Vector | 0.700 | 0.595536 | 0.026668 |
| Hybrid RRF | 0.900 | 0.732619 | 0.035590 |
| Hybrid + rerank | 0.775 | 0.572222 | 1.551633 |

Source: [ablation.json](../eval/results/ablation.json). Original dataset SHA-256: `2ca01e2089a2b45556f5c0cb89fda245a2bca912c73e6be345cad582dd13ca03`.

Recall is macro-average fraction of labelled chunks retrieved, not answer accuracy or any-hit rate. JSON also records Recall/Hit@1/3/5/10, truncated MRR, latency distributions, per-query rankings, configuration, model revisions, dataset/corpus fingerprints and environment.

Use **hybrid with reranking explicitly disabled** provisionally. This small draft pilot does not establish general superiority. See [reranker diagnostics](reranker_diagnostics.md) for failure explanations.

## Evidence locations

| Artifact | Purpose |
|---|---|
| [ablation.json](../eval/results/ablation.json), [ablation.md](../eval/results/ablation.md) | Original four-method pilot |
| [retrieval.json](../eval/results/retrieval.json) | Separate original reranked pilot |
| [smoke.json](../eval/results/smoke.json), [bm25_smoke.json](../eval/results/bm25_smoke.json) | Unlabelled execution and citation checks |
| [Draft](../eval/questions.draft.jsonl) | Unchanged original labels |
| [Candidate](../eval/questions.reviewed_candidate.jsonl) | 76 proposed positive pairs: 42 Full, 34 Partial |
| [Policy review](../eval/relevance_policy_review.md) | Current decisions and approval workflow |
| [Historical audit](../eval/relevance_audit.md) | Source excerpts, PDF checks, pooled rankings and earlier reasoning |

The first historical vector and reranker smoke calls included model initialization. Do not interpret their timings as steady-state benchmarks. All raw results remain unchanged.

## Limitations and remaining work

- All 20 questions remain pending human approval. No approved dataset exists; candidate-label scores have not been measured.
- Human review must settle question scope, partial evidence, alternative answers, and damaged source text. Then freeze labels and run the existing ablation to a new output path, as documented in the policy review.
- Chunk Recall does not measure complete answer-component coverage. Overlapping and alternative passages count separately; keep Full/Partial annotations for future coverage analysis.
- Specialized terminology, truncation, noisy equations/tables, and topical distractors can affect ranking. Review flags are incomplete.
- The pilot is too small for reliable model selection or final quality claims. A larger reviewed development/held-out collection is future evaluation work, not a blocker to API integration.
- No measured 50% optimization claim is made. Any future optimization must compare fixed labels/settings and held-out quality; earlier project targets were at least 50% latency reduction with at most 0.02 absolute Recall@5 loss.
- Member 3 still needs answer generation, citation display, and handling of insufficient or unreliable evidence.
