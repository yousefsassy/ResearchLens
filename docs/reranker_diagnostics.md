# Reranker diagnostics

## Findings

The original 20-question draft pilot shows lower Recall@5 and much higher latency after reranking. The [results report](retrieval_results.md) contains the four-method comparison. These findings apply to the original labels, not the expanded candidate.

All original labelled passages were already in the hybrid top 10. The cross-encoder replaced that ranking and demoted included evidence; no reversed sorting or query/passage pairing error was found. A saved top-30 replay reproduced all original top-10 rankings.

## Important cases

| Question | Original labelled passage movement | Interpretation |
|---|---|---|
| Q006 | 1 -> 15 | Exact Prompt mapping loses to other SelfCheckGPT variants |
| Q007 | 1 -> 9 | Annotation definitions lose to topical study/metric discussion |
| Q008 | 3 -> 6 | Human annotation aggregation competes with model-score discussion |
| Q012 | 2 -> 9 for assumptions | Independent scoring loses complementary evidence |
| Q017 | 7 -> 22 | Broad retrieval/hallucination matches beat architecture distinction |
| Q001, Q004 | Alternative support promoted | Original labels omitted plausible answers; review matters |

Q006/Q007/Q008/Q012 lose Recall@5; Q010 improves. Q018 has a small rank change without a recorded metric loss.

## Explanation and recommendation

Likely contributors are scientific-task mismatch, noisy extraction, broad topical matching, and independent scoring of multi-part evidence. These are hypotheses from passage inspection, not proof of the model's internal reasoning.

None of the original labelled pairs exceeds 512 tokens, so truncation does not explain their losses. Restricting the saved scores to the first 10, 20 or 30 fused candidates leaves draft Recall@5 at 0.775. A smaller pool preserves top-10 membership but does not fix top-5 ordering. Reranking accounts for about 97.3% of recorded request latency.

**Use `mode="hybrid", rerank=False` provisionally.** Approve labels before optimization. Afterwards, consider conservative RRF/CE rank combination, a measured smaller reranking budget, and controlled scoring-text experiments. Model replacement or adaptation needs more reviewed data. No changes are implemented or gains promised.

## Reproducibility

Raw pilot outputs are linked in the results report. Preserve [the diagnostic replay](../tmp/reranker_diagnostic_replay.json). Current label decisions are in [the policy review](../eval/relevance_policy_review.md); the historical evidence below intentionally retains original labels and interpretations.

<details>
<summary>Historical provenance, configuration checks, and per-question ranking evidence</summary>

## Original provenance


Inspected existing [ablation.py](../eval/ablation.py), [retrieval_eval.py](../eval/retrieval_eval.py), the retrieval orchestrator, hybrid fusion, reranker, configuration, and shared ranking helpers; read [ablation.json](../eval/results/ablation.json), [ablation.md](../eval/results/ablation.md), [retrieval.json](../eval/results/retrieval.json), the unchanged draft labels, and actual chunk text. Smoke results are unlabelled demonstrations and were not substituted for this pilot.

- Dataset: `eval\questions.draft.jsonl`; SHA-256 `2ca01e2089a2b45556f5c0cb89fda245a2bca912c73e6be345cad582dd13ca03` matches the current file.
- Corpus fingerprint: `817fa270d2b7842bd86dbdb0a5d5f89d08170eb3c5937a184851098f4cab1713` matches current chunks and the validated index.
- All 20 labels still have `review_status=pending_human_review`. No label, source chunk, ingestion module, retrieval implementation, or existing evaluation output was changed.
- Each saved per-query Recall@1/3/5/10 was independently recomputed from the frozen labels and rankings; all matched. Recall is macro-averaged fraction of labelled chunks, not any-hit accuracy. MRR is truncated at depth 10.
- The separate retrieval.json has identical aggregate recall/MRR values and a mean latency of 1.595088 s. This supports repeatability of this ranking outcome, not statistical significance or broad generalization.
- Ablation was recorded on 2026-10-25 UTC. Diagnostic replay used the same pinned models and saved configuration with network access disabled. Full replay trace: [temporary diagnostic data](../tmp/reranker_diagnostic_replay.json). No implementation change or final evaluation was performed.


