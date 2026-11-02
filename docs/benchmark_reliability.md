# Benchmark reliability review

Generation work was committed as `103a788` and pushed to
`origin/feature/generation-reliability`. This separate work is on
`feature/benchmark-reliability` and is intentionally uncommitted. Initial verification
was offline. A subsequently authorized live pilot stopped on a judge-validation
failure after two cases (three generation requests and two judge requests). No full
live benchmark, label rewrite, or pricing work was performed in that session. A
subsequent explicit authorization completed all 117 questions and added token-based
cost reporting: see `docs/full_benchmark_review.md` for the current results. See
`docs/live_evaluation_review.md` for the earlier pilot and stopping decision.

## Existing framework

- `eval/benchmark.py`: `run()` executes cases serially, enforces request budgets,
  saves each generation response and independent semantic result, and supports
  manifest-checked resume. `read_rows()` verifies response hashes and contracts.
- `eval/benchmark_judge.py`: `LLMJudge.evaluate()` constructs the judge prompt and
  strict Responses API JSON schema; `validate_judgment()` checks inventories,
  evidence references, and exact excerpts from the generated answer.
- `eval/benchmark_scoring.py`: `evaluate()` performs deterministic structural
  checks; `summarize()` aggregates outcomes and semantic scores.
- `eval/benchmark_data.py`: `BenchmarkCase`, `Point`, `Reference` and
  `load_benchmark()` load expected components, scopes, rubrics and source quotes.
- `eval/full_benchmark.py`: `build_sections()`, `case_info()` and `report()` produce
  readable reports and CSV from persisted results; `full_run()` is the live wrapper.
- `eval/results/final/`: the historical 105-case report, manifest, saved responses,
  judgments and summary. `eval/benchmark.v1.jsonl` contains its historical rubrics;
  `eval/benchmark.v2.jsonl` is the current 117-case dataset.

SDK retries remain disabled. The judge makes at most one request per eligible case;
there is no automatic judge repair or retry. Generation's separate citation repair
remains governed by the existing generation budget.

## Historical evidence

Saved results contain 105 records: 60 evaluated, 37 judge errors, 8 not evaluated.
All 37 recorded errors reached local `judgment_validation`, after JSON/schema
parsing. The stored diagnostics are:

| Diagnostic | Count | What is established |
|---|---:|---|
| `citations_item_ids` | 21 | Missing, duplicate or unexpected citation inventory IDs |
| `claims_verdict_or_reference` | 9 | Disallowed claim verdict or evidence reference |
| `invalid_answer_excerpt` | 3 | Claimed coverage quoted text absent from the answer |
| `citation_source_mismatch` | 2 | Supported citation did not reference its attached chunk |
| `citations_verdict_or_reference` | 1 | Disallowed citation verdict or reference |
| `points_verdict_or_reference` | 1 | Disallowed point verdict or reference |

Raw failed judge outputs were not saved, so the precise cause within combined
diagnostics cannot be recovered. In particular, the 21 inventory errors do not
prove that all 21 arose from merging citations. There is no recorded evidence that
these 37 were malformed JSON, provider failures or truncations. Future tests cover
those additional possibilities without attributing them to the historical run.

The old schema allowed all seven verdicts in all inventories, although local
validation subsequently rejected the wrong group. Its schema accepted arbitrary
item IDs and chunk IDs. The prompt described separate inventories but did not
constrain those IDs in the provider schema. These were real gaps between the
provider contract and local validation. Answer excerpts and citation entailment
remain behavioral requirements that schema constraints alone cannot guarantee.

All 60 saved successful judgments were revalidated offline using their original
v1 cases and saved generation responses; all 60 still pass. No historical score,
response, or report was overwritten.

## Changes

- `benchmark_judge.py`: separate support versus point verdict types;
  `judgment_schema()` constrains IDs and evidence references to the actual case.
  Empty inventories require empty arrays. Local checks still reject omitted or
  duplicate items, source mismatches and invalid answer excerpts. Blank reasons
  are rejected. No fuzzy quote matching, invented defaults, score substitution,
  or output repair was added.
- `LLMJudge.evaluate()`: prompt version 2.1 adds exact counts, valid chunk IDs and
  clearer citation/excerpt instructions. Refusal, incomplete response, malformed
  JSON, schema errors and semantic-contract errors are distinguished. Safe
  diagnostics retain schema error types/field paths and missing/duplicate known
  inventory IDs, excluding raw output and exception payloads. API errors remain
  separate. Missing usage stays null.
