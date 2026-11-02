# Full 117-question live benchmark — 2 November 2026

## Completion and reproducibility

Completed **117/117** unchanged cases on `feature/benchmark-reliability`.
No files were committed or pushed; `emna` and `main` were unchanged.

Artifacts: `eval/results/full-20261102-034056/` contains `summary.json`,
`per_question.csv`, `answers.md`, `report.md`, `results.jsonl`, `manifest.json`,
`request-budget.json`, `api-usage.jsonl`, `api-costs.json`, `tests.txt`, `tests.json`,
`verification_checks.json`, and `environment.json`. Historical evaluations were
preserved. New generated artifacts remain ignored by Git.

Runtime configuration:

- Eight papers, 250 pages, 1,001 chunks; normalized 1,001 x 384 NumPy vector index.
- Embeddings: `BAAI/bge-small-en-v1.5`, revision
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Corpus fingerprint:
  `3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
- Dataset: `eval/benchmark.v2.jsonl`, all 117 original IDs and draft rubrics.
- Retrieval: BM25 + BGE + RRF, flagged evidence excluded, reranking disabled.
- Generation: `gpt-5.4-nano`, 2,048 output tokens, 12,000 context characters,
  180-second timeout, generation prompt 1.8.
- Judge: `gpt-5.4-mini`, 6,000 output tokens, judge prompt/schema 2.1.
- Actual reported models: `gpt-5.4-nano-2026-03-17` and
  `gpt-5.4-mini-2026-03-17`. No substitutions or paid fallback models.
- Maximum 234 generation requests, 117 judge requests, $18 estimated API budget.
  Transport retries disabled; at most one generation citation-repair request.
- Isolated invalid model/judge outputs were retained as distinct errors, not
  treated as incorrect generated answers. Stop controls covered provider failures,
  estimated budget exhaustion and three consecutive judge-validation failures.

The existing CLI was invoked with its implemented arguments:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
.venv/bin/python eval/full_benchmark.py run --live \
  --output eval/results/full-20261102-034056 \
  --max-requests 234 --judge-model gpt-5.4-mini --judge-budget 117 --budget-usd 18
```

The invocation used the same `main()` argument parser from Python to assign the
timestamped directory. Generation/judge prompts, labels and retrieval settings
were frozen throughout inference. Post-run edits only improved cost/report
presentation, tests and documentation. The manifest records the implementation
hash at run time and dataset/corpus hashes; it was not rewritten after those edits.

## Corrected judge verification

Reused GEN-011's saved generated answer from the previous failed pilot and sent
it directly to judge version 2.1: **one judge request, zero generation requests**.
The result validated successfully: accuracy 1.0, completeness 0.5, semantic
citation support 1.0. `missing_answer_excerpt` did not recur in this verification
or anywhere in the full run. This demonstrates the tested correction, not a
guarantee that every future judge output will be valid.

Verification artifacts: `eval/results/judge-verification-20261102-033844/`.
That request cost an estimated **$0.01412475** and is separate from benchmark costs.

## Generation outcomes

| Outcome | Count | Percentage of 117 |
|---|---:|---:|
| Complete | 79 | 67.52% |
| Partial | 27 | 23.08% |
| Abstained | 7 | 5.98% |
| Needs clarification | 3 | 2.56% |
| Generation error | 1 | 0.85% |

Expected-status agreement: **92/117 = 78.63%** against draft acceptable statuses.
This is not factual accuracy. There were 25 status disagreements.

Abstention works in several live unsupported cases: GEN-017 (lunar launch),
GEN-103 (fictional Neptune score), GEN-104 (vaccine dosing) and GEN-105 (private
credentials) abstained. GEN-016 and GEN-019 also abstained. GEN-093 abstained
instead of explicitly correcting a false premise, so its expected status was not
met. GEN-015 acknowledged that the fictional dataset was absent but still returned
an unrelated research finding as partial. Thus semantic abstention remains fallible.
Earlier real-retrieval/mocked-generation checks also verified the weather question
and empty year/author filters without extra paid calls.

## Citations, judging and answer quality

- Combined benchmark structural/quote validation: **106/107 = 99.07%**. The
  denominator includes 106 released factual answers plus GEN-020's rejected
  structured output. Its failure does not establish that a bad quote was published.
- Independently revalidated released answers: **106/106**. Their **305/305 citation
  links** pass source-ID, metadata, contiguous quote and applicable comparison
  citation checks. There are 233 released claim blocks.
- Exact source provenance does not prove entailment or responsiveness. The judge
  flagged semantic citation problems on four questions despite valid quotations.