## Original configuration and passage analysis


Observed configuration: 50 BM25 candidates, 50 vector candidates, RRF constant 60, best 30 fused candidates passed to the cross-encoder, batch size 16, maximum query-passage sequence length 512, and top 10 returned. The two branch lists are merged by chunk ID: 50+50 does not mean 100 distinct reranked candidates.

Without reranking the evaluator requests the best 10 fused results. With reranking it requests 30 fused candidates, scores each `(question, chunk_text)` pair, sorts by descending cross-encoder score, and returns 10. RRF scores are preserved for debugging but do not influence final ordering. This is a complete replacement of the ranking, with no safeguard for strong RRF results and no multi-passage coverage objective.

No reversed-sort or query/passage pairing error was found: the code constructs `(question, text)` pairs, pairs returned scores with the corresponding candidates, and sorts in descending score order with deterministic chunk-ID ties. Saved `retrieval_rank` records the pre-reranking rank. Model loads are lazy and reused; warmup=True excludes initialization from timed queries.

### Fixed-score candidate-pool sensitivity (diagnostic, not a new final benchmark)

The replay scores all 30 candidates once per question, then restricts those scores to candidates with original RRF ranks <=10, <=20, or <=30. It does not retrain, alter text/labels, or separately time smaller batches. The full-30 ordering exactly reproduces saved top-10 results. These numbers describe ranking sensitivity on the same draft, not held-out validation.

| RRF candidates retained before CE sorting | Draft Recall@5 | Draft Recall@10 |
|---:|---:|---:|
| 10 | 0.775 | 1.000 |
| 20 | 0.775 | 0.900 |
| 30 | 0.775 | 0.900 |

All labelled passages are in the first 10 fused candidates, so increasing pool size cannot improve candidate coverage on this pilot. Reducing the pool to 10 prevents Q006 and Q017 from disappearing beyond top 10, but this is a set-retention consequence: returning all ten candidates guarantees the original top-10 membership. It does not improve Recall@5, which stays 0.775 for every tested restriction. Higher-ranked distractors already inside the first ten are sufficient to produce all four Recall@5 failures.

Batch size 16 on 30 pairs means two batches per question. A 10-candidate setting would need fewer pair evaluations and one batch, so lower latency is plausible, but its latency reduction has not been measured here. Increasing candidates beyond 30 is not justified by these failures and would add computation.

### Truncation and latency

Across 600 replayed query-passage pairs, 18 exceed 512 tokens before truncation. None is a labelled passage. Malformed tables and equations can inflate token counts even in character-limited chunks. Truncation may affect some distractors, but it does not remove the gold evidence in the observed losses.

| Failure | Labelled chunk | Original rank | Full CE rank | CE score | Pair tokens incl. special tokens |
|---|---|---:|---:|---:|---:|
| DRAFT-Q006 | P002-p005-c002 | 1 | 15 | -1.894253 | 484 |
| DRAFT-Q007 | P002-p005-c003 | 1 | 9 | 2.838432 | 397 |
| DRAFT-Q008 | P002-p006-c001 | 3 | 6 | 2.796618 | 407 |
| DRAFT-Q012 | P003-p010-c001 | 1 | 1 | 4.491838 | 221 |
| DRAFT-Q012 | P003-p003-c003 | 2 | 9 | -3.351256 | 394 |
| DRAFT-Q017 | P005-p003-c002 | 7 | 22 | -0.579091 | 413 |

Hardware recorded by the run: CPU, 16 logical CPUs, 8 PyTorch threads, CUDA unavailable. Mean time inside reranking is 1.509879 s, approximately 97.3% of the 1.551633 s request latency; mean candidate retrieval is 0.041728 s. Hybrid-only candidate retrieval averages 0.035581 s. The p95 latency rises from 0.042155 s to 1.980584 s (47.0x). These are warm-query measurements; repeated loading/downloading is not the source of the recorded overhead.

