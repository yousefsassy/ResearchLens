# Live pilot review — 2 November 2026

This records the earlier stopped pilot. A later explicitly authorized session
verified the schema correction, completed all 117 benchmark cases, and recorded
API costs; current results are in `docs/full_benchmark_review.md`.

## Outcome and stopping decision

The authorized five-case pilot stopped after GEN-011 failed judge validation.
The full 117-case benchmark **did not run**. No additional API calls were made
after that failure; cost tracking was deferred because its prerequisites were not met.
Working branch: `feature/benchmark-reliability`. All benchmark changes remain
uncommitted and unpushed; `emna` and `main` were unchanged.

Pilot artifacts are preserved in:

`eval/results/pilot-20261102-032722/`

Files: `manifest.json`, `results.jsonl`, `summary.json`, `report.md`,
`per_question.csv`, `answers.md`, `request-budget.json`, `http-requests.json`,
and the separate `pilot_review.json`. The saved run uses judge prompt 2.0;
the post-failure offline correction is version 2.1. The original run outputs,
summary and manifest were not rewritten to claim success after the correction.
API credentials were never included in logs or artifacts. `.env` remains ignored.

## Abstention and local checks before paid calls

- All 282 pre-existing offline tests passed. Adding stop-control tests brought
  this to 285 before the live pilot; post-failure regressions bring it to 288.
