# Relevance policy review - pending human approval

Supersedes the policy and proposed positives in [the historical audit](relevance_audit.md). This reviews existing judgments and current chunk text for all 20 questions, not a new exhaustive corpus audit. Original questions and draft labels are unchanged.

## Policy

- **Full:** independently answers the entire question.
- **Partial:** directly supports a requested component, but not the entire question.
- **Irrelevant:** no direct requested support.
- Binary positives are Full plus substantive Partial. Missing other components does not disqualify useful evidence.
- Exclude merely topical/incidental text and orphan or damaged fragments with no independently useful evidence. Overlap alone is not a reason to exclude.
- Accept accurate secondary sources when the question permits them; preserve baseline/variant distinctions.
- JSON retains separate Full/Partial IDs, substantive flags, reasons, and required components. Per-chunk component coverage still needs human annotation before any future coverage metric.

Existing chunk Recall@k weights positive IDs equally, including alternatives. It does not measure whether every answer component is covered. More alternative positives can lower Recall@k even when an answer is sufficient. Metric definitions remain unchanged.

## Proposed positives

### DRAFT-Q001

According to the hallucination survey, how do intrinsic and extrinsic hallucinations differ?

| Positive chunk | Type | Reason |
|---|---|---|
| P001-p005-c003 | Full | Defines both contradiction of source context and unverifiability; retain. |
| P001-p002-c002 | Full | Complete alternative definition of both categories in the introduction. |

<details>
<summary>Borderline exclusions</summary>

P001-p005-c004: Orphan overlap omits the category name, so it cannot independently supply the requested named contrast.

</details>

### DRAFT-Q002

In the survey taxonomy, what distinguishes factual contradiction from factual fabrication?

| Positive chunk | Type | Reason |
|---|---|---|
| P001-p006-c003 | Partial | Complete contradiction facet: real-world-grounded facts that contradict reality; needs fabrication evidence. |
| P001-p006-c004 | Partial | Explicit fabrication definition and contradiction examples, but no standalone definition of the named factual-contradiction category. Credit fabrication; c003 supplies the explicit contradiction definition. |
| P001-p007-c001 | Partial | Elaborates the unverifiable and overclaim side of fabrication, complementary to contradiction evidence. |

### DRAFT-Q003

What three subtypes of faithfulness hallucination does the survey identify, and what does each mean?

| Positive chunk | Type | Reason |
|---|---|---|
| P001-p007-c002 | Full | Names and explains all three subtypes. |
| P001-p002-c003 | Full | Complete alternative: instruction, context, and logical inconsistencies with meanings. |
| P001-p006-c003 | Partial | Names all three subtypes; meanings still require other evidence. |
| P001-p008-c004 | Partial | Explains the named context-inconsistency subtype through unsupported gender attribution. |

<details>
<summary>Borderline exclusions</summary>

P001-p006-c002: Flattened examples lack the named subtype associations required for usable taxonomy evidence. P001-p007-c001: Introduces dimensions but omits explicit subtype names and their associations.

</details>

### DRAFT-Q004

Which three broad sources of LLM hallucination organize the survey discussion of causes?

| Positive chunk | Type | Reason |
|---|---|---|
| P001-p007-c003 | Full | Explicit data, training, inference organization of Section 3. |
| P001-p002-c004 | Full | Explicit alternative listing of the three contributing stages. |
| P001-p003-c001 | Full | Explicitly links corresponding causes to data-, training-, and inference-related approaches. |
| P001-p019-c002 | Full | Explicitly links the same three categories to Hallucination Causes, Section 3. |
| P001-p010-c003 | Partial | Explicitly identifies training as one of the three hallucination causes. |

### DRAFT-Q005

How can SelfCheckGPT detect possible hallucinations without an external knowledge database?

| Positive chunk | Type | Reason |
|---|---|---|
| P002-p002-c002 | Full | Explains knowledge-consistency premise, divergence of hallucinations, sampling, and no external database. |
| P001-p014-c003 | Full | Survey describes Manakul et al.'s same-prompt sampling and factual-consistency detection (reference 205). |
| P002-p001-c002 | Full | Abstract gives the complete zero-resource sampling/consistency explanation. |
| P002-p001-c003 | Full | Figure caption describes sentence comparisons against stochastic samples without an external database. |
| P002-p003-c003 | Full | Explicit zero-resource scheme comparing sampled responses for consistency. |
| P002-p003-c004 | Full | Explains same-query stochastic sampling and consistency-based hallucination scoring. |
| P002-p004-c002 | Full | Explains repeated versus absent information in samples as the factuality signal. |
| P002-p004-c003 | Partial | Explains sample-based n-gram probability estimation as a concrete detection mechanism. |
| P002-p005-c001 | Partial | Explains contradiction scoring between generated samples and the assessed sentence. |
| P002-p007-c003 | Partial | Explains low token frequency in generated samples as a non-factuality signal. |