## Why the model demotes evidence: interpretation limits

The direct mechanical cause is observable: higher cross-encoder scores replace the RRF ordering. Text inspection identifies likely failure patterns, but it cannot prove the neural model's internal causal reasoning. Domain mismatch, noisy formatting, and query emphasis below are hypotheses for controlled tests, not established causes.

The model is trained for MS MARCO passage ranking, according to its [official model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2). This does not establish suitability for scientific definitions, equations, numerical annotation schemes, and multi-part evidence questions. Domain/task mismatch is plausible here; it has not been isolated experimentally.

Observed patterns include: broad topic matches beating exact distinctions (Q006/Q007/Q017), independent scoring losing complementary evidence (Q012), fragmented equations/plot text surrounding correct evidence (Q006/Q008/Q012), and incomplete labels penalizing useful alternate support (especially Q001 and Q004). Review flags are not a complete detector: several malformed gold passages have `needs_review=False`. Excluding all flagged pages would not solve these failures and could discard good prose.

No global CE score threshold should be inferred. Scores are uncalibrated and not comparable probabilities across queries: the correct first-ranked Q011 passage has a negative CE score. Applying a threshold of zero would remove a successful answer.

## Detailed top-10 comparisons and passage diagnoses

`*` marks a proposed relevant chunk under the unchanged draft labels; unstarred means unlabelled, not proven irrelevant. The left and right columns are independent ranked lists. CE scores are those saved in ablation.json; full gold ranks beyond 10 come from the matching diagnostic replay. `Prior RRF rank` on the right shows whether a promoted candidate came from outside the original top 10. Chunk IDs encode paper and one-based PDF page.

### DRAFT-Q001: Alternative supporting passage is unlabelled.

According to the hallucination survey, how do intrinsic and extrinsic hallucinations differ?

The labelled definition P001-p005-c003 moves 1 -> 2 (CE 0.3755), below P001-p002-c002 (2.7370). The promoted passage explicitly defines intrinsic hallucination as contradiction and extrinsic hallucination as unverifiability. This looks like a draft relevance-coverage issue rather than a clearly worse answer. Do not change labels automatically; a blinded human audit must apply the same policy to all methods.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P001-p005-c003 * | 0.032787 | P001-p002-c002 | 2.737005 | 2 |
| 2 | P001-p002-c002 | 0.032258 | P001-p005-c003 * | 0.375462 | 1 |
| 3 | P001-p003-c002 | 0.031010 | P002-p001-c004 | -0.378304 | 11 |
| 4 | P001-p034-c003 | 0.030303 | P001-p002-c003 | -0.549609 | 5 |
| 5 | P001-p002-c003 | 0.029324 | P001-p003-c001 | -1.205960 | 9 |
| 6 | P001-p033-c001 | 0.028986 | P001-p033-c001 | -1.589661 | 6 |
| 7 | P001-p003-c003 | 0.028814 | P001-p022-c003 | -1.597314 | 23 |
| 8 | P001-p002-c004 | 0.028219 | P001-p003-c002 | -1.611634 | 3 |
| 9 | P001-p003-c001 | 0.026631 | P001-p011-c001 | -1.825024 | 16 |
| 10 | P001-p007-c001 | 0.026357 | P001-p007-c001 | -1.914765 | 10 |

**Label movement across the full 30-candidate replay:** P001-p005-c003: 1 -> 2 (CE 0.3755).

### DRAFT-Q002: Broad taxonomy text outranks the requested distinction.

In the survey taxonomy, what distinguishes factual contradiction from factual fabrication?