- `ResearchRetriever.status()` confirms 1,001 chunks and a valid 1,001 x 384
  index, using unchanged `BAAI/bge-small-en-v1.5` and corpus fingerprint
  `3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
- `load_benchmark()` validates the unchanged 117-case dataset against that corpus.
- Real hybrid retrieval for "What was the weather in Tunis on January 1, 1995?"
  selected six unrelated passages. Mocked abstention returned `status=abstained`,
  no claims/citations, and the insufficient-evidence answer. The real LLM was not
  called for this scenario. This establishes orchestration, not semantic judgment.
- Year 1900 and a nonexistent author selected zero passages and abstained with
  zero model calls. Empty/flagged evidence, partial questions, missing-paper
  comparisons, retrieval errors and API failures have deterministic regression
  coverage. A comparison may return supported claims with explicit missing-paper
  gaps; a wholly failed retrieval returns an error rather than abstention.
- A quote-provenance check still cannot detect an irrelevant but real quote
  attached to an unsupported claim. The generator does not automatically label
  nonempty evidence sufficient, but its semantic relevance decision remains
  fallible. Reliable live out-of-domain abstention was **not established** here.

Offline local-retrieval records are in
`eval/results/local_abstention_verification.json`.

## Pilot scope, models and request controls

Selected unchanged benchmark cases:

| ID | Purpose | Result |
|---|---|---|
| GEN-005 | SelfCheckGPT without an external database | Complete; citations valid; judge valid |
| GEN-011 | Two-paper evaluation units/findings; multiple citations | Partial; citations valid after repair; judge failed |
| GEN-013 | Broad comparison with expected partial coverage | Not run after stop |
| GEN-015 | Fictional experiment requiring abstention | Not run after stop |
| GEN-017 | Out-of-domain lunar launch question | Not run after stop |

Generation used `gpt-5.4-nano`; judging used `gpt-5.4-mini`. Retrieval was hybrid
without reranking. No models, benchmark questions, labels, or generation prompts
were changed during the run.

Limits were 10 generation and 5 judge attempts. Actual HTTP POST request hooks
recorded **3 generation requests and 2 judge requests**, matching the durable
reservation ledger. Generation consisted of two initial requests and one citation
repair; there were no transport retries or extra judge repair calls.

## Observed metrics — pilot only

| Measure | Result | Denominator |
|---|---:|---|
| Planned questions processed | 2/5 (40%) | Selected pilot |
| Complete | 1 (50%) | 2 processed |
| Partial | 1 (50%) | 2 processed |
| Abstained / clarification / generation error | 0 each (0%) | 2 processed |
| Expected-status agreement | 1/2 (50%) | Draft labels |
| Structural and exact-quote citation validity | 2/2 (100%) | Released responses checked |
| Successfully judged | 1/2 (50%) | Processed cases / judge attempts |
| Judge-output validation failure | 1/2 (50%) | Judge attempts |
| Judge API error | 0/2 (0%) | Judge attempts |
| Factual accuracy | 100% | 1 successfully judged question, 2 claims |
| Completeness | 100% | 1 successfully judged question, 2 rubric points |
| Semantic citation support | 100% | 1 successfully judged question, 2 citations |
| Mean / median pipeline latency | 13.13 / 13.13 seconds | 2 processed cases |
| p95 pipeline latency | 16.14 seconds | Interpolated from only 2 cases |
| Mean retrieval / generation latency | 2.74 / 10.38 seconds | 2 processed cases |

Pipeline latency excludes judge time and includes the cold BGE initialization in
the first question. Judge latency was not separately recorded by this runner.
Two observations cannot establish stable latency percentiles or benchmark quality.
There is no successfully judged comparison score and no live abstention result.

## Failure analysis and offline correction

GEN-005 returned two supported claims and two citations. Its judge assessed both
claims, both points and both citations; the valid automated verdict is not human
ground truth.

GEN-011 initially failed exact quotation validation (`quote_mismatch`). One
generation repair produced a partial answer with four claims and six valid citation
links across both requested papers. No source-ID fabrication or wrong-paper
selection was detected structurally. Its qualification asks for evidence about
aggregation/direct human-judgment comparisons beyond the literal evaluation-unit
and findings request; this is a candidate overqualification for human review.

The GEN-011 judge response was completed and schema-parseable, but local validation
rejected it with `missing_answer_excerpt`. This diagnostic means at least one point
was marked covered/partial with an empty `answer_quotes` array. The failed raw
judgment was not persisted, so its precise point ID cannot be recovered. No score
was assigned to it and the valid generation was retained as partial, not error.

The provider schema allowed the combination that local validation rejected.
`judgment_schema()` now uses two nested `anyOf` branches: covered/partial requires
`answer_quotes` with at least one entry; missing/uncertain permits an empty list.
The prompt explicitly states the same rule. Exact answer-substring validation and
all scoring criteria remain unchanged. Future failures include the known point ID,
verdict and quote count in safe diagnostics. The official
[OpenAI structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
documents nested `anyOf` and array-length constraints. Provider acceptance and
effectiveness of the corrected schema remain **unverified live**.

The final offline suite is **288 passed, 0 failed, 0 skipped**. Regression tests
cover the failed coverage/excerpt combination, valid missing/uncertain points,
pilot stopping and preservation of the failed generation/judge outcome independently.

## Historical comparison and limitations

| Measure | Historical 105-case run | Current stopped 2-case pilot |
|---|---:|---:|
| Complete / partial / generation error | 64 / 25 / 8 | 1 / 1 / 0 |
| Abstained / clarification | 5 / 3 | 0 / 0 |
| Expected-status agreement | 72.4% | 50% |
| Structural/quote validity | 91.8% (97 checked) | 100% (2 checked) |
| Successfully judged | 60/105 | 1/2 |
| Judge-validation errors | 37 | 1 |
| Mean / p95 pipeline latency | 4.37 / 9.63 seconds | 13.13 / 16.14 seconds |

These are descriptive observations, **not** a controlled improvement/regression
comparison. Corpus size, selected questions, implementation, hardware/cold-start
conditions, and sample sizes differ. Semantic scores from one judged question are
not comparable quality evidence to the historical 60 successfully judged cases.
All 117 current rubrics remain human-unverified; five cases reference flagged
SelfCheckGPT evidence as documented in `benchmark_reliability.md`.

## Files and next step

This session changed `eval/benchmark.py` (guarded stopping),
`eval/benchmark_judge.py` (conditional quote requirement and diagnostics),
`tests/test_benchmark_reliability.py` (six new regressions), and
`docs/benchmark_reliability.md`; this review document is new. Previous uncommitted
changes in `eval/benchmark_data.py`, `eval/benchmark_scoring.py` and
`eval/full_benchmark.py` remain. Generated session artifacts are ignored by Git.

Next step: review and authorize a fresh bounded pilot of judge version 2.1.
Do not resume the failed run under changed code or start the 117-case benchmark
until a pilot validates all applicable cases, including unsupported questions.
Cost estimates were not implemented or calculated.