<details>
<summary>Borderline exclusions</summary>

P002-p009-c002: Restates zero-resource availability without explaining a detection mechanism.

</details>

### DRAFT-Q006

How does SelfCheckGPT-Prompt convert Yes, No, and unrecognized responses into an inconsistency score?

| Positive chunk | Type | Reason |
|---|---|---|
| P002-p005-c002 | Full | Yes=0, No=1, other responses=N/A=0.5; final score averages samples (Equation 11). |

<details>
<summary>Borderline exclusions</summary>

P002-p005-c001: Support-checking task description supplies none of the requested numerical conversions. P002-p013-c002: Output semantics provide no numeric conversion or aggregation rule.

</details>

### DRAFT-Q007

Which sentence-level factuality labels and numeric values were used to annotate the SelfCheckGPT WikiBio passages?

| Positive chunk | Type | Reason |
|---|---|---|
| P002-p005-c003 | Full | All three sentence annotation labels, definitions, and numeric values. |
| P002-p006-c001 | Full | Figure 3 repeats all three labels and values: 1, 0.5, 0. |
| P002-p005-c004 | Partial | Independently gives Accurate=0. Do not credit the orphan 0.5 fragment as another mapping. |

<details>
<summary>Borderline exclusions</summary>

P002-p006-c002: Binary evaluation grouping supplies none of the three annotation label-value mappings.

</details>

### DRAFT-Q008

How did the SelfCheckGPT authors obtain human passage-level factuality scores from sentence annotations?

| Positive chunk | Type | Reason |
|---|---|---|
| P002-p006-c001 | Full | Explicitly averages sentence-level human labels in each passage. |
| P002-p008-c003 | Full | Explicitly describes averaging sentence labels into less-noisy ground truths. |

<details>
<summary>Borderline exclusions</summary>

P002-p005-c004: Sentence-level adjudication is a different operation from passage-level aggregation. P002-p008-c001: Model-predicted score averaging does not establish human-label aggregation. P002-p008-c002: Model-score averaging is a different target from human-label aggregation.

</details>

### DRAFT-Q009

Why does FActScore evaluate atomic facts instead of assigning one factuality label to each whole sentence?

| Positive chunk | Type | Reason |
|---|---|---|
| P003-p003-c002 | Full | Explains mixed supported/unsupported facts and shortcomings of sentence labels. |
| P002-p009-c003 | Full | Explicitly links mixed factual/non-factual sentences to Min et al.'s atomic-fact evaluation. |
| P003-p001-c002 | Full | Mixed true/false information makes binary judgement inadequate; atomic decomposition follows. |
| P003-p001-c003 | Full | Footnote explicitly says one sentence has multiple facts and mixed support. |

<details>
<summary>Borderline exclusions</summary>

P003-p002-c001: General precision description supplies no sentence-versus-fact rationale. P003-p003-c003: Overlap names a fine-grained unit but omits the sentence-level problem; no independent rationale for the contrast.

</details>

### DRAFT-Q010

How does the Retrieve-to-LM variant of the FActScore estimator decide whether an atomic fact is supported?

| Positive chunk | Type | Reason |
|---|---|---|
| P003-p006-c003 | Full | Retrieved passages plus atomic fact plus True/False prompt; probability or generated-text decision. |
| P003-p017-c001 | Partial | Supplies evidence retrieval: five GTR passages from the entity page; no LM decision rule. |
| P003-p018-c004 | Partial | Explicitly supplies the True/False prompting component; no retrieval or decision extraction. |

<details>
<summary>Borderline exclusions</summary>

P003-p006-c002: General decomposition and validation overview supplies no variant-specific decision component.

</details>

### DRAFT-Q011

Why can FActScore miss incomplete answers, and which additional statistics do its authors recommend reporting?

| Positive chunk | Type | Reason |
|---|---|---|
| P003-p010-c002 | Full | Complete reason and both recommended supplementary statistics. |
| P003-p003-c003 | Partial | Complete why facet: precision excludes recall and rewards fewer facts or abstention; lacks reporting recommendation. |
| P003-p010-c003 | Full | Repeats both recommendations and Table 6 illustrates a supported biography omitting essential information. |
| P003-p004-c003 | Partial | Explicitly observes that abstention can improve factual precision; supports the incompleteness problem, not the reporting recommendation. |

<details>
<summary>Borderline exclusions</summary>

P003-p009-c003: Future work on recall supplies neither the incompleteness explanation nor the reporting recommendation.

</details>

### DRAFT-Q012

What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its applicability?