P001-p002-c003 (CE 1.0668) discusses factuality versus faithfulness, rather than directly distinguishing factual contradiction from fabrication. The two labelled passages score 0.7923 and -2.1900, moving 1 -> 2 and 3 -> 5. The fabrication definition follows entity/relation-error examples and is split from the contradiction definition. Topic similarity and fragmented context plausibly contribute; no token truncation occurs for either label.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P001-p006-c003 * | 0.032522 | P001-p002-c003 | 1.066830 | 2 |
| 2 | P001-p002-c003 | 0.031250 | P001-p006-c003 * | 0.792276 | 1 |
| 3 | P001-p006-c004 * | 0.030886 | P001-p019-c001 | -1.155133 | 17 |
| 4 | P001-p013-c001 | 0.029274 | P001-p023-c001 | -1.561320 | 21 |
| 5 | P003-p005-c004 | 0.028175 | P001-p006-c004 * | -2.190030 | 3 |
| 6 | P003-p006-c001 | 0.028043 | P001-p013-c001 | -2.366107 | 4 |
| 7 | P001-p002-c002 | 0.024923 | P002-p006-c003 | -3.924680 | 29 |
| 8 | P001-p014-c001 | 0.024826 | P001-p014-c001 | -4.556889 | 8 |
| 9 | P001-p013-c004 | 0.024052 | P002-p006-c001 | -5.106462 | 24 |
| 10 | P001-p005-c004 | 0.023960 | P001-p012-c004 | -5.343095 | 22 |

**Label movement across the full 30-candidate replay:** P001-p006-c003: 1 -> 2 (CE 0.7923); P001-p006-c004: 3 -> 5 (CE -2.1900).

### DRAFT-Q004: Topical alternatives and incomplete draft labels.

Which three broad sources of LLM hallucination organize the survey discussion of causes?

The labelled causes paragraph moves 2 -> 4 (3.3192). P001-p002-c004 remains first (4.4724) and explicitly lists data, training, and inference; P001-p003-c001 and P001-p003-c003 are also promoted ahead of the label. At least the first passage is a clear candidate alternative support. Recall@3 and reciprocal rank decline under the frozen labels even though the first result names the required causes in both runs.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P001-p002-c004 | 0.032522 | P001-p002-c004 | 4.472448 | 1 |
| 2 | P001-p007-c003 * | 0.032522 | P001-p003-c001 | 3.588221 | 10 |
| 3 | P001-p003-c002 | 0.031258 | P001-p003-c003 | 3.363198 | 4 |
| 4 | P001-p003-c003 | 0.031025 | P001-p007-c003 * | 3.319218 | 2 |
| 5 | P001-p033-c001 | 0.028372 | P001-p003-c002 | 2.888432 | 3 |
| 6 | P001-p003-c004 | 0.028125 | P001-p009-c001 | 2.651215 | 17 |
| 7 | P001-p019-c002 | 0.027864 | P001-p034-c003 | 1.479055 | 9 |
| 8 | P001-p007-c001 | 0.027253 | P001-p019-c002 | 1.354452 | 7 |
| 9 | P001-p034-c003 | 0.025989 | P001-p033-c001 | 1.329458 | 5 |
| 10 | P001-p003-c001 | 0.025729 | P001-p007-c001 | 1.291170 | 8 |

**Label movement across the full 30-candidate replay:** P001-p007-c003: 2 -> 4 (CE 3.3192).

### DRAFT-Q006: Wrong SelfCheckGPT variant promoted over the precise mapping.

How does SelfCheckGPT-Prompt convert Yes, No, and unrecognized responses into an inconsistency score?