- Judge attempts: **116**; GEN-020's generation error skipped judging.
- Successful judgments: **109/117 = 93.16%** dataset coverage, or **109/116 = 93.97%**
  of attempted judgments. Judge-validation failures: **7/116 = 6.03%**. Judge API
  failures: **0**. Generation errors and judge failures were never merged.
- Mean per-question factual accuracy: **95.63% over 101 successfully judged,
  answer-bearing questions**. Eight other successful judgments have no factual
  claims and therefore no accuracy denominator.
- Mean completeness: **85.32% over 109 successfully judged questions**.
- Mean semantic citation support: **98.04% over 101 successfully judged,
  citation-bearing questions**.

These are unverified automated judgments and macro averages of question scores,
not pooled claim counts or quality measured across all 117 questions. Every case
still has `human_verified=false`.

The dataset category `comparison` has 12 cases: 3 complete, 9 partial; 11 were
successfully judged. On those 11, mean accuracy is 91.67%, completeness 67.42%,
and semantic citation support 95.67%. Other categories also contain cross-paper
questions, so this category is not a census of every comparison-like request.

## Latency and request accounting

Pipeline latency across all 117 outcomes: **mean 3.80 s, median 2.98 s, p95 8.24 s**.
Mean retrieval time: **0.092 s**; mean generation time including repairs: **3.705 s**.
These figures include zero-inference clarification cases and first-call BGE loading,
and exclude semantic judge latency. SDK judge requests averaged **3.05 s** each.

Requests: **114 initial generation + 12 repairs + 116 judge = 242**. Every request
has a returned response ID and usage record, and totals match the durable request
ledger and per-question attempt counts. The separate verification adds one judge
request, making this session **243 requests**, including **117 judge requests**.

Initial citation validation found eight quote mismatches and four missing-paper
synthesis citation failures. Six repairs passed the complete validator; six still
had invalid claims and released only a strictly validated subset as partial.
No invalid claim from those repaired drafts was published. GEN-020 was a separate
structured-generation contract failure and did not enter citation repair.

## Concrete failure analysis

| Cases | Finding | Evidence and practical consequence |
|---|---|---|
| GEN-009, GEN-038 | Relevant passage not selected | Neither selected its draft reference chunk; the n-gram rationale and author limitations were incompletely answered. One GEN-009 reference is flagged, complicating evaluation. Reference recall is diagnostic, not proof that no alternate support exists. |
| GEN-087 | Comparison misses one requested definition | TruthfulQA evidence was present; the survey's referenced instruction-inconsistency passage was not selected. The answer described only one failure type and returned partial. |
| GEN-116 | Intra-paper variant coverage gap | Selected the chunk preceding the draft 2-step CoVe reference but not that reference itself. It explained joint execution and declared 2-step information missing. Its limitations also introduced unasked findings/limitations dimensions; scope inference needs review. |
| GEN-015, GEN-018 | Unsupported request receives unrelated facts | Both acknowledged evidence gaps but returned partial claims outside the requested fictional experiment/damaged equation. This fails the intended abstention/scope policy. |
| GEN-070, GEN-075, GEN-081, GEN-096 | Repair still had quote mismatches | Invalid claims were removed; remaining independently validated claims were explicitly partial. |
| GEN-013, GEN-084 | Repair still had synthesis coverage failures | One-paper synthesis did not satisfy both-paper citation rules and was removed. |
| GEN-020 | Generation contract failure | Returned `invalid_model_output`, no answer/claims, no judge call. Current sanitized logs do not identify the precise invalid field. |
| GEN-014, GEN-061, GEN-101 | Invalid judge answer excerpts | Rejected covered-point excerpts did not occur in rendered `response.answer`; two are clarification cases. Their generated statuses were preserved. |
| GEN-086, GEN-088, GEN-089, GEN-115 | Judge citation-source mismatch | A supported-citation judgment omitted the attached chunk. Rejected without assigning semantic scores. Raw failed judgments were not retained, limiting further reconstruction. |
| GEN-010, GEN-074 | Judge reasoning needs human review | Some reasons call a claim contradicted while acknowledging support for its narrower wording, or treat an incomplete list as contradiction. Valid judge JSON is not evidence that the judgment itself is correct. |

No paper-scope violations were detected by structural checks. That does not prove
every claim attributes the correct facts or that the selected context is sufficient.
Twelve cases were flagged for missing rubric components, six for factual issues and
four for semantic citation issues; these counts overlap and need human adjudication.