| Positive chunk | Type | Reason |
|---|---|---|
| P003-p003-c003 | Partial | All three assumptions: undebatable support, equal importance, nonconflicting/nonoverlapping knowledge. |
| P003-p010-c001 | Partial | Explicit applicability limits for debatable facts and conflicting sources. |
| P003-p004-c001 | Partial | Explains objective/specific facts and source self-consistency as conditions satisfying assumptions 1 and 3. |
| P003-p016-c003 | Partial | Explains ambiguity, inference and subjectivity causing disagreement, illustrating debatability limitation. |
| P003-p006-c001 | Partial | Explicit inconsistent Wikipedia award claims illustrate the problem with contradictory support evidence; no complete assumption list. |

<details>
<summary>Borderline exclusions</summary>

P003-p002-c001: Domain selection alone is not an explicit assumption or limitation explanation. P003-p003-c004: Defines source-relative support without stating the requested assumptions or explaining a conflicting-source failure.

</details>

### DRAFT-Q013

What are the imitative falsehoods that TruthfulQA questions are designed to elicit?

| Positive chunk | Type | Reason |
|---|---|---|
| P004-p004-c003 | Full | Explicit definition: false statements with high likelihood on training distribution. |
| P001-p008-c003 | Full | Explains learned misinformation and increased probability of repeating false statements. |
| P001-p018-c003 | Full | Survey explicitly defines TruthfulQA's target as misleading responses frequent in training data. |
| P004-p001-c001 | Full | Abstract links human misconceptions to false answers learned through imitation. |
| P004-p001-c004 | Full | Defines false answers incentivized by training objective and high training-distribution likelihood. |
| P004-p008-c002 | Full | Explains the LM objective and repetition of human false claims. |
| P004-p002-c001 | Partial | Caption explicitly identifies model answers mimicking human falsehoods and misconceptions; no training-distribution explanation. |

<details>
<summary>Borderline exclusions</summary>

P004-p007-c002: Discussion of non-imitative syntax errors supplies no independent positive definition.

</details>

### DRAFT-Q014

Why can answering No comment to every TruthfulQA question count as truthful, yet still be undesirable?

| Positive chunk | Type | Reason |
|---|---|---|
| P004-p004-c001 | Partial | Complete truthfulness facet: avoid asserting falsehood, allowing noncommittal answers. |
| P004-p004-c002 | Full | No comment is perfectly truthful, but useful answers must reduce uncertainty and be informative. |
| P004-p006-c004 | Partial | Explains informativeness and calls No comment uninformative; lacks the no-false-claims explanation for why abstention is truthful. |
| P004-p008-c003 | Partial | Explicitly states truthfulness permits noncommittal responses; complementary truthfulness facet. |

<details>
<summary>Borderline exclusions</summary>

P004-p008-c004: Orphan overlap loses the subject connecting noncommittal responses to the truthfulness criterion. P004-p028-c003: A tagged example supplies neither the truthfulness criterion nor a reason universal refusal is undesirable. P004-p035-c001: A scored example gives a verdict without either requested explanation. P004-p036-c001: Damaged score-column associations prevent reliable standalone use of the relevant illustration; do not credit PDF-only repairs.

</details>

### DRAFT-Q015

How were the filtered and unfiltered subsets of TruthfulQA constructed, and how many questions did each contain?

| Positive chunk | Type | Reason |
|---|---|---|
| P004-p004-c003 | Full | Complete construction of filtered 437 and unfiltered 380 questions. |
| P004-p004-c004 | Partial | Complete unfiltered facet: 380 additional questions without target-model testing. |
| P004-p024-c001 | Partial | Complete count facet and filtering target, but omits precise exclusion procedure. |
| P001-p018-c003 | Partial | Correct counts and filtering of GPT-3-correct answers. Credit those components only; non-adversarial is not a precise definition of unfiltered construction. |

### DRAFT-Q016

What restrictions define the true zero-shot setting used for the TruthfulQA baselines?

| Positive chunk | Type | Reason |
|---|---|---|
| P004-p005-c002 | Full | No gradient updates, no benchmark prompt examples, no prompt/hyperparameter tuning on benchmark examples. |

<details>
<summary>Borderline exclusions</summary>

P004-p004-c002: Mentions zero-shot but supplies no defining restriction. P004-p005-c003: Describes dissimilar trivia prompts, not an explicit restriction on benchmark examples, tuning, or updates.

</details>

### DRAFT-Q017

In Retrieval Augmentation Reduces Hallucination in Conversation, how do RAG-Sequence and RAG-Token differ in their use of retrieved documents?

| Positive chunk | Type | Reason |
|---|---|---|
| P005-p003-c002 | Full | Sequence independently generates per document; Token marginalizes per token. |
| P005-p009-c001 | Partial | Direct simultaneous-document contrast with RAG-Sequence, without exact token-level formula. |
| P005-p019-c002 | Partial | Explicitly contrasts joint RAG-Token document use and separate RAG-Sequence use, but lacks token-level marginalization detail. |
| P005-p019-c003 | Partial | Complete sequence facet: separate documents/generations; complementary to Token evidence. |
| P005-p006-c002 | Partial | Explicit RAG-Token fusion across documents supports the Token component; no Sequence comparison. |