P002-p005-c002 contains the requested Yes=0, No=1, N/A=0.5 mapping and averaging rule, but drops 1 -> 15 with CE -1.8943. P002-p004-c002 scores 1.7298 and describes BERTScore/QA-MQAG consistency, not the requested prompt mapping. The labelled chunk has malformed Markdown around the mapping, a fragmented equation, and unrelated annotation text at the end. These are plausible scoring distractions; the 484-token pair fits within 512, so lost input through truncation is not the explanation.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P002-p005-c002 * | 0.031319 | P002-p004-c002 | 1.729838 | 6 |
| 2 | P002-p004-c001 | 0.031281 | P002-p001-c003 | 1.078545 | 8 |
| 3 | P002-p003-c004 | 0.030366 | P002-p005-c001 | 0.890823 | 7 |
| 4 | P002-p013-c002 | 0.030366 | P002-p003-c004 | 0.715021 | 3 |
| 5 | P002-p008-c001 | 0.030310 | P002-p008-c004 | 0.508677 | 15 |
| 6 | P002-p004-c002 | 0.029907 | P002-p008-c003 | 0.223529 | 9 |
| 7 | P002-p005-c001 | 0.029437 | P002-p008-c001 | 0.109407 | 5 |
| 8 | P002-p001-c003 | 0.029324 | P002-p002-c002 | 0.029463 | 10 |
| 9 | P002-p008-c003 | 0.027973 | P002-p013-c002 | -0.192665 | 4 |
| 10 | P002-p002-c002 | 0.027864 | P002-p004-c001 | -0.507583 | 2 |

**Label movement across the full 30-candidate replay:** P002-p005-c002: 1 -> 15 (CE -1.8943).

### DRAFT-Q007: Study/metric discussion promoted over the annotation definitions.

Which sentence-level factuality labels and numeric values were used to annotate the SelfCheckGPT WikiBio passages?

P002-p005-c003 contains Major Inaccurate=1, Minor Inaccurate=0.5, Accurate=0, but falls 1 -> 9 (2.8384). P002-p009-c003 wins (5.2480) with limitations about the 238 WikiBio texts and sentence-level factuality, without the three requested numeric label definitions. P002-p008-c002, a performance table, ranks second. The label definitions occur after dataset and table material in the correct chunk, which may dilute the match. They are not truncated: the entire pair is 397 tokens. Several promoted candidates carry review flags, but the correct chunk does not.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P002-p005-c003 * | 0.032522 | P002-p009-c003 | 5.248034 | 3 |
| 2 | P002-p001-c003 | 0.032002 | P002-p008-c002 | 4.693536 | 7 |
| 3 | P002-p009-c003 | 0.031319 | P002-p001-c003 | 4.479967 | 2 |
| 4 | P002-p001-c002 | 0.031258 | P002-p009-c002 | 4.066414 | 8 |
| 5 | P002-p008-c003 | 0.030303 | P002-p007-c002 | 3.466294 | 12 |
| 6 | P002-p008-c001 | 0.030118 | P002-p008-c003 | 3.390747 | 5 |
| 7 | P002-p008-c002 | 0.029469 | P002-p008-c001 | 3.200244 | 6 |
| 8 | P002-p009-c002 | 0.029418 | P001-p018-c005 | 3.089387 | 11 |
| 9 | P002-p006-c001 | 0.029412 | P002-p005-c003 * | 2.838432 | 1 |
| 10 | P002-p006-c002 | 0.028783 | P002-p001-c002 | 2.224510 | 4 |

**Label movement across the full 30-candidate replay:** P002-p005-c003: 1 -> 9 (CE 2.8384).

### DRAFT-Q008: Model scoring and evaluation text confounded with human annotation aggregation.

How did the SelfCheckGPT authors obtain human passage-level factuality scores from sentence annotations?

The annotation paragraph P002-p006-c001 moves 3 -> 6 (2.7966), narrowly below P002-p008-c004 at rank 5 (2.9014), which discusses correlations and performance. The top result P002-p008-c002 (5.7008) says passage scores average sentence scores, but its surrounding context concerns model scoring and ablation. The query specifically asks about human annotations. The correct chunk includes figure labels and plot-axis noise; this is a plausible distraction, not a proven cause. P002-p008-c003 explicitly discusses averaging sentence labels for ground truth and is an additional candidate support at rank 9, illustrating why completeness needs human audit.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P002-p008-c001 | 0.032787 | P002-p008-c002 | 5.700835 | 4 |
| 2 | P002-p001-c003 | 0.032002 | P002-p001-c003 | 4.621952 | 2 |
| 3 | P002-p006-c001 * | 0.030835 | P002-p008-c001 | 4.613845 | 1 |
| 4 | P002-p008-c002 | 0.030798 | P002-p014-c001 | 3.729956 | 6 |
| 5 | P002-p008-c003 | 0.030536 | P002-p008-c004 | 2.901427 | 7 |
| 6 | P002-p014-c001 | 0.029877 | P002-p006-c001 * | 2.796618 | 3 |
| 7 | P002-p008-c004 | 0.029437 | P001-p018-c005 | 2.549348 | 11 |
| 8 | P002-p009-c002 | 0.028814 | P002-p007-c002 | 2.376889 | 9 |
| 9 | P002-p007-c002 | 0.028006 | P002-p008-c003 | 2.275755 | 5 |
| 10 | P002-p004-c001 | 0.027418 | P002-p009-c003 | 1.428066 | 13 |