Five draft cases still reference flagged `P002-p009-c001`: GEN-009, GEN-012,
GEN-013, GEN-044 and GEN-088. Labels and references were preserved. Human review
must resolve extraction sensitivity, acceptable alternate evidence, unjustified
partial labels, compound rubric points and possible judge false positives.

## API usage and cost

Rates were verified against the official model pages on 2 November 2026:
[nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano) and
[mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
Per million input/cached-input/output tokens: nano **$0.20/$0.02/$1.25**;
mini **$0.75/$0.075/$4.50**. Cached tokens are included in total input and priced
at the discounted rate rather than added again. No pricing assumption was applied
to missing cached-token records from historical benchmarks.

| Category | Model | Requests | Input | Cached input | Output | Estimated USD |
|---|---|---:|---:|---:|---:|---:|
| Initial generation | nano | 114 | 897,244 | 197,120 | 30,569 | $0.18217845 |
| Citation repair | nano | 12 | 112,307 | 21,504 | 4,852 | $0.02465568 |
| Semantic judging | mini | 116 | 803,274 | 0 | 49,181 | $0.82377000 |
| Total benchmark | — | 242 | 1,812,825 | 218,624 | 84,602 | **$1.03060413** |

Generation including repair: **$0.20683413**, or **$0.00176781 per processed user
question** (117-question denominator, including errors/clarifications). Judge cost
including failed-attempt overhead: **$0.00755752 per successfully judged question**
(109 denominator). Total evaluation: **$0.00880858 per processed question**.

At the same usage, question mix, repair frequency, cached-input fraction and prices,
production generation without judging projects to **$0.17678 for 100 questions**
and **$17.67813 for 10,000 questions**. These are extrapolations, not volume/cache
guarantees. Evaluation judging is not included in production inference costs.

Including the separate judge verification, this session totals **$1.04472888**.
All figures estimate standard text-token charges from actual returned usage;
they are not a billing statement or a query of the professor's account balance.
No requests were made solely to obtain cost information.

## Historical comparison

| Metric | Historical 105 cases | Current 117 cases |
|---|---:|---:|
| Complete / partial / error | 64 / 25 / 8 | 79 / 27 / 1 |
| Abstained / clarification | 5 / 3 | 7 / 3 |
| Expected-status agreement | 72.38% | 78.63% |
| Combined structural/quote validation | 91.75% (97 checked) | 99.07% (107 checked) |
| Successfully judged | 60/105 (57.14%) | 109/117 (93.16%) |
| Judge-validation errors | 37 | 7 |
| Factual accuracy, judged non-null scores | 94.55% | 95.63% |
| Completeness, successful judgments | 90.42% | 85.32% |
| Semantic citation support, judged non-null scores | 96.36% | 98.04% |
| Mean / median / p95 pipeline latency | 4.37 / 3.68 / 9.63 s | 3.80 / 2.98 / 8.24 s |

This is descriptive, not a controlled model-quality experiment. The corpus,
dataset, generation implementation, evaluator contract, coverage and execution
conditions changed. Higher scores do not by themselves establish better model
quality; lower completeness also requires rubric/coverage-aware interpretation.

## Checks, changes and recommended next work

Post-run verification recomputed every summary metric from 117 saved records,
validated response/case hashes and original question IDs, rechecked 106 released
answers and 305 quote links, matched all 242 usage records to attempts, loaded all
117 CSV rows, and scanned artifacts for the actual API key with zero matches.
The offline suite passes **300 tests, zero failures/skips** after cost/report tests.

New this session: `eval/api_costs.py` and `tests/test_api_costs.py`; changed
`eval/benchmark.py` for optional usage accounting, request classification and safe
stops, and `eval/full_benchmark.py` for the budget option and visible cost reporting.
The generation interface and public response contract are unchanged. Existing
uncommitted benchmark/judge/data/scoring/report changes remain for review.
No dependencies, embeddings, vector storage, paper metadata or ground truth changed.

Complete uncommitted file list: `eval/benchmark.py`, `eval/benchmark_data.py`,
`eval/benchmark_judge.py`, `eval/benchmark_scoring.py`, `eval/full_benchmark.py`,
`eval/api_costs.py`, `tests/test_benchmark_reliability.py`, `tests/test_api_costs.py`,
`docs/benchmark_reliability.md`, `docs/live_evaluation_review.md`, and this document.

Recommended next work: human-review the unsupported and comparison failures;
separate genuine retrieval gaps from overqualified partial answers; improve
status-aware judge excerpt handling and citation-source adherence; adjudicate
suspected judge false positives and draft rubrics before publishing quality claims.
The full run is complete; there is no reason to rerun it to obtain costs.