<details>
<summary>Borderline exclusions</summary>

P005-p013-c002: Different RAG-Turn variants with incomplete formulas do not supply the standard Sequence/Token distinction.

</details>

### DRAFT-Q018

How does Fusion-in-Decoder combine retrieved documents, and is its retriever updated during training in the baseline described by the conversation paper?

| Positive chunk | Type | Reason |
|---|---|---|
| P005-p003-c003 | Full | Independent document/context encoding; concatenate representations for decoder; retriever fixed. |
| P005-p004-c003 | Full | Summarizes fused independent encoder outputs and untrained retriever, then distinguishes FiD-RAG. |
| P005-p009-c001 | Partial | Explicit joint-document use by the FiD architecture supports combination; no independent-encoding detail or fixed-baseline-retriever evidence. |

<details>
<summary>Borderline exclusions</summary>

P005-p008-c002: RAG-trained retriever results do not establish the original baseline mechanism or training status.

</details>

### DRAFT-Q019

Why does the conversation paper propose DPR-Poly reranking, and how does it increase interaction between a dialogue context and candidate documents?

| Positive chunk | Type | Reason |
|---|---|---|
| P005-p003-c004 | Full | Dot-product limitation, scalable reranking subset, candidate-aware Poly-encoder attention. |
| P005-p002-c001 | Partial | Explicit motivation: finer-grained context-candidate scoring for improved performance; no attention or reranking procedure. |

<details>
<summary>Borderline exclusions</summary>

P005-p003-c005: Substantive mechanism belongs to PolyFAISS rather than DPR-Poly. P005-p008-c003: Performance results alone do not explain the design rationale or interaction mechanism. P005-p008-c005: Best-performing configuration does not explain design rationale or mechanism.

</details>

### DRAFT-Q020

Which datasets were used in the conversation retrieval study, and what makes their unseen evaluation splits different from the training data?

| Positive chunk | Type | Reason |
|---|---|---|
| P005-p004-c004 | Full | Both datasets; unseen topics or movies not discussed during training. |
| P005-p002-c002 | Partial | Names both datasets; complete identity facet, lacks precise split definition. |
| P005-p013-c003 | Full | Detailed alternative: WoW unseen topics and custom CMU_DoG two-movie holdout. |
| P005-p004-c003 | Partial | Independently identifies Wizard of Wikipedia as a study dataset; no second dataset or split definition. |

<details>
<summary>Borderline exclusions</summary>

P005-p006-c004: Unseen-performance discussion does not independently identify datasets or define held-out splits.

</details>

## Decisions requiring approval

- Q002: c003 and c004 are complementary Partial definitions; page-7 elaboration remains Partial. c004 is no longer graded Full.
- Q014: page-4 c002 is Full; page-4 c001 and page-8 c003 support truthfulness. Page-6 c004 supports informativeness and is now Partial. Incidental tagged examples remain excluded.
- Q018: page-3 c003 and page-4 c003 each independently answer both parts and remain Full alternatives. Page-9 c001 adds Partial combination evidence, not fixed-retriever evidence.
- Q015: accept accurate count/filtering components from the survey, without treating its non-adversarial gloss as the full unfiltered construction definition.

## Approval and subsequent ablation

1. Review scope, requested components, positives, and exclusions against source pages in the original audit. Apply the same policy to every method; resolve ambiguous component boundaries.
2. Record actual reviewer, date, and decisions. All current labels are pending human approval, not verified.
3. Freeze a separate eval/questions.approved.jsonl with approved metadata, dataset hash/version, and matching corpus fingerprint. Preserve old labels and results.
4. Validate schema and IDs again. load_questions() does not enforce human approval; schema validity is not approval.
5. After approval, run the existing four-method ablation from the project directory with a new output path:

```powershell
.venv\Scripts\python.exe eval/ablation.py --dataset eval/questions.approved.jsonl --output eval/results/ablation.approved.json
```

This runs BM25, Vector, Hybrid RRF, and Hybrid + rerank. Keep corpus, models, configuration, and warmup consistent. Changed-label scores are not directly comparable to old-label scores as evidence of model improvement. No benchmark was run or accuracy reported here.

## Status

All 20 questions remain pending human approval: **76 positive pairs (42 Full, 34 substantive Partial)**. The policy review added 17 positives and changed two Full grades to Partial; none were removed. Exact prior IDs and grade changes remain in [candidate metadata](questions.reviewed_candidate.jsonl).

This formatting cleanup changes no labels. PDFs, ingestion, retrieval, models, evaluation scripts, original draft, and benchmark results remain unchanged.