**Label movement across the full 30-candidate replay:** P002-p006-c001: 3 -> 6 (CE 2.7966).

### DRAFT-Q009: Short broad explanation outranks the detailed atomic-fact rationale.

Why does FActScore evaluate atomic facts instead of assigning one factuality label to each whole sentence?

P003-p002-c001 (4.7382) is a short fragment about fine-grained factual precision and verifiable biographies. It displaces P003-p003-c002 (3.7828) from rank 1 to 2. The latter explicitly explains mixed supported/unsupported facts within a sentence and why atomic facts are the chosen unit. The short alternative is related but does not fully explain the requested sentence-versus-fact distinction. Recall@5 is unaffected.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P003-p003-c002 * | 0.032787 | P003-p002-c001 | 4.738198 | 6 |
| 2 | P003-p001-c002 | 0.031054 | P003-p003-c002 * | 3.782753 | 1 |
| 3 | P003-p010-c002 | 0.030579 | P003-p001-c002 | 3.436887 | 2 |
| 4 | P003-p006-c002 | 0.030118 | P003-p007-c003 | 2.403908 | 19 |
| 5 | P003-p003-c003 | 0.029643 | P002-p009-c003 | 2.257760 | 25 |
| 6 | P003-p002-c001 | 0.028718 | P003-p021-c001 | 1.925558 | 7 |
| 7 | P003-p021-c001 | 0.028577 | P003-p006-c002 | 1.874598 | 4 |
| 8 | P003-p005-c004 | 0.028405 | P003-p010-c002 | 1.843984 | 3 |
| 9 | P003-p003-c001 | 0.028125 | P003-p005-c004 | 1.836202 | 8 |
| 10 | P003-p001-c003 | 0.028043 | P003-p003-c003 | 1.602280 | 5 |

**Label movement across the full 30-candidate replay:** P003-p003-c002: 1 -> 2 (CE 3.7828).

### DRAFT-Q012: Independent scoring loses one half of a multi-part question.

What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its applicability?

P003-p010-c001, answering applicability limits, stays first (4.4918). P003-p003-c003, which lists all three assumptions, drops 2 -> 9 (-3.3513). Short biography text P003-p002-c001 and general limitations/precision passages move above it. The missing half begins amid a fragmented equation. Pairwise scoring optimizes each candidate independently and has no objective ensuring joint coverage of assumptions plus limitations. Both labelled inputs fit within 512 tokens.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P003-p010-c001 * | 0.032522 | P003-p010-c001 * | 4.491838 | 1 |
| 2 | P003-p003-c003 * | 0.031754 | P003-p002-c001 | -0.275039 | 4 |
| 3 | P003-p009-c003 | 0.031545 | P003-p010-c002 | -1.328107 | 5 |
| 4 | P003-p002-c001 | 0.031258 | P003-p009-c003 | -1.766166 | 3 |
| 5 | P003-p010-c002 | 0.029851 | P003-p002-c002 | -1.794647 | 10 |
| 6 | P003-p006-c002 | 0.029199 | P003-p006-c002 | -2.569553 | 6 |
| 7 | P003-p001-c002 | 0.028370 | P001-p013-c002 | -2.677916 | 8 |
| 8 | P001-p013-c002 | 0.027885 | P003-p009-c002 | -3.086151 | 11 |
| 9 | P003-p003-c004 | 0.027402 | P003-p003-c003 * | -3.351256 | 2 |
| 10 | P003-p002-c002 | 0.026861 | P003-p001-c002 | -3.402104 | 7 |