- The live version-2.0 pilot exposed `missing_answer_excerpt`: covered/partial
  verdicts could still supply an empty answer quote array in the provider schema.
  Version 2.1 uses nested `anyOf` branches to require a nonempty array for those
  verdicts while preserving empty arrays for missing/uncertain points. The original
  local checks remain authoritative. Point-failure diagnostics now record the
  known point ID, verdict and quote count without saving arbitrary failed output.
  This correction has offline coverage but has not been re-tested live.
- `evaluation_outcome()` gives explicit outcomes while retaining legacy `status`
  values for existing consumers: `successfully_judged`,
  `judge_output_validation_failure`, `judge_api_failure`, `judge_unavailable`,
  `not_evaluated`. Budget exhaustion means unavailable. Legacy saved outcomes can
  be classified from their recorded stages without rewriting the archive.
- `benchmark.py`: evaluator exceptions no longer discard completed generation
  records. The judge receives a reconstructed independent response. Generation
  errors skip judging with an explicit reason. Manifest/resume records judge prompt
  version; comparisons reject mismatched versions. Old runs remain readable but
  cannot be resumed under a changed implementation.
- `run(..., stop_on_judge_error=True)` stops the guarded pilot immediately after
  persisting a failed judgment; all runs stop on a reported judge API failure.
  Existing client request ceilings still include failed requests and repairs.
- `benchmark_scoring.py`: evaluation outcome distribution is independent of
  `response.status`. Each semantic metric has its own non-null denominator,
  including per-category/difficulty summaries. An abstention may be successfully
  judged yet have no claim-accuracy or citation-support denominator.
- `full_benchmark.py`: CSV and readable reports expose the evaluation outcome;
  report and terminal scores show the metric's actual question denominator.
- `benchmark_data.py`: reject duplicate corpus IDs, unknown scoped paper IDs and
  references outside an explicit case scope, in addition to existing exact
  location/quote checks. Dataset labels were not changed.

Scoring definitions are unchanged: factual accuracy and semantic citation support
are supported-item fractions within each judged question; completeness assigns
covered=1, partial=0.5, other verdicts=0 within each question. Summary scores remain
the mean of available question scores, **not** pooled claim-level accuracy or
accuracy across all 117 cases. Evaluator failures receive no semantic score.

Structured-output implementation follows the official
[OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses),
which also documents refusal and incomplete-output handling. Provider acceptance
and live judge behavior have not been tested during this session.

## Current dataset audit and human review

`load_benchmark()` validates all 117 cases against the 1,001-chunk/eight-paper corpus.
All 129 source-reference entries (56 distinct chunks) match exact locations and
quotes, and no reference falls outside its explicit paper scope. Explicit-scope
coverage is P001=16, P002=28, P003=29, P004=19, P005=19, P006=4, P007=4, P008=4
(comparisons contribute to multiple counts).

Every case has `human_verified=false`. Reference provenance does not prove that
the draft expected components are correct, complete or fairly answerable with
unflagged evidence. Five cases reference flagged `P002-p009-c001`: GEN-009,
GEN-012, GEN-013, GEN-044 and GEN-088. Four are labeled answerable and GEN-013 partial.
Because production excludes flagged evidence, human reviewers must determine
whether alternative unflagged passages support their required components. These
labels and references were preserved for review rather than automatically changed.

Generation still has no deterministic semantic relevance/entailment verifier.
An outside-corpus question can retrieve unrelated top-k passages; correct abstention
then depends on the model obeying the grounded prompt. Reference-integrity checks
alone cannot certify this behavior or a judge's semantic correctness.

## Verification and next step

```bash
.venv/bin/python -m pytest tests/test_benchmark_reliability.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Judge-reliability offline result before the full-run session: **288 passed, 0 failed, 0 skipped**, including 40 new
benchmark reliability regressions. Generation's pre-push result was 248 passed.
Tests exercise all six historical diagnostic categories, malformed JSON, missing
fields, bad types/enums, extra fields, refusal, truncation, absent usage, API errors,
budget exhaustion, safe diagnostics, generation/evaluation separation, preservation
through evaluator exceptions, metric denominators, historical replay and corpus
integrity. All transports used by tests are mocks.

The original authorized pilot **failed**, so the full benchmark was not started in
that session. A later authorization successfully rejudged GEN-011 with version 2.1
and completed the full run (109 valid judgments of 116 attempts). The following
recommendations describe the pre-full-run handoff; see `full_benchmark_review.md`
for the final analysis. The next step at that time was fresh controlled live validation,
not a full 117-case quality claim. Include unequal claim/citation counts, partial answers,
abstention with nonempty evidence, and comparisons; inspect each result manually.
Verify provider acceptance of the dynamic schema and measure remaining judge error
rates before authorizing the full run. Review the five flagged-reference cases and
draft rubrics before treating benchmark scores as a project result. Existing API
models, retrieval, ground-truth files and pricing logic remain unchanged.