**Label movement across the full 30-candidate replay:** P003-p010-c001: 1 -> 1 (CE 4.4918); P003-p003-c003: 2 -> 9 (CE -3.3513).

### DRAFT-Q014: Distractors displace complementary truthfulness evidence at a tighter cutoff.

Why can answering No comment to every TruthfulQA question count as truthful, yet still be undesirable?

P004-p004-c002 remains first (4.4638), but the other labelled definition P004-p004-c001 moves 2 -> 4 (2.4364). A malicious-use discussion P004-p009-c002 (3.0625) and an annotation-disagreement appendix P004-p039-c001 (2.5314, original RRF rank 16) outrank it without directly answering the No comment issue. Recall@3 falls from 1 to 0.5; Recall@5 stays 1.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P004-p004-c002 * | 0.032787 | P004-p004-c002 * | 4.463759 | 1 |
| 2 | P004-p004-c001 * | 0.032258 | P004-p009-c002 | 3.062479 | 3 |
| 3 | P004-p009-c002 | 0.030798 | P004-p039-c001 | 2.531410 | 16 |
| 4 | P004-p009-c001 | 0.030118 | P004-p004-c001 * | 2.436383 | 2 |
| 5 | P004-p001-c003 | 0.027530 | P004-p009-c001 | 1.380409 | 4 |
| 6 | P004-p002-c002 | 0.026984 | P004-p004-c004 | 1.057337 | 24 |
| 7 | P004-p002-c003 | 0.026357 | P004-p002-c002 | 0.995731 | 6 |
| 8 | P004-p029-c001 | 0.025487 | P004-p007-c004 | 0.967928 | 10 |
| 9 | P004-p008-c002 | 0.025008 | P004-p039-c002 | 0.685619 | 15 |
| 10 | P004-p007-c004 | 0.024810 | P004-p008-c003 | 0.346360 | 23 |

**Label movement across the full 30-candidate replay:** P004-p004-c002: 1 -> 1 (CE 4.4638); P004-p004-c001: 2 -> 4 (CE 2.4364).

### DRAFT-Q016: Prompt description preferred to exact zero-shot restrictions.

What restrictions define the true zero-shot setting used for the TruthfulQA baselines?

P004-p005-c003 (4.3584), describing baseline prompts and generation settings, moves above P004-p005-c002 (3.1805), which lists no gradient updates, no TruthfulQA examples in prompts, and no tuning on benchmark examples. The labelled passage falls 1 -> 2. The promoted passage is adjacent and topical but lacks the full restrictions. Recall@5 remains 1.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P004-p005-c002 * | 0.032787 | P004-p005-c003 | 4.358399 | 2 |
| 2 | P004-p005-c003 | 0.032258 | P004-p005-c002 * | 3.180478 | 1 |
| 3 | P004-p004-c002 | 0.031010 | P004-p009-c001 | 0.940543 | 4 |
| 4 | P004-p009-c001 | 0.030777 | P004-p004-c002 | 0.640268 | 3 |
| 5 | P004-p002-c002 | 0.030366 | P004-p005-c001 | -0.037427 | 9 |
| 6 | P004-p004-c004 | 0.026690 | P004-p002-c002 | -0.258105 | 5 |
| 7 | P004-p005-c004 | 0.026389 | P004-p002-c003 | -1.322016 | 8 |
| 8 | P004-p002-c003 | 0.026235 | P004-p008-c002 | -1.762156 | 15 |
| 9 | P004-p005-c001 | 0.026172 | P004-p003-c003 | -2.193857 | 12 |
| 10 | P004-p004-c001 | 0.025344 | P004-p022-c002 | -2.200114 | 22 |

**Label movement across the full 30-candidate replay:** P004-p005-c002: 1 -> 2 (CE 3.1805).

### DRAFT-Q017: Broad RAG/hallucination relevance beats the architecture comparison.

In Retrieval Augmentation Reduces Hallucination in Conversation, how do RAG-Sequence and RAG-Token differ in their use of retrieved documents?

P005-p003-c002 explicitly contrasts RAG-Sequence and RAG-Token, but drops 7 -> 22 (CE -0.5791). The first result P005-p005-c002 (3.8129) discusses retrieval effectiveness and hallucination, not that comparison. P001-p026-c002, a broad RAG discussion in the survey, is promoted to second (3.3287). The long paper title in the question may emphasize broad retrieval/hallucination terms over the requested distinction; this is a hypothesis requiring a controlled rewrite test. The labelled pair has 413 tokens and is not truncated. Recall@5 was already zero before reranking; this case worsens Recall@10 and MRR.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P005-p005-c002 | 0.031778 | P005-p005-c002 | 3.812855 | 1 |
| 2 | P005-p006-c002 | 0.030579 | P001-p026-c002 | 3.328717 | 8 |
| 3 | P005-p007-c005 | 0.029877 | P005-p007-c005 | 3.177205 | 3 |
| 4 | P005-p009-c001 | 0.029211 | P005-p019-c003 | 3.071143 | 9 |
| 5 | P005-p001-c001 | 0.028624 | P005-p001-c001 | 3.036682 | 5 |
| 6 | P005-p004-c001 | 0.028531 | P005-p006-c003 | 3.012696 | 10 |
| 7 | P005-p003-c002 * | 0.027972 | P005-p009-c001 | 2.864715 | 4 |
| 8 | P001-p026-c002 | 0.027971 | P005-p004-c001 | 2.636083 | 6 |
| 9 | P005-p019-c003 | 0.027799 | P005-p006-c002 | 2.102824 | 2 |
| 10 | P005-p006-c003 | 0.027693 | P004-p012-c001 | 1.368201 | 19 |

**Label movement across the full 30-candidate replay:** P005-p003-c002: 7 -> 22 (CE -0.5791).

### DRAFT-Q018: Small rank movement with no reported metric regression.

How does Fusion-in-Decoder combine retrieved documents, and is its retriever updated during training in the baseline described by the conversation paper?

P005-p003-c003 stays first and P005-p004-c003 moves 2 -> 3. Both relevant passages remain within top 3; Recall@1/3/5/10 and reciprocal rank are unchanged. Included for completeness because one labelled passage is demoted, not because the question has a measured accuracy regression.

| Rank | Before: RRF chunk | RRF score | After: CE chunk | CE score | Prior RRF rank |
|---:|---|---:|---|---:|---:|
| 1 | P005-p003-c003 * | 0.032787 | P005-p003-c003 * | 4.756768 | 1 |
| 2 | P005-p004-c003 * | 0.032002 | P005-p002-c001 | 0.979644 | 9 |
| 3 | P005-p008-c004 | 0.030550 | P005-p004-c003 * | 0.566662 | 2 |
| 4 | P005-p008-c005 | 0.029710 | P005-p005-c002 | -0.181518 | 5 |
| 5 | P005-p005-c002 | 0.029236 | P005-p016-c004 | -0.952028 | 23 |
| 6 | P005-p018-c004 | 0.029199 | P005-p019-c002 | -1.413586 | 8 |
| 7 | P005-p003-c002 | 0.028043 | P005-p003-c002 | -1.800684 | 7 |
| 8 | P005-p019-c002 | 0.027365 | P005-p008-c004 | -1.941384 | 3 |
| 9 | P005-p002-c001 | 0.026387 | P005-p001-c003 | -2.746985 | 16 |
| 10 | P005-p003-c004 | 0.025873 | P005-p003-c004 | -4.245215 | 10 |

**Label movement across the full 30-candidate replay:** P005-p003-c003: 1 -> 1 (CE 4.7568); P005-p004-c003: 2 -> 3 (CE 0.5667).


</details>
