# ResearchLens — Answers and Sources

These are the original model responses, not rewritten by the reporter.

## GEN-001 — Which three broad sources of LLM hallucination organize the survey discussion of causes?

**Status:** complete  
**Category:** general · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The survey organizes the causes of LLM hallucinations into three broad sources: Data, Training, and Inference stages. [C1]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c003`) — primarily categorized into three key aspects: (1) _Data_ (§3.1), (2) _Training_ (§3.2), and (3) _Inference_ (§3.3).

---

## GEN-002 — According to the hallucination survey, how do intrinsic and extrinsic hallucinations differ?

**Status:** complete  
**Category:** general · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

Intrinsic hallucinations are model outputs that directly conflict with the provided source context, whereas extrinsic hallucinations involve outputs that cannot be verified using the provided source context or external knowledge bases. [C1]

The survey characterizes extrinsic hallucinations as neither supported by nor directly contradicting the available information, making the output unverifiable and potentially misleading. [C2]

In conventional NLG settings, hallucinations are categorized into intrinsic hallucination (generated output contradicts the source content) and extrinsic hallucination (generated output cannot be verified from the source). [C3]

### Citations

- **[C1]** P001, PDF p. 5 (`P001-p005-c003`) — Specifically, _intrinsic hallucinations_ pertain to the model outputs that directly conflict with the provided source context. On the other hand, _extrinsic hallucinations_ involve outputs that cannot be verified using the provided source context or external knowledge bases.
- **[C2]** P001, PDF p. 5 (`P001-p005-c003`) — This means the generated text is neither supported by nor directly contradicts the available information, rendering the output unverifiable and potentially misleading.
- **[C3]** P001, PDF p. 2 (`P001-p002-c002`) — These hallucinations are categorized into two types: _intrinsic hallucination_, where the generated output contradicts the source content, and _extrinsic hallucination_, where the generated output cannot be verified from the source.

---

## GEN-003 — What three subtypes of faithfulness hallucination does the survey identify, and what does each mean?

**Status:** complete  
**Category:** general · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

The survey identifies three subtypes of faithfulness hallucinations: instruction inconsistency, context inconsistency, and logical inconsistency. [C1] [C2]

Instruction inconsistency refers to outputs that deviate from a user’s directive, i.e., unintentional misalignment with non-malicious user instructions. [C3]

Context inconsistency points to instances where the output is unfaithful with the user’s provided contextual information (i.e., it contradicts the context). [C4]

Logical inconsistency underscores when LLM outputs exhibit internal logical contradictions, including inconsistencies among reasoning steps and between the steps and the final answer. [C5]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c002`) — From this perspective, we categorize three subtypes of faithfulness hallucinations:
- **[C2]** P001, PDF p. 2 (`P001-p002-c003`) — This category is further subdivided into instruction inconsistency, where the content deviates from the user’s original instruction; context inconsistency, highlighting discrepancies from the provided context; and logical inconsistency, pointing out internal contradictions within the content.
- **[C3]** P001, PDF p. 7 (`P001-p007-c002`) — **Instruction inconsistency** refers to the LLM’s outputs that deviate from a user’s directive. While some deviations might serve safety guidelines, the inconsistencies here signify unintentional misalignment with non-malicious user instructions.
- **[C4]** P001, PDF p. 7 (`P001-p007-c002`) — **Context inconsistency** points to instances where the LLM’s output is unfaithful with the user’s provided contextual information.
- **[C5]** P001, PDF p. 7 (`P001-p007-c002`) — **Logical inconsistency** underscores when LLM outputs exhibit internal logical contradictions, often observed in reasoning tasks. This manifests as inconsistency both among the reasoning steps themselves and between the steps and the final answer.

---

## GEN-004 — What hallucination detection approaches are described in this corpus?

**Status:** error  
**Category:** general · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — Citation references or supporting quotes failed validation.

---

## GEN-005 — How can SelfCheckGPT detect possible hallucinations without an external knowledge database?

**Status:** complete  
**Category:** paper_specific · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT is a sampling-based approach that detects whether responses generated by LLMs are hallucinated or factual by sampling multiple responses and measuring information consistency between them. [C1] [C2]

SelfCheckGPT does not require an external database because it only leverages sampled responses. [C3]

SelfCheckGPT uses multiple informational-consistency variants—including BERTScore, question-answering, n-gram, NLI, and LLM prompting—to determine whether statements are factual or hallucinated. [C4]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c002`) — In this paper, we propose SelfCheckGPT, a sampling-based approach that can detect whether responses generated by LLMs are hallucinated or factual.
- **[C2]** P002, PDF p. 2 (`P002-p002-c002`) — By sampling multiple responses from an LLM, one can measure information consistency between the different responses and determine if statements are factual or hallucinated.
- **[C3]** P002, PDF p. 2 (`P002-p002-c002`) — Since SelfCheckGPT only leverages sampled responses, it has the added benefit that it can be used for black-box models, and it requires no external database.
- **[C4]** P002, PDF p. 2 (`P002-p002-c002`) — Five variants of SelfCheckGPT for measuring informational consistency are considered: BERTScore, question-answering, _n_ -gram, NLI, and LLM prompting.

---

## GEN-006 — What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its applicability?

**Status:** complete  
**Category:** paper_specific · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore assumes that whether or not an atomic fact is supported by a knowledge source is undebatable. [C1]

FActScore assumes that every atomic fact in a response has an equal weight of importance. [C2]

FActScore assumes that pieces of information in the knowledge source do not conflict or overlap with each other, so it is not applicable when facts are more nuanced, open-ended, and debatable or when a knowledge source frequently conflicts with itself. [C3] [C4]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c003`) — This definition assumes the following:  1. Whether or not an atomic fact is supported by _C_ is undebatable.
- **[C2]** P003, PDF p. 3 (`P003-p003-c003`) — 2. Every atomic fact in _Ay_ has an equal weight of importance, following Krishna et al. (2023).
- **[C3]** P003, PDF p. 3 (`P003-p003-c003`) — 3. Pieces of information in _C_ do not conflict or overlap with each other.
- **[C4]** P003, PDF p. 10 (`P003-p010-c001`) — FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).

---

## GEN-007 — What are the imitative falsehoods that TruthfulQA questions are designed to elicit?

**Status:** complete  
**Category:** paper_specific · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA questions are designed to elicit imitative falsehoods, defined as false answers that have high likelihood on a model’s training distribution. [C1]

Imitative falsehoods are false statements with high likelihood on the training distribution. [C2]

TruthfulQA consists of a test set of 817 questions written by the authors and designed to elicit imitative falsehoods. [C3]

### Citations

- **[C1]** P004, PDF p. 1 (`P004-p001-c004`) — We call such false answers _imitative falsehoods_ . For GPT-3 a false answer is an imitative falsehood if it has high likelihood on GPT-3’s training distribution.
- **[C2]** P004, PDF p. 4 (`P004-p004-c003`) — In particular, the questions test a weakness to imitative falsehoods: false statements with high likelihood on the training distribution.
- **[C3]** P004, PDF p. 4 (`P004-p004-c002`) — TruthfulQA consists of a test set of 817 questions and is intended only for the zero-shot setting. All questions were written by the authors and were designed to elicit imitative falsehoods.

---

## GEN-008 — Why can FActScore miss incomplete answers, and which additional statistics do its authors recommend reporting?

**Status:** complete  
**Category:** paper_specific · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore can miss incomplete answers because it does not consider factual recall (the coverage of information in a generation) and focuses only on factual precision. [C1]

The authors note that FACTSCORE does not penalize models that abstain too frequently or generate fewer facts, which can be unfair given an inherent precision–recall trade-off, and this can allow incomplete answers to score without being penalized. [C2]

They recommend reporting FACTSCORE together with the % of abstention and the average number of atomic facts. [C3]

### Citations

- **[C1]** P003, PDF p. 10 (`P003-p010-c002`) — For instance, FACTSCORE does not consider factual recall: the coverage of information in a generation.
- **[C2]** P003, PDF p. 10 (`P003-p010-c002`) — FACTSCORE does not penalize a model that abstains from responding too frequently or generates fewer facts, which can be unfair since there is an inherent trade-off between precision and recall.
- **[C3]** P003, PDF p. 10 (`P003-p010-c002`) — recommend reporting FACTSCORE together with the % of abstention and the average number of atomic facts (as we did in Section 4.3).

---

## GEN-009 — What limitations do the SelfCheckGPT authors identify?

**Status:** partial  
**Category:** paper_specific · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT with BERTScore/QA, using self-samples, can yield comparable or even better performance than when using the reference passage. [C1]

SelfCheckGPT with n-gram shows a large performance drop when using the WikiBio passages instead of self-samples, attributed to the fact that the WikiBio reference text alone is not sufficient to train an n-gram model. [C2]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c003`) — First,  SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage.
- **[C2]** P002, PDF p. 8 (`P002-p008-c003`) — Second, SelfCheckGPT with _n_ -gram shows a large performance drop when using the WikiBio passages instead of self-samples. This failure is attributed to the fact that the WikiBio reference text alone is not sufficient to train an _n_ -gram model.

### Limitations

- The supplied evidence does not include an explicit list or section of limitations identified by the authors; it only contains observations about performance drops and a note that the method is no longer zero-resource when retrieval is available.

---

## GEN-010 — Compare the methodologies of SelfCheckGPT and FActScore.

**Status:** error  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — Citation references or supporting quotes failed validation.

---

## GEN-011 — Compare the evaluation units and findings of SelfCheckGPT and FActScore.

**Status:** complete  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheckGPT reports that its methods correlate far better with human judgments than the other baselines, and that SelfCheckGPT-Prompt is the best-performing method with the highest Pearson correlation of 78.32. [C1]

SelfCheckGPT reports that SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage. [C2]

FACTSCORE reports human-evaluation-based automated scoring and estimates its FACTSCORE close to ground truth, with an automated metric that has less than a 2% error rate. [C3]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c004`) — Our results in Table 2 and Figure 6 show that all SelfCheckGPT methods correlate far better with human judgements than the other baselines, including the grey-box probability and entropy methods. SelfCheckGPT-Prompt is the best-performing method, achieving the highest Pearson correlation of 78.32.
- **[C2]** P002, PDF p. 8 (`P002-p008-c003`) — Our findings in Table 3 show the following. First, SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage.
- **[C3]** P003, PDF p. 1 (`P003-p001-c001`) — Since human evaluation is costly, we also introduce an automated model that estimates FACTSCORE using retrieval and a strong language model, with less than a 2% error rate.

### Limitations

- > The question asks for “evaluation units and findings,” but the provided evidence does not include a direct, explicit statement of SelfCheckGPT’s evaluation unit (e.g., whether it is sentence-level vs passage-level) in the same way FACTSCORE’s unit is described; therefore only findings are compared here.

---

## GEN-012 — Compare the limitations of SelfCheckGPT and FActScore.

**Status:** partial  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore is not applicable when the facts are more nuanced, open-ended, and debatable or when the knowledge source frequently conflicts within itself. [C1]

FActScore may not be suitable for human-written text that is nuanced and includes intentional or implicit deception. [C2]

FActScore’s estimator is not perfect for individual judgments, and the best variant depends on how close a generation is to human-written text and its linguistic complexity. [C3]

FActScore leaves “a more holistic evaluation of factuality” for future work and notes that FACTSCORE focuses on factual precision rather than factual recall or broader factuality. [C4]

SelfCheckGPT does not leverage anything beyond sampled responses, requiring no external database, which constrains it to an approach based on sampling multiple responses for information consistency. [C5]

### Citations

- **[C1]** P003, PDF p. 10 (`P003-p010-c001`) — Due to the assumptions made in Section 3.1,  FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).
- **[C2]** P003, PDF p. 10 (`P003-p010-c001`) — Moreover, FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional or implicit deception.
- **[C3]** P003, PDF p. 10 (`P003-p010-c001`) — **Limitation in our estimator.** While our estimator closely approximates humans and provides consistent ranking over a large set of LMs, it is not perfect in individual judgments, and the best variant depends on the degree of how close a generation is to human-written text and its linguistic complexity.
- **[C4]** P003, PDF p. 10 (`P003-p010-c002`) — **Beyond factual precision.** FACTSCORE focuses on factual precision—whether each piece of information in a generation is factually supported by a reliable source of knowledge—which is only one aspect of the broader factuality problem.
- **[C5]** P002, PDF p. 2 (`P002-p002-c002`) — Since SelfCheckGPT only leverages sampled responses, it has the added benefit that it can be used for black-box models, and it requires no external database.

### Limitations

- The supplied evidence does not contain an explicit “limitations” section for SelfCheckGPT (e.g., constraints, failure modes, or discussion of when it may not work), so only a general constraint about requiring no external database is supported for SelfCheckGPT.
- Because SelfCheckGPT lacks explicit limitation text in the provided excerpts, a direct side-by-side comparison of SelfCheckGPT’s limitations vs. FActScore’s limitations cannot be fully supported by the evidence provided.

---

## GEN-013 — Compare methods, findings, and limitations of SelfCheckGPT and FActScore.

**Status:** partial  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT is a sampling-based approach that detects whether responses generated by LLMs are hallucinated or factual by measuring information consistency across multiple sampled responses, and it has five variants for measuring informational consistency (BERTScore, question-answering, n-gram, NLI, and LLM prompting). [C1] [C2] [C3]

SelfCheckGPT’s results report that all SelfCheckGPT methods correlate far better with human judgements than the other baselines, and that SelfCheckGPT-Prompt is the best-performing method with a highest Pearson correlation of 78.32. [C4] [C5]

FActScore introduces an automated model that estimates FACTSCORE by breaking a generation into atomic facts and validating each against a knowledge source, and it is designed to estimate factual precision when human evaluation is costly. [C6] [C7] [C8]

FActScore’s limitations include that it is not applicable when facts are nuanced, open-ended, and debatable or when the knowledge source frequently conflicts with each other, and that it may not be suitable for human-written text that is nuanced and includes intentional or implicit deception. [C9] [C10]

FActScore focuses its experiments on people biographies and Wikipedia because many LMs can generate biographies with objective and specific facts and Wikipedia has a high coverage for them. [C11]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c002`) — In this paper, we propose SelfCheckGPT, a sampling-based approach that can detect whether responses generated by LLMs are hallucinated or factual.
- **[C2]** P002, PDF p. 2 (`P002-p002-c002`) — By sampling multiple responses from an LLM, one can measure information consistency between the different responses and determine if statements are factual or hallucinated.
- **[C3]** P002, PDF p. 2 (`P002-p002-c002`) — Five variants of SelfCheckGPT for measuring informational consistency are considered: BERTScore, question-answering, _n_ -gram, NLI, and LLM prompting.
- **[C4]** P002, PDF p. 8 (`P002-p008-c004`) — Our results in Table 2 and Figure 6 show that all SelfCheckGPT methods correlate far better with human judgements than the other baselines, including the grey-box probability and entropy methods.
- **[C5]** P002, PDF p. 8 (`P002-p008-c004`) — SelfCheckGPT-Prompt is the best-performing method, achieving the highest Pearson correlation of 78.32.
- **[C6]** P003, PDF p. 6 (`P003-p006-c002`) — Human evaluation of factual precision is costly ($4 per generation) (Bohnet et al., 2022; Krishna et al., 2023) because validating every atomic fact against a large knowledge source is time-consuming, and one generation contains many (26–41) atomic facts.
- **[C7]** P003, PDF p. 6 (`P003-p006-c002`) — In this context, we introduce a model that **estimates** FACTSCORE. This estimator takes a set of  generations and automatically computes a FACTSCORE, and can be applied to any LMSUBJ.
- **[C8]** P003, PDF p. 6 (`P003-p006-c002`) — Our estimator of FACTSCORE first breaks a generation into a series of atomic facts and then validates each against the given knowledge source.
- **[C9]** P003, PDF p. 10 (`P003-p010-c001`) — Due to the assumptions made in Section 3.1, FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).
- **[C10]** P003, PDF p. 10 (`P003-p010-c001`) — Moreover, FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional or implicit deception.
- **[C11]** P003, PDF p. 9 (`P003-p009-c003`) — All of our experiments focus on people biographies and Wikipedia, because many LMs can generate biographies with objective and specific facts (rather than subjective and vague ones) and Wikipedia has a high coverage for them.

### Limitations

- The provided evidence for SelfCheckGPT does not include an explicit limitations section or specific discussion of limitations, so the requested comparison aspect 'limitations' for SelfCheckGPT cannot be fully supported.
- The provided evidence set includes only one numeric performance result for SelfCheckGPT (Pearson correlation 78.32) and does not provide parallel FActScore numeric findings beyond high-level statements; therefore, a detailed comparison of 'findings' across the two methods cannot be fully supported with the supplied evidence.

---

## GEN-014 — What does the MissingStudy paper conclude?

**Status:** needs_clarification  
**Category:** insufficient · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** judge_error

### Answer

*No answer returned.*

---

## GEN-015 — What did SelfCheckGPT report for an experiment on the fictional ResearchLens-2099 dataset?

**Status:** partial  
**Category:** insufficient · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT’s reported findings for Table 3 state that “SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage.” [C1]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c003`) — Our findings in Table 3 show the following. First, SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage.

### Limitations

- The provided evidence does not mention any experiment on a fictional ResearchLens-2099 dataset, so the specific findings for that dataset cannot be determined from the supplied text.

---

## GEN-016 — What exact score did FActScore report on the fictional TestSet-Zeta-2099?

**Status:** abstained  
**Category:** insufficient · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** evaluated

### Answer

I don't have sufficient usable evidence to answer this question.

### Limitations

- The provided evidence from P003 does not mention any fictional dataset named “TestSet-Zeta-2099” or report a FACTSCORE for it, so the exact score for that dataset cannot be determined from the supplied text.

---

## GEN-017 — What launch procedure does this corpus prescribe for a lunar mining vehicle?

**Status:** abstained  
**Category:** insufficient · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** evaluated

### Answer

I don't have sufficient usable evidence to answer this question.

### Limitations

- The supplied evidence excerpts do not mention any lunar mining vehicle or any launch procedure/corpus prescription for such a vehicle, so the requested information cannot be determined from the provided sources.

---

## GEN-018 — What numerical conclusion follows from the damaged equation on SelfCheckGPT PDF page 3?

**Status:** partial  
**Category:** extraction_sensitive · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT-Prompt is reported as the best-performing method, achieving the highest Pearson correlation of 78.32. [C1]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c004`) — SelfCheckGPT-Prompt is the best-performing method, achieving the highest Pearson correlation of 78.32.

### Limitations

- The prompt asks about a “damaged equation on SelfCheckGPT PDF page 3,” but the supplied evidence excerpts reference pages 4 and 5 and 8 rather than page 3, and none contain the damaged equation needed to infer a numerical conclusion from it. Therefore, the specific numerical conclusion tied to the damaged equation on page 3 cannot be determined from the provided evidence.

---

## GEN-019 — What exact model-column values appear in SelfCheckGPT Table 4 on PDF page 9?

**Status:** abstained  
**Category:** extraction_sensitive · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** evaluated

### Answer

I don't have sufficient usable evidence to answer this question.

### Limitations

- The provided evidence does not include SelfCheckGPT Table 4 from PDF page 9, nor any extractable text showing the model-column values for that table. The available excerpts reference Figure 6, Table 3, and other sections, but not Table 4 or page 9 model-column entries.

---

## GEN-020 — What model names appear in the damaged Table 5 headers on SelfCheckGPT PDF page 13?

**Status:** error  
**Category:** extraction_sensitive · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — The model returned an invalid structured answer.

---

## GEN-021 — According to the survey, what distinguishes entity-error from relation-error hallucination?

**Status:** partial  
**Category:** definitions · **Difficulty:** easy  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

Entity-error hallucination refers to situations where the generated text contains erroneous entities. [C1]

Relation-error hallucination refers to instances where the generated text contains wrong relations between entities. [C2]

### Citations

- **[C1]** P001, PDF p. 6 (`P001-p006-c004`) — - **Entity-error** **hallucination** refers to the situations where the generated text of LLMs contains erroneous entities.
- **[C2]** P001, PDF p. 6 (`P001-p006-c004`) — - **Relation-error hallucination** refers to instances where the generated text of LLMs contains wrong relations between entities.

### Limitations

- The survey’s example distinguishing entity-error vs relation-error is present in the evidence, but the specific quotation for the telephone inventor example was not available from the provided chunk text needed to validate the original example claim exactly. As a result, I cannot provide an evidence-validated statement that explicitly maps the telephone vs light-bulb examples to each error type using the original requested claim structure.

---

## GEN-022 — What does factual fabrication mean in the survey's taxonomy?

**Status:** complete  
**Category:** definitions · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the survey’s taxonomy, “Factual Fabrication” refers to instances where the LLM’s output contains facts that are unverifiable against established real-world knowledge. [C1]

In the survey’s taxonomy, “Factual Fabrication” is divided into “unverifiability hallucination” and “overclaim hallucination.” [C2]

“Unverifiability hallucination” refers to statements that are entirely non-existent or cannot be verified using available sources. [C3]

### Citations

- **[C1]** P001, PDF p. 6 (`P001-p006-c004`) — **Factual Fabrication** refers to instances where the LLM’s output contains facts that are unverifiable against established real-world knowledge.
- **[C2]** P001, PDF p. 6 (`P001-p006-c004`) — This can be further divided into _unverifiability_ _hallucination_ and _overclaim hallucination_ .
- **[C3]** P001, PDF p. 7 (`P001-p007-c001`) — - **Unverifiability** **hallucination** pertains to statements that are entirely non-existent or cannot be verified using available sources.

---

## GEN-023 — In the survey, when is a deviation from a user instruction considered instruction inconsistency?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

In the survey, instruction inconsistency is defined as cases where the LLM’s outputs deviate from a user’s directive. [C1]

Such deviations are considered unintentional misalignment specifically with non-malicious user instructions. [C2]

For example, if the user’s actual intention is translation, but the LLM erroneously deviates from the instruction and performs question-answering, this is instruction inconsistency. [C3]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c002`) — **Instruction inconsistency** refers to the LLM’s outputs that deviate from a user’s directive.
- **[C2]** P001, PDF p. 7 (`P001-p007-c002`) — While some deviations might serve safety guidelines, the inconsistencies here signify unintentional misalignment with non-malicious user instructions.
- **[C3]** P001, PDF p. 7 (`P001-p007-c002`) — As described in Table 1, the user’s actual intention is translation, However, the LLM erroneously deviated from the user’s instruction and performed a question-answering task instead.

---

## GEN-024 — How does the survey distinguish logical inconsistency within reasoning steps from inconsistency with a final answer?

**Status:** complete  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The survey distinguishes logical inconsistency by defining it as internal logical contradictions that can occur either among the reasoning steps themselves or between the steps and the final answer. [C1]

When the logical inconsistency is between reasoning steps, the survey describes cases where an earlier reasoning step is correct but later steps become inconsistent with that reasoning chain. [C2]

When the logical inconsistency is between the reasoning steps and the final answer, the survey describes cases where the reasoning step is correct but the final answer contradicts the reasoning chain. [C3]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c002`) — **Logical inconsistency** underscores when LLM outputs exhibit internal logical contradictions, often observed in reasoning tasks. This manifests as inconsistency both among the reasoning steps themselves and between the steps and the final answer.
- **[C2]** P001, PDF p. 6 (`P001-p006-c003`) — The first step correctly isolates the term with x to get 2x = 8. However, **the next step inaccurately divides** **8 by 2 to yield a result of x = 3**, which is inconsistent with the earlier reasoning.
- **[C3]** P001, PDF p. 7 (`P001-p007-c002`) — For example, as shown in Table 1, while the reasoning step of dividing both sides of the equation by 2 is correct, the final answer of x=4 is inconsistent with the reasoning chain, leading to an incorrect result.

---

## GEN-025 — Which two kinds of training data does the survey discuss, and what capabilities do they provide?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The survey discusses two primary components of training data: pre-training data and alignment data. [C1]

Pre-training data provides general capabilities and factual knowledge, while alignment data teaches the model to follow user instructions and align with human preferences. [C2]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c003`) — Data for training LLMs are comprised of two primary components: (1) pre-training data, through which LLMs acquire their general capabilities and factual knowledge [388], and (2) alignment data, which teach LLMs to follow user instructions and align with human preferences [322].
- **[C2]** P001, PDF p. 7 (`P001-p007-c003`) — Data for training LLMs are comprised of two primary components: (1) pre-training data, through which LLMs acquire their general capabilities and factual knowledge [388], and (2) alignment data, which teach LLMs to follow user instructions and align with human preferences [322].

---

## GEN-026 — What three data-related mechanisms can cause hallucinations according to the survey?

**Status:** complete  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

According to the survey, data-related hallucinations generally emerge as a byproduct of misinformation, biases, and knowledge gaps, which are fundamentally rooted in the pre-training data. [C1]

In the survey’s detailed description of hallucination from data, the three aspects are the presence of misinformation and biases in the flawed pre-training data sources, the knowledge boundary inherently bounded by the scope of the pre-training data, and the hallucinations induced by inferior alignment data. [C2]

### Citations

- **[C1]** P001, PDF p. 19 (`P001-p019-c002`) — As analyzed in §3.1, data-related hallucinations generally emerge as a byproduct of misinformation, biases, and knowledge gaps, which are fundamentally rooted in the pre-training data.
- **[C2]** P001, PDF p. 7 (`P001-p007-c003`) — This primarily manifests in three aspects: the presence of misinformation and biases in the flawed pre-training data sources (§3.1.1), the knowledge boundary inherently bounded by the scope of the pre-training data (§3.1.2), and the hallucinations induced by inferior alignment data (§3.1.3).

---

## GEN-027 — What two sources of knowledge boundaries does the survey identify?

**Status:** complete  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The survey identifies two sources of knowledge boundaries in LLMs: (1) the inability of LLMs to memorize all factual knowledge encountered during pre-training, especially less frequent long-tail knowledge, and (2) the intrinsic boundary of the pre-training data itself, which does not include rapidly evolving world knowledge or content restricted by copyright laws. [C1] [C2]

### Citations

- **[C1]** P001, PDF p. 9 (`P001-p009-c003`) — Consequently, when LLMs encounter information that falls outside their limited knowledge boundaries, they are more susceptible to generating hallucinations. We present detailed examples for clear illustration in Table 3.
- **[C2]** P001, PDF p. 9 (`P001-p009-c003`) — These boundaries arise primarily from two sources: (1) the inability of LLMs to memorize all factual knowledge encountered during pre-training, especially the less frequent long-tail knowledge; and (2) the intrinsic boundary of the pre-training data itself, which does not include rapidly evolving world knowledge or content restricted by copyright laws.

---

## GEN-028 — How does the survey connect entity popularity and domain-specific knowledge to hallucination risk?

**Status:** complete  
**Category:** findings · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

The survey links higher hallucination risk to cases where an LLM encounters information outside its limited knowledge boundaries. [C1]

It connects entity popularity (and general-domain accuracy) to knowledge coverage in pre-training corpora, stating that entity popularity correlates with model accuracy on general domain questions, and that deficits in domain-specific knowledge lead to pronounced hallucinations on domain-specific tasks. [C2] [C3]

The survey associates hallucination risk with the mismatch between the knowledge boundaries learned during pre-training and the demands placed on the model during supervised fine-tuning, which can encourage fabrication when tasks exceed those boundaries and the model cannot express uncertainty. [C4] [C5] [C6] [C7]

### Citations

- **[C1]** P001, PDF p. 9 (`P001-p009-c004`) — encounter information that falls outside their limited knowledge boundaries, they are more susceptible to generating hallucinations.
- **[C2]** P001, PDF p. 9 (`P001-p009-c004`) — Recent studies have highlighted a strong correlation between the model’s accuracy on general domain questions and the volume of relevant documents [145] or entity popularity [204] within the pre-training corpora.
- **[C3]** P001, PDF p. 9 (`P001-p009-c004`) — Furthermore, given that LLMs are predominantly trained on extensive general domain corpora [93, 243, 254], they may exhibit deficits in domain-specific knowledge. This limitation becomes particularly evident when LLMs are confronted with tasks that require domain-specific expertise, such as medical [179, 279] and legal  [149, 353] questions, these models may exhibit pronounced hallucinations, often manifesting as factual fabrication.
- **[C4]** P001, PDF p. 11 (`P001-p011-c001`) — LLMs have inherent capability boundaries established during pre-training.
- **[C5]** P001, PDF p. 11 (`P001-p011-c001`) — However, challenges arise when the demands of annotated instructions exceed the model’s pre-defined capability boundaries.
- **[C6]** P001, PDF p. 11 (`P001-p011-c001`) — As discussed in §3.1.3, over-fitting on new factual knowledge encourages LLMs prone to fabricating content, amplifying the risk of hallucinations [98, 269].
- **[C7]** P001, PDF p. 11 (`P001-p011-c001`) — Consequently, when faced with queries that exceed their knowledge boundaries, these models are more likely to fabricate content rather than reject it.

---

## GEN-029 — Why might a previously correct answer become a hallucination risk under the survey's discussion of temporal knowledge boundaries?

**Status:** partial  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

A previously correct answer can become a hallucination risk when a question falls outside the model’s knowledge boundaries, because the model may “fit responses beyond their actual knowledge boundaries” and is “more likely to fabricate content rather than reject it.” [C1]

The survey attributes hallucinations to LLMs’ difficulties in recognizing their own knowledge boundaries, where this “shortfall leads to the occurrence of hallucinations, where LLMs confidently produce falsehoods without an awareness of their own
knowledge limits.” [C2]

### Citations

- **[C1]** P001, PDF p. 11 (`P001-p011-c001`) — However, challenges arise when the demands of annotated instructions exceed the model’s pre-defined capability boundaries. In such cases, LLMs are trained to fit responses beyond their actual knowledge boundaries. As discussed in §3.1.3, over-fitting on new factual knowledge encourages LLMs prone to fabricating content, amplifying the risk of hallucinations [98, 269]. Moreover, another significant reason lies in the models’ inability to reject. Traditional SFT methods typically force models to complete each response, without allowing them to accurately express uncertainty [341, 362]. Consequently, when faced with queries that exceed their knowledge boundaries, these models are more likely to fabricate content rather than reject it.
- **[C2]** P001, PDF p. 34 (`P001-p034-c001`) — This shortfall leads to the occurrence of hallucinations, where LLMs confidently produce falsehoods without an awareness of their own knowledge limits [235, 261, 384].

### Limitations

- The provided evidence includes general statements about capability/knowledge boundaries and temporal boundaries (“Up-to-date Knowledge”) but does not explicitly explain how a *previously correct answer* specifically becomes a hallucination risk under discussion of temporal knowledge boundaries. The excerpt ends before giving the details needed to connect the temporal-boundary discussion to the “previously correct answer” scenario.
- The evidence does not provide direct “methods” or “limitations” content specifically tied to the temporal knowledge-boundary discussion beyond general statements about knowledge boundaries and hallucination causes.

---

## GEN-030 — According to the survey, how can licensing restrictions affect an LLM's knowledge coverage?

**Status:** complete  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

Licensing restrictions constrain existing LLMs to training on corpora that are publicly licensed or otherwise available for use without infringing copyright laws, which limits the breadth and diversity of knowledge they can legally acquire. [C1]

Because a significant portion of valuable knowledge in copyrighted materials remains inaccessible, licensing restrictions create a knowledge gap that can lead to hallucinations when LLMs try to generate information in domains where their training data is inaccessible. [C2]

The survey characterizes this licensing-induced knowledge gap as a reason LLMs may fabricate facts or provide answers that were correct in the past but are now outdated when queries transcend their temporal scope. [C3]

### Citations

- **[C1]** P001, PDF p. 10 (`P001-p010-c001`) — Due to licensing restrictions [262], existing LLMs are legally constrained to training on corpora that are publicly licensed [63, 93] or otherwise available for use without infringing copyright laws [10, 115]. This limitation significantly impacts the breadth and diversity of knowledge that LLMs can legally acquire.
- **[C2]** P001, PDF p. 10 (`P001-p010-c001`) — A significant portion of valuable knowledge, encapsulated in copyrighted materials such as recent scientific research, proprietary data, and copyrighted literary works, remains inaccessible to LLMs. This exclusion creates a knowledge gap, leading to potential hallucinations when LLMs attempt to generate information in domains where their training data is inaccessible [215].
- **[C3]** P001, PDF p. 10 (`P001-p010-c001`) — When confronted with queries that transcend their temporal scope, LLMs often resort to fabricating facts or providing answers that might have been correct in the past but are now outdated.

---

## GEN-031 — What relationship between new factual knowledge during supervised fine-tuning and hallucinations does the survey report?

**Status:** complete  
**Category:** findings · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The survey reports that acquiring new factual knowledge during supervised fine-tuning is correlated with increased hallucinations, suggesting that introducing new factual knowledge encourages LLMs to hallucinate. [C1]

### Citations

- **[C1]** P001, PDF p. 10 (`P001-p010-c002`) — Most importantly, they discovered a correlation between the acquisition of new knowledge through SFT and increased hallucinations, suggesting that introducing new factual knowledge encourages LLMs to hallucinate.

---

## GEN-032 — How do pre-training knowledge boundaries and alignment data together explain hallucination risks in the survey?

**Status:** complete  
**Category:** multi_hop · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the survey, data used to train LLMs is described as having two primary components—pre-training data and alignment data—and the survey states that these data “inadvertently become the principal contributors to LLM hallucinations,” including a knowledge boundary bounded by pre-training scope and hallucinations induced by inferior alignment data. [C1]

The survey explains that pre-training establishes inherent capability/knowledge boundaries, and that misalignment with these boundaries during supervised fine-tuning can make models fit responses beyond their actual knowledge boundaries, amplifying hallucination risk. [C2]

The survey further links alignment data to hallucination risk by describing an “inferior alignment data” cause: during SFT, instruction pairs labeled by human annotators may introduce new factual knowledge beyond the pre-training knowledge boundary, and the survey reports a correlation between acquisition of new knowledge through SFT and increased hallucinations. [C3]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c003`) — Data for training LLMs are comprised of two primary components: (1) pre-training data, through which LLMs acquire their general capabilities and factual knowledge [388], and (2) alignment data, which teach LLMs to follow user instructions and align with human preferences [322]. Although these data constantly expand the capability boundaries of LLMs, they inadvertently become the principal contributors to LLM hallucinations. This primarily manifests in three aspects: the presence of misinformation and biases in the flawed pre-training data sources (§3.1.1), the knowledge boundary inherently bounded by the scope of the pre-training data (§3.1.2), and the hallucinations induced by inferior alignment data (§3.1.3).
- **[C2]** P001, PDF p. 11 (`P001-p011-c001`) — LLMs have inherent capability boundaries established during pre-training. SFT seeks to utilize instruction data and corresponding responses to unlock these pre-acquired abilities. However, challenges arise when the demands of annotated instructions exceed the model’s pre-defined capability boundaries. In such cases, LLMs are trained to fit responses beyond their actual knowledge boundaries. As discussed in §3.1.3, over-fitting on new factual knowledge encourages LLMs prone to fabricating content, amplifying the risk of hallucinations [98, 269].
- **[C3]** P001, PDF p. 10 (`P001-p010-c002`) — _3.1.3_ _Inferior_ _Alignment_ _Data._ After the pre-training stage, LLMs have embedded substantial factual knowledge within their parameters, thereby establishing obvious knowledge boundaries. During the supervised fine-tuning (SFT) stage, LLMs are typically trained on instruction pairs labeled by human annotators, potentially introducing new factual knowledge that extends beyond the knowledge boundary established during pre-training. Gekhman et al. [98] analyzed the training dynamics of incorporating new factual knowledge during the SFT process and found that LLMs struggle to acquire such new knowledge effectively. Most importantly, they discovered a correlation between the acquisition of new knowledge through SFT and increased hallucinations, suggesting that introducing new factual knowledge encourages LLMs to hallucinate.

---

## GEN-033 — Which five SelfCheckGPT consistency variants are listed by the authors?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The authors list five SelfCheckGPT consistency variants: BERTScore, question-answering, n-gram, NLI, and LLM prompting. [C1]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c002`) — Five variants of SelfCheckGPT for measuring informational consistency are considered: BERTScore, question-answering, _n_ -gram, NLI, and LLM prompting.

---

## GEN-034 — Why can perturbing factual texts produce an imperfect hallucination-detection dataset, according to SelfCheckGPT's related work?

**Status:** complete  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT’s related work notes that Liu et al. (2022) introduced a hallucination detection dataset by perturbing factual texts, but that this may not reflect true LLM hallucination. [C1]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c003`) — Further, Liu et al. (2022) introduce a hallucination detection dataset, however, texts are obtained by perturbing factual texts and thus may not reflect true LLM hallucination.

---

## GEN-035 — What additional access and supervision does the hidden-state classifier discussed in SelfCheckGPT require?

**Status:** partial  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The hidden-state classifier approach cited as a related work uses the internal states of the LLM, which may not be available through API calls, and requires labelled data for supervised training. [C1]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c003`) — Recently, Azaria and Mitchell (2023) trained a multi-layer perception classifier where an LLM’s hidden representations are used as inputs to predict the truthfulness of a sentence. However, this approach is a white-box approach that uses the  internal states of the LLM, which may not be available through API calls, and requires labelled data for supervised training.

### Limitations

- The provided evidence does not further specify what additional access and supervision the hidden-state classifier requires beyond internal-state access (may not be available via API calls) and labelled data for supervised training.

---

## GEN-036 — How does SelfCheckGPT's MQAG variant test consistency using generated questions?

**Status:** partial  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In SelfCheckGPT’s MQAG variant, for each sentence r_i in the response R the method draws questions q and options o using a question-generation stage G, where the questions are conditioned on r_i and R. [C1]

MQAG measures consistency by generating multiple-choice questions over the main generated response, then using an independent answering system to predict the answers conditioned on the other sampled responses, with the expectation that consistent information yields similar answers. [C2]

SelfCheckGPT with QA (used with the MQAG question-answering setup) is defined as the average of inconsistency scores across q. [C3]

### Citations

- **[C1]** P002, PDF p. 4 (`P002-p004-c002`) — For the sentence _ri_ in the response _R_, we draw questions _q_ and options **o** :  _q,_ **o** _P_ `G` ( _q,_ **o** _ri, R_ ) (2) _∼_ _|_
- **[C2]** P002, PDF p. 4 (`P002-p004-c002`) — MQAG assesses consistency by generating multiple-choice questions over the main generated response, which an independent answering system can attempt to answer while conditioned on the other sampled responses. If questions on consistent information are queried, the answering system is expected to predict similar answers.
- **[C3]** P002, PDF p. 4 (`P002-p004-c001`) — Ultimately, SelfCheckGPT with QA is the average of inconsistency scores across _q_,

### Limitations

- The provided evidence explains how the MQAG question-generation and answering setup is used for consistency, but it does not provide explicit MQAG-specific numerical findings or performance results (e.g., exact correlation values for MQAG/QA) tied to this variant.
- The provided evidence does not describe MQAG-specific limitations; any general performance comparison statements are not specific enough to isolate the MQAG variant’s limitations.

---

## GEN-037 — Which backbone is used for BERTScore in SelfCheckGPT?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In SelfCheckGPT, RoBERTa-Large (Liu et al., 2019) is used as the backbone of BERTScore. [C1]

### Citations

- **[C1]** P002, PDF p. 4 (`P002-p004-c002`) — In this work, RoBERTa-Large (Liu et al., 2019) is used as the backbone of BERTScore.

---

## GEN-038 — Why does SelfCheckGPT include the main response when training its n-gram approximation?

**Status:** partial  
**Category:** methodology · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT’s n-gram variant can experience a large performance drop when using WikiBio passages instead of self-samples because “the WikiBio reference text alone is not sufficient to train an n-gram model.” [C1]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c003`) — Second, SelfCheckGPT with _n_ -gram shows a large performance drop when using the WikiBio passages instead of self-samples. This failure is attributed to the fact that the WikiBio reference text alone is not sufficient to train an _n_ -gram model.

### Limitations

- The provided evidence does not explicitly explain why SelfCheckGPT includes the main response specifically when training its n-gram approximation; it only states that using WikiBio reference text alone is insufficient to train an n-gram model.

---

## GEN-039 — Which NLI model and class logits are used in SelfCheckGPT-NLI?

**Status:** complete  
**Category:** methodology · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheck-NLI in SelfCheckGPT uses DeBERTa-v3-large fine-tuned to MNLI as the NLI model. [C1]

SelfCheckGPT-NLI considers only the logits associated with the ‘entailment’ and ‘contradiction’ classes, using logits ze and zc in the normalization for the probability of contradiction. [C2]

The SelfCheckGPT with NLI score for each sample S[n] is defined using P(contradict ri, S[n]) and then aggregated across n samples. [C3]

### Citations

- **[C1]** P002, PDF p. 5 (`P002-p005-c001`) — For SelfCheck-NLI, we use DeBERTa-v3-large (He et al., 2023) fine-tuned to MNLI as the NLI model.
- **[C2]** P002, PDF p. 5 (`P002-p005-c001`) — Only the logits associated with the ‘entailment’ and ‘contradiction’ classes are considered,  exp( _zc_ ) _P_ (contradict _ri, S_ _[n]_ ) = (9) _|_ exp( _ze_ ) + exp( _zc_ )  where _ze_ and _zc_ are the logits of the ‘entailment’ and ‘contradiction’ classes, respectively.
- **[C3]** P002, PDF p. 5 (`P002-p005-c001`) — The SelfCheckGPT with NLI score for each sample _S_ _[n]_ is then defined as,  NLI( _i_ ) = [1] _S_ _N_  _N_  _n_ =1  _n_ =1  _P_ (contradict _ri, S_ _[n]_ ) (10) _|_

---

## GEN-040 — How many WikiBio articles were sampled for SelfCheckGPT, and from which part of the length distribution?

**Status:** complete  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheckGPT sampled 238 WikiBio articles. [C1]

The sampled WikiBio articles came from the top 20% of longest articles in the paragraph-length distribution. [C2]

### Citations

- **[C1]** P002, PDF p. 5 (`P002-p005-c003`) — We rank the WikiBio test set in terms of paragraph length and randomly sample 238 articles from the top 20% of longest articles (to ensure no very obscure concept is selected).
- **[C2]** P002, PDF p. 5 (`P002-p005-c003`) — We rank the WikiBio test set in terms of paragraph length and randomly sample 238 articles from the top 20% of longest articles (to ensure no very obscure concept is selected).

---

## GEN-041 — What are SelfCheckGPT's three sentence annotation labels and their numeric values?

**Status:** complete  
**Category:** quantitative · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheckGPT’s three sentence annotation labels are Major Inaccurate, Minor Inaccurate, and Accurate. [C1]

Major Inaccurate corresponds to the numeric value 1. [C2]

Minor Inaccurate corresponds to the numeric value 0.5, and Accurate corresponds to the numeric value 0. [C3]

### Citations

- **[C1]** P002, PDF p. 5 (`P002-p005-c003`) — passages using the guidelines shown in Figure 3 such that each sentence is classified as either:  - **Major Inaccurate** (Non-Factual, **1** ): The sentence is entirely hallucinated, i.e. the sentence is unrelated to the topic.  - **Minor** **Inaccurate** (Non-Factual, **0.5** ): The sentence consists of some non-factual information, but the sentence is related to the topic.  - **Accurate** (Factual, **0** ): The information presented in the sentence is accurate.
- **[C2]** P002, PDF p. 5 (`P002-p005-c003`) — - **Major Inaccurate** (Non-Factual, **1** ): The sentence is entirely hallucinated, i.e. the sentence is unrelated to the topic.
- **[C3]** P002, PDF p. 5 (`P002-p005-c003`) — - **Minor** **Inaccurate** (Non-Factual, **0.5** ): The sentence consists of some non-factual information, but the sentence is related to the topic.  - **Accurate** (Factual, **0** ): The information presented in the sentence is accurate.

---

## GEN-042 — How were annotator disagreements resolved in the SelfCheckGPT dataset?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

For sentences with annotations from two different annotators, if both annotators agree then the agreed label is used, but if there is disagreement the worse-case label is selected (e.g., {minor inaccurate, major inaccurate} is mapped to major inaccurate). [C1]

### Citations

- **[C1]** P002, PDF p. 5 (`P002-p005-c004`) — 201 sentences in the dataset had annotations from two different annotators. To obtain a single label for this subset, if both annotators agree, then the agreed label is used. However, if there is disagreement, then the worse-case label is selected (e.g., {minor inaccurate, major inaccurate} is mapped to  major inaccurate).

---

## GEN-043 — What temperatures were used for SelfCheckGPT's main response and stochastic samples, and how many samples were drawn?

**Status:** partial  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

To obtain the main response, SelfCheckGPT sets the temperature to 0.0 and uses standard beam search decoding. [C1]

For the stochastically generated samples, SelfCheckGPT sets the temperature to 1.0 and generates samples with N = 20. [C2] [C3]

### Citations

- **[C1]** P002, PDF p. 6 (`P002-p006-c001`) — To obtain the main response, we set the temperature to 0.0 and use standard beam search decoding.
- **[C2]** P002, PDF p. 6 (`P002-p006-c001`) — For the stochastically generated samples, we set the temperature to 1.0 and generate
- **[C3]** P002, PDF p. 6 (`P002-p006-c002`) — _N_ =20 samples.

### Limitations

- The evidence provided does not explicitly state how the temperature setting (0.0 for the main response and 1.0 for stochastic samples) maps to the specific SelfCheckGPT components the question calls “main response” and “stochastic samples” beyond the general experimental description in the cited passages.

---

## GEN-044 — What trade-off does SelfCheckGPT report as the number of sampled responses increases?

**Status:** partial  
**Category:** findings · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

SelfCheckGPT reports that, as SelfCheckGPT with Prompt can be computationally heavy, it can provide a trade-off between performance and computation by using SelfCheckGPT with NLI as a more practical method. [C1]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c001`) — As SelfCheckGPT with Prompt can be computationally heavy, SelfCheckGPT with NLI could be the most practical method as it provides a good trade-off between performance and computation.

### Limitations

- The provided evidence does not state how the trade-off changes specifically “as the number of sampled responses increases”; it only mentions computational heaviness and a performance–computation trade-off when choosing between prompt and NLI.

---

## GEN-045 — What is an atomic fact in FActScore, and why is a sentence sometimes too coarse a unit?

**Status:** complete  
**Category:** definitions · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In FActScore, an atomic fact is defined as a short sentence conveying one piece of information, and it is used as a more fundamental unit than a sentence to provide more fine-grained evaluation. [C1]

A sentence can be too coarse a unit in FActScore because even a single sentence can contain a mix of supported and unsupported facts. [C2]

FActScore motivates atomic-level evaluation in part because human validation against a large knowledge source is time-consuming and costly, preventing evaluation at scale; specifically, validating every atomic fact is time-consuming and one generation contains many (26–41) atomic facts. [C3]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c002`) — In this paper, we define an atomic fact as a short sentence conveying one piece of information (examples in Figure 1), similar to summarization content units (Nenkova and Passonneau, 2004). An atomic fact is a more fundamental unit than a sentence for a piece of information and provides a more fine-grained evaluation,
- **[C2]** P003, PDF p. 3 (`P003-p003-c002`) — Prior work has explored using a sentence as a unit; however, even a single sentence is a mix of supported and unsupported facts,
- **[C3]** P003, PDF p. 6 (`P003-p006-c002`) — Human evaluation of factual precision is costly ($4 per generation) (Bohnet et al., 2022; Krishna et al., 2023) because validating every atomic fact against a large knowledge source is time-consuming, and one generation contains many (26–41) atomic facts.

---

## GEN-046 — Does FActScore assess global truth or support relative to a chosen knowledge source?

**Status:** partial  
**Category:** definitions · **Difficulty:** easy  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore does not treat factual precision as whether atomic facts are globally true or false; instead, it evaluates whether an atomic fact is supported by a particular knowledge source that end users consider trustworthy and reliable. [C1]

FActScore models factual precision as a function of a given knowledge source by breaking a generation into atomic facts and validating each against that given knowledge source. [C2]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c004`) — Therefore, instead of whether an atomic fact is globally true or false, we consider whether it is _supported_ by a given source of knowledge.
- **[C2]** P003, PDF p. 6 (`P003-p006-c002`) — Our estimator of FACTSCORE first breaks a generation into a series of atomic facts and then validates each against the given knowledge source.

### Limitations

- The requested aspects of limitations are not fully supported because the supplied evidence for the limitation content about recall/holistic evaluation appears in a different source chunk than the one referenced by the prior quote (the chunk labeled S3 does not contain the specific limitation sentences about factual recall and leaving holistic evaluation for future work).

---

## GEN-047 — Why did FActScore evaluate biographies against Wikipedia?

**Status:** partial  
**Category:** experimental_setup · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore prompted an LM to generate people biographies and evaluated them against Wikipedia for the following reasons: biographies are objective and contain specific information (not vague), satisfying Assumption 1. [C1]

FActScore evaluated generations as people biographies against Wikipedia because it evaluates factual precision on verifiable statements rather than debatable or subjective ones, with a broad scope covering diverse nationalities, professions, and rarity levels. [C2]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c001`) — - Biographies are objective (not subjective or debatable) and contain specific (not vague) information, satisfying Assumption 1 in Section 3.1.
- **[C2]** P003, PDF p. 2 (`P003-p002-c001`) — We evaluate FACTSCORE on the task of generating people biographies because generations consist of verifiable statements rather than debatable or subjective ones, and the scope is broad (i.e., covering diverse nationalities, professions, and levels of rarity).

### Limitations

- The specific quoted justification that Wikipedia offers reasonable coverage of information about people and is reasonably selfconsistent (Assumption 3) could not be validated against the provided S1 chunk because the earlier response used a quote that does not match the available S1 text.

---

## GEN-048 — How many people entities were sampled in FActScore's human evaluation, and where were they sampled from?

**Status:** complete  
**Category:** quantitative · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore’s human evaluation sampled 183 people entities. [C1]

The sampled people entities were sampled from Wikidata, restricted to those who have corresponding Wikipedia pages. [C2]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c001`) — Step** **0:** **Sampling** **people** **entities.** We sample 183 people entities from Wikidata who have corresponding Wikipedia pages.
- **[C2]** P003, PDF p. 4 (`P003-p004-c001`) — We sample 183 people entities from Wikidata who have corresponding Wikipedia pages.

---

## GEN-049 — How were machine-generated atomic facts used to assist FActScore's human annotators?

**Status:** complete  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the FACTSCORE human-annotation pipeline, human annotators broke each generation into atomic facts, and to save annotation time the paper provided atomic facts “broken down by InstructGPT which human annotators can take and revise.” [C1]

The paper states that atomic facts provided by InstructGPT were also used in the FACTSCORE estimator for automatic evaluation, where it “find[s] taking atomic facts generated by InstructGPT (used in data collection in Section 3.3) effective and close to human.” [C2]

The paper reports that human evaluation of FACTSCORE is costly ($4 per generation), and explains this is due to the time needed to validate “every atomic fact,” motivating automatic estimation. [C3]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c002`) — Step 2:** **Atomic facts generation.** Human annotators break a generation into a series of atomic facts. To save annotation time, we provide atomic facts broken down by InstructGPT which human annotators can take and revise. Details in Appendix A.2.
- **[C2]** P003, PDF p. 6 (`P003-p006-c002`) — We find taking atomic facts generated by InstructGPT (used in data collection in Section 3.3) effective and close to human, consistent with findings from prior work (Chen et al., 2022).
- **[C3]** P003, PDF p. 6 (`P003-p006-c002`) — Human evaluation of factual precision is costly ($4 per generation) (Bohnet et al., 2022; Krishna et al., 2023) because validating every atomic fact against a large knowledge source is time-consuming, and one generation contains many (26–41) atomic facts.

---

## GEN-050 — Which three annotation labels does FActScore assign to atomic facts?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore assigns each atomic fact one of three labels: Irrelevant, Supported, and Not-supported. [C1]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c002`) — We ask another set of human annotators to assign each atomic fact one of three labels. If the atomic fact is clearly not related to the prompt, and thus should be removed from the bio without a validation step, they assign Irrelevant. If the fact is relevant, they validate the fact based on the English Wikipedia, and label either Supported or Not-supported.

---

## GEN-051 — What hourly pay range and per-generation annotation cost does FActScore report?

**Status:** complete  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore reports paying freelancers 15–25 USD per hour. [C1]

FActScore reports that annotation costs $4 per generation. [C2]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c002`) — We recruit freelancers through Upwork and pay 15–25 USD per hour.
- **[C2]** P003, PDF p. 4 (`P003-p004-c002`) — Annotation requires extensive effort and time, leading to the cost of $4 per generation.

---

## GEN-052 — What FActScores were reported for InstructGPT, ChatGPT, and PerplexityAI in the human evaluation?

**Status:** complete  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

In the human evaluation, InstructGPT achieved a FACTSCORE of 42.5%. [C1]

In the human evaluation, ChatGPT achieved a FACTSCORE of 58.3%. [C2]

In the human evaluation, PerplexityAI achieved a FACTSCORE of 71.5%. [C3]

### Citations

- **[C1]** P003, PDF p. 4 (`P003-p004-c003`) — InstructGPT and ChatGPT achieve FACTSCOREs of 42.5% and 58.3%, respectively.
- **[C2]** P003, PDF p. 4 (`P003-p004-c003`) — InstructGPT and ChatGPT achieve FACTSCOREs of 42.5% and 58.3%, respectively.
- **[C3]** P003, PDF p. 4 (`P003-p004-c003`) — PerplexityAI, which uses a commercial search engine and thus should have a perfect FACTSCORE if directly copying the text from the correct Wikipedia page, attains a FACTSCORE of 71.5%.

---

## GEN-053 — How does FActScore's equal-importance assumption treat individual atomic facts?

**Status:** complete  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore’s definition assumes that every atomic fact in the generation has an equal weight of importance. [C1]

Under these assumptions, FActScore evaluates factual precision by treating an atomic fact as a unit of information that can be true or false, rather than using sentences as the unit. [C2] [C3]

The paper notes an additional assumption for applying FACTSCORE that knowledge-source pieces of information do not conflict or overlap with each other, which constrains how atomic facts are treated relative to the knowledge source. [C4]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c003`) — 2. Every atomic fact in _Ay_ has an equal weight of importance, following Krishna et al. (2023).
- **[C2]** P003, PDF p. 3 (`P003-p003-c002`) — Long-form text consists of many pieces of information that can each be either true or false.
- **[C3]** P003, PDF p. 3 (`P003-p003-c002`) — In this paper, we define an atomic fact as a short sentence conveying one piece of information (examples in Figure 1), similar to summarization content units (Nenkova and Passonneau, 2004).
- **[C4]** P003, PDF p. 3 (`P003-p003-c003`) — 3. Pieces of information in _C_ do not conflict or overlap with each other.

---

## GEN-054 — Why is FActScore unsuitable for some nuanced or intentionally deceptive human-written text?

**Status:** complete  
**Category:** limitations · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore is not applicable when the underlying facts are more nuanced, open-ended, and debatable. [C1]

FActScore may be unsuitable when the knowledge source frequently conflicts with itself. [C2]

FActScore may not be suitable for human-written text that is nuanced and includes intentional or implicit deception. [C3]

### Citations

- **[C1]** P003, PDF p. 10 (`P003-p010-c001`) — FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023)
- **[C2]** P003, PDF p. 10 (`P003-p010-c001`) — or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).
- **[C3]** P003, PDF p. 10 (`P003-p010-c001`) — Moreover, FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional or implicit deception.

---

## GEN-055 — Why should good aggregate FActScore estimator performance not be interpreted as perfect individual judgments?

**Status:** complete  
**Category:** limitations · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

Good aggregate FActScore estimator performance should not be interpreted as perfect individual judgments because the paper states that the estimator is “not perfect in individual judgments.” [C1]

FActScore performance can depend on assumptions and the type of facts, so even if aggregate results look good, the estimator is limited for cases that are “more nuanced, open-ended, and debatable,” have conflicting sources, or involve “intentional or implicit deception.” [C2]

### Citations

- **[C1]** P003, PDF p. 10 (`P003-p010-c001`) — While our estimator closely approximates humans and provides consistent ranking over a large set of LMs, it is not perfect in individual judgments, and the best variant depends on the degree of how close a generation is to human-written text and its linguistic complexity.
- **[C2]** P003, PDF p. 10 (`P003-p010-c001`) — FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022). Moreover, FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional or implicit deception.

---

## GEN-056 — How many generations and models were included in FActScore's larger automated case study, and what human cost was estimated?

**Status:** complete  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore's larger automated case study evaluated 6,500 generations from 13 LMs. [C1]

FActScore estimated the human cost of evaluating those 6,500 generations from 13 LMs to be $26K. [C2]

### Citations

- **[C1]** P003, PDF p. 2 (`P003-p002-c002`) — Our case study evaluates 6,500 generations from 13 LMs that could have cost $26K,
- **[C2]** P003, PDF p. 1 (`P003-p001-c001`) — Finally, we use this automated metric to evaluate 6,500 generations from a new set of 13 recent LMs that would have cost $26K if evaluated by humans, with various findings:

---

## GEN-057 — Under TruthfulQA's definition, can a truthful answer be irrelevant or noncommittal?

**Status:** complete  
**Category:** definitions · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

Under TruthfulQA’s definition, a truthful answer can be noncommittal (e.g., “No comment” or “I don’t know”) and can also be true while irrelevant. [C1]

TruthfulQA treats non-committal answers as true even when there is a sense in which the model knows a true answer. [C2]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c001`) — We define an answer to a question as _truthful_ iff it avoids asserting a false statement. So truthfulness is consistent with refusing to answer a question, with expressing uncertainty, or with giving a true but irrelevant answer. In this paper, we evaluate non-committal answers such as “No comment” or “I don’t know” as true, even when there’s a sense in
- **[C2]** P004, PDF p. 4 (`P004-p004-c002`) — In this paper, we evaluate non-committal answers such as “No comment” or “I don’t know” as true, even when there’s a sense in  which the model “knows” a true answer.

---

## GEN-058 — Why does TruthfulQA evaluate informativeness as well as truthfulness?

**Status:** complete  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA evaluates informativeness in addition to truthfulness because, while truthfulness is about avoiding false statements, the authors want answers that are both truthful and informative, meaning they provide information that reduces uncertainty raised by the question. [C1]

TruthfulQA defines informativeness as an additional evaluation component alongside truthfulness, and it combines these components in reported scoring such as “Truth*Info score,” which averages the product of scalar truth and informativeness scores. [C2]

The paper explicitly notes that its automated evaluation approach for informativeness is implemented by finetuning a model specifically to evaluate informativeness rather than truthfulness. [C3]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c002`) — In practice we want answers that are both truthful and _informative_ (i.e. providing information that reduces uncertainty raised by the question). So in assessing models, we also include evaluations of informativeness.
- **[C2]** P004, PDF p. 21 (`P004-p021-c002`) — - “Truth*Info score” is the average over the product of scalar truth and informativeness scores.
- **[C3]** P004, PDF p. 16 (`P004-p016-c001`) — We also use an identical approach to finetune a model to evaluate informativeness (rather than truthfulness).

---

## GEN-059 — How many questions and categories does TruthfulQA contain?

**Status:** complete  
**Category:** quantitative · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

TruthfulQA contains 817 questions. [C1]

TruthfulQA contains 38 categories. [C2]

### Citations

- **[C1]** P004, PDF p. 1 (`P004-p001-c001`) — The benchmark comprises 817 questions that span 38 categories, including health, law, finance and politics.
- **[C2]** P004, PDF p. 1 (`P004-p001-c001`) — The benchmark comprises 817 questions that span 38 categories, including health, law, finance and politics.

---

## GEN-060 — What is the median question length in TruthfulQA, and what reference material accompanies a question?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In TruthfulQA, most questions are one-sentence long with a median length of 9 words. [C1]

Each TruthfulQA question has sets of true and false reference answers and a source that supports the answers (e.g. a Wikipedia page). [C2]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c002`) — Most questions are one-sentence long with a median length of 9 words.
- **[C2]** P004, PDF p. 4 (`P004-p004-c002`) — Each question has sets of true and false reference answers and a source that supports the answers (e.g. a Wikipedia page).

---

## GEN-061 — How do TruthfulQA's filtered and unfiltered question sets differ in construction and size?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA consists of a test set of 817 questions, with questions produced by an adversarial procedure that yields both a “filtered” set and an additional “unfiltered” set. [C1] [C2] [C3]

Filtered questions were produced by writing questions that some humans would answer falsely, testing them on GPT-3-175B, and filtering out questions that the model consistently answered correctly; this produced 437 filtered questions. [C4] [C5]

Unfiltered questions were produced by writing 380 additional questions expected some humans and models to answer falsely, but since they were not tested on the target model, they were labeled “unfiltered” questions. [C6] [C7]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c002`) — TruthfulQA consists of a test set of 817 questions
- **[C2]** P004, PDF p. 4 (`P004-p004-c003`) — We produced 437 questions this way, which we call the “filtered” questions (Wallace and Boyd-Graber, 2018).
- **[C3]** P004, PDF p. 4 (`P004-p004-c003`) — Since we did not test on the target model, these are “unfiltered” questions.
- **[C4]** P004, PDF p. 4 (`P004-p004-c003`) — We wrote questions that some humans would answer falsely. We tested them on the target model and filtered out questions that the model consistently answered correctly when multiple random samples were generated at nonzero temperatures.
- **[C5]** P004, PDF p. 4 (`P004-p004-c003`) — We produced 437 questions this way, which we call the “filtered” questions (Wallace and Boyd-Graber, 2018).
- **[C6]** P004, PDF p. 4 (`P004-p004-c003`) — Using this experience of testing on the target model, we wrote 380 additional questions that we expected some humans and models to answer falsely.
- **[C7]** P004, PDF p. 4 (`P004-p004-c003`) — Since we did not test on the target model, these are “unfiltered” questions.

---

## GEN-062 — What disagreement rate did TruthfulQA's external validator report on its sample of reference answers?

**Status:** complete  
**Category:** quantitative · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

TruthfulQA’s external validator disagreed with the authors’ true/false labels on 7% of questions (from a sample of 100 questions). [C1] [C2]

The paper also states that the validator explicitly described a disagreement or ambiguity on 6% of instances. [C3]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c004`) — They disagreed on 7% of questions.
- **[C2]** P004, PDF p. 4 (`P004-p004-c004`) — A “validator” was shown a random sample of 100 questions from TruthfulQA with one true and one false reference answer given per question.
- **[C3]** P004, PDF p. 39 (`P004-p039-c001`) — The validator explicitly described a disagreement or ambiguity on 6% of instances.

---

## GEN-063 — What four model families were evaluated in the main TruthfulQA baseline experiments?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the main TruthfulQA baseline experiments, the four model families evaluated were GPT-3, GPT-Neo/J, GPT-2, and UnifiedQA. [C1]

### Citations

- **[C1]** P004, PDF p. 5 (`P004-p005-c001`) — To compute baselines for TruthfulQA, we evaluate four model families:  1. GPT-3 (Brown et al., 2020) is trained on filtered Common Crawl and other sources.  2. GPT-Neo/J (Black et al., 2021; Wang and Komatsuzaki, 2021) is a variant of GPT-3 with a different training set (Gao et al., 2020).  3. GPT-2 is trained on WebText (Radford et al., 2019).  4. UnifiedQA (Khashabi et al., 2020) is a T5 model (Raffel et al., 2019) fine-tuned on diverse QA tasks.

---

## GEN-064 — What makes TruthfulQA's baseline setting true zero-shot?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

TruthfulQA’s “true zero-shot” baseline setting means that no gradient updates are performed and no examples from TruthfulQA appear in prompts (though prompts may contain natural language instructions), and additionally that prompts and hyperparameters are not tuned on examples from TruthfulQA in any way. [C1]

For the “true zero-shot” baselines, generation answers are produced by greedy decoding (temperature set to zero) with model and sampling parameters otherwise unchanged from the defaults in the OpenAI API or the HuggingFace API. [C2]

TruthfulQA reports that the benchmark is intended only for the zero-shot setting and defines perfect truthfulness as answering “No comment” for every question. [C3] [C4]

### Citations

- **[C1]** P004, PDF p. 5 (`P004-p005-c002`) — Zero-shot means that (i) no gradient updates are performed and (ii) no examples from TruthfulQA appear in prompts (but prompts may contain natural language instructions). For our baselines, we also require that prompts and hyperparameters are not tuned on examples from TruthfulQA in any way. We call this the _true_ _zero-shot_ setting
- **[C2]** P004, PDF p. 5 (`P004-p005-c003`) — Answers are generated using greedy decoding (i.e. temperature set to zero). Model and sampling parameters are otherwise unchanged from the defaults in the OpenAI API (GPT-3; OpenAI, 2020) or the HuggingFace API (GPT-2, GPT-Neo/J, UnifiedQA; Wolf et al., 2020).
- **[C3]** P004, PDF p. 4 (`P004-p004-c002`) — TruthfulQA consists of a test set of 817 questions and is intended only for the zero-shot setting.
- **[C4]** P004, PDF p. 4 (`P004-p004-c002`) — It follows from our definition that a model is perfectly truthful if it answers “No comment” for every question.

---

## GEN-065 — How does TruthfulQA score its multiple-choice task?

**Status:** complete  
**Category:** methodology · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

For the multiple-choice variation, TruthfulQA evaluates each question by computing the likelihood of each true and false reference answer independently conditional on the default prompt and question, then uses the total normalized likelihood of the true answers (normalized across all true and false reference answers) as the truthfulness score for the question. [C1]

### Citations

- **[C1]** P004, PDF p. 5 (`P004-p005-c004`) — To evaluate a model on a question, we compute the likelihood of each reference answer independently, conditional on the default prompt and question. The truthfulness score for the question is the total normalized likelihood of the true answers (normalized across all true and false reference answers).

---

## GEN-066 — What relationship between model size, truthfulness, and informativeness is reported for TruthfulQA's studied families?

**Status:** complete  
**Category:** findings · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

For the studied families, truthfulness shows an inverse scaling pattern: larger models generally do worse than smaller models within the same family, exemplified by the largest GPT-Neo/J being 17% less truthful than a model 60x smaller. [C1]

Across these families, informativeness increases with model size even though truthfulness decreases, with the paper stating that while larger models were less truthful, they were more informative. [C2]

Synthesis: The paper interprets these results as indicating that scaling up model size makes models more capable (in principle) of being both truthful and informative. [C3]

The paper also reports that, although larger models in a family were less truthful, the paraphrase control experiment found that truthfulness scores do not change substantially for paraphrased questions, and that the largest GPT-3 and GPT-Neo/J models still perform worse than the smaller models in the family. [C4]

When both truthfulness and informativeness are taken into account, there remains a large gap between the best-performing model and the human baseline. [C5]

### Citations

- **[C1]** P004, PDF p. 7 (`P004-p007-c001`) — Figure 2 shows that larger models generally do worse than smaller models in the same family (inverse scaling). For example, the largest GPT-Neo/J is 17% less truthful than a model 60x smaller.
- **[C2]** P004, PDF p. 7 (`P004-p007-c001`) — While larger models were less truthful, they were more informative.
- **[C3]** P004, PDF p. 7 (`P004-p007-c001`) — This suggests that scaling up model size makes models more capable (in principle) of being both truthful and informative.
- **[C4]** P004, PDF p. 7 (`P004-p007-c004`) — Overall, we find that truthfulness scores for models do not change substantially on the paraphrased questions (Appendix B.9). In particular, the largest GPT-3 and GPT-Neo/J models still perform worse than the smaller models in the family.
- **[C5]** P004, PDF p. 22 (`P004-p022-c002`) — there is still a large gap between the best-performing model (WebGPT) and the human baseline, especially when both truthfulness and informativeness are taken into account.

---

## GEN-067 — How were TruthfulQA's matched control questions constructed and what scaling trend did they show?

**Status:** complete  
**Category:** methodology · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

TruthfulQA’s matched control questions were constructed by editing 1–3 words of a question in TruthfulQA in a way that preserved the form of the questions but turned them into straightforward trivia or common-sense questions. [C1]

Truthfulness on the matched control questions showed an improving scaling trend with model size for all model families. [C2]

### Citations

- **[C1]** P004, PDF p. 7 (`P004-p007-c003`) — Each question was constructed by editing 1-3 words of a question in TruthfulQA (see Appendix C.2 for examples). The edits preserve the form of the questions but turn them into straightforward trivia or common-sense questions.
- **[C2]** P004, PDF p. 7 (`P004-p007-c003`) — Yet Figure 2 shows that truthfulness on the matched  controls improves with model size for all model families and that the largest GPT-3 and GPT-Neo/J achieve high absolute truthfulness scores.

---

## GEN-068 — What did TruthfulQA's paraphrase experiment suggest, and what alternative explanation remains difficult to rule out?

**Status:** complete  
**Category:** limitations · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

TruthfulQA’s paraphrase experiment found that “truthfulness scores for models do not change substantially on the paraphrased questions,” and that “the largest GPT-3 and GPT-Neo/J models still perform worse than the smaller models in the family.” [C1]

Synthesis: The results suggest that the poor performance on TruthfulQA is not explained by most questions exploiting a non-imitative weakness tied to “a particular syntax or form.” [C2]

An alternative explanation that remains difficult to rule out is “non-imitative weaknesses that are more “semantic” in nature.” [C3]

### Citations

- **[C1]** P004, PDF p. 7 (`P004-p007-c004`) — Overall, we find that truthfulness scores for models do not change substantially on the paraphrased questions (Appendix B.9). In particular, the largest GPT-3 and GPT-Neo/J models still perform worse than the smaller models in the family.
- **[C2]** P004, PDF p. 7 (`P004-p007-c004`) — This evidence suggests that the poor performance of models on TruthfulQA is not explained by most questions exploiting a (non-imitative) weakness to a particular syntax or form.
- **[C3]** P004, PDF p. 7 (`P004-p007-c004`) — It is harder to rule out non-imitative weaknesses that are more “semantic” in nature.

---

## GEN-069 — In the conversation paper, how does RAG-Sequence differ from RAG-Token?

**Status:** partial  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

RAG-Sequence considers documents independently by generating an output sequence for each concatenated context separately and marginalizing over the output generations. [C1]

RAG-Token marginalizes the output distribution over all documents, allowing the generator to attend over a different document for each token. [C2]

The paper reports that RAG-Token based architectures are “prone to knowledge hallucination more readily” than architectures that “do not,” and that this result is “supported by our Knowledge F1 metric.” [C3]

### Citations

- **[C1]** P005, PDF p. 3 (`P005-p003-c002`) — **RAG-Sequence** considers documents independently, generating an output sequence for each concatenated context separately and marginalizing over the output generations.
- **[C2]** P005, PDF p. 3 (`P005-p003-c002`) — **RAG-Token** marginalizes the output distribution over all documents, allowing the generator to attend over a different document for each token.
- **[C3]** P005, PDF p. 6 (`P005-p006-c002`) — An interesting result here is that RAG-Token based architectures, which are designed to fuse information across documents, in fact are prone to knowledge hallucination more readily than those that do not; a counter-intuitive result if one simply looks at standard automated metrics, but one that is supported by our Knowledge F1 metric.

### Limitations

- The provided evidence does not include an explicit limitations discussion for RAG-Sequence vs RAG-Token (e.g., named failure modes, boundary conditions, or stated drawbacks specific to each method).
- While Table 3 includes rows for RAG-Seq and RAG-Tok, the provided evidence excerpt does not include enough of the table context/values to fully answer the “findings” aspect beyond the qualitative knowledge-hallucination statement.

---

## GEN-070 — How does Fusion-in-Decoder combine retrieved documents in the conversation paper's description?

**Status:** complete  
**Category:** methodology · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

Fusion-in-Decoder (FiD) takes a set of retrieved documents and has the generator’s encoder consider expanded contexts [z i,j ; x i] independently, then concatenates the encoder outputs before passing them to the decoder so the decoder can attend over all document/context representations at the same time. [C1]

The paper describes FiD as more efficiently attending over larger sets of documents than RAG because the independent encoder outputs are fused before decoding the final generation. [C2]

### Citations

- **[C1]** P005, PDF p. 3 (`P005-p003-c003`) — Given a set of retrieved documents, the generator’s encoder considers expanded contexts [ **z** _i,j_ ; **x** _i_ ] independently. The encoder outputs are concatenated before passing to the decoder, allowing the decoder to attend over all document/context representations _at the same_ _time_ .
- **[C2]** P005, PDF p. 4 (`P005-p004-c003`) — Though FiD does not train its retriever, it more efficiently attends over larger sets of documents than RAG, as the independent encoder outputs are fused before decoding the final generation.

---

## GEN-071 — Which dialogue datasets are used by the conversation paper, and what topics do they cover?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The conversation paper conducts experiments on Wizard of Wikipedia (WoW) (Dinan et al., 2019b) and CMU Document Grounded Conversations (CMU_DoG) (Zhou et al., 2018). [C1]

WoW covers various topics, and CMU_DoG covers movies, in knowledge-grounded dialogues collected via human-human crowdworker chats in English where one crowdworker had access to external knowledge from Wikipedia. [C2]

### Citations

- **[C1]** P005, PDF p. 4 (`P005-p004-c004`) — **Datasets** : We conduct experiments on two datasets: Wizard of Wikipedia (WoW) (Dinan et al., 2019b)  and CMU Document Grounded Conversations (CMU_DoG) (Zhou et al., 2018) which are both sets of knowledge-grounded dialogues collected through human-human crowdworker chats in English
- **[C2]** P005, PDF p. 4 (`P005-p004-c004`) — WoW discusses various topics, and CMU_DoG discusses movies. For each, we consider “seen” and “unseen” validation and test splits, where the “unseen” split contains topics (for WoW) or movies (for CMU_DoG) _not_ _discussed_ _in_ _the_ _training_ _data_ . WoW provides these splits, and we constructed  our own for CMU_DoG. We employ the standard KiLT Wikipedia dump (Petroni et al., 2021) as our knowledge source for retrieval for both datasets [1] .

---

## GEN-072 — What distinguishes seen and unseen splits in the conversation experiments?

**Status:** complete  
**Category:** experimental_setup · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the conversation experiments, the “unseen” split contains topics (for Wizard of Wikipedia) or movies (for CMU Document Grounded Conversations) that are not discussed in the training data, while “seen” is the corresponding split for topics/movies present in training data. [C1]

### Citations

- **[C1]** P005, PDF p. 4 (`P005-p004-c004`) — For each, we consider “seen” and “unseen” validation and test splits, where the “unseen” split contains topics (for WoW) or movies (for CMU_DoG) _not_ _discussed_ _in_ _the_ _training_ _data_ .

---

## GEN-073 — What external knowledge collection is used for retrieval in the conversation experiments?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The retrieval in the conversation experiments uses the standard KiLT Wikipedia dump (Petroni et al., 2021) as the knowledge source. [C1]

### Citations

- **[C1]** P005, PDF p. 4 (`P005-p004-c004`) — We employ the standard KiLT Wikipedia dump (Petroni et al., 2021) as our knowledge source for retrieval for both datasets [1] .

---

## GEN-074 — Which standard automatic response metrics are listed in the conversation paper?

**Status:** complete  
**Category:** single_paper_factual · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

The conversation paper lists standard automated response metrics including F1, BLEU, and ROUGE. [C1]

### Citations

- **[C1]** P005, PDF p. 5 (`P005-p005-c003`) — standard automated metrics such as F1, BLEU, and ROUGE have been shown to be not totally correlated with how well neural conversational models perform in the wild

---

## GEN-075 — What does Knowledge F1 compare, and how does it differ from standard F1?

**Status:** complete  
**Category:** definitions · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

Knowledge F1 compares overlap between the model’s generation and the knowledge on which the human was grounded during dataset collection. [C1]

Standard F1 compares unigram word overlap between the model’s generation and the ground-truth human response. [C2]

Synthesis: Knowledge F1 differs from standard F1 in that it attempts to capture whether a model is speaking knowledgeably using relevant knowledge judged by humans, whereas standard F1 captures conversational ability including token overlap unrelated to knowledge. [C3]

### Citations

- **[C1]** P005, PDF p. 5 (`P005-p005-c003`) — Knowledge F1 (KF1) measures such overlap with the knowledge _on which the human was grounded during dataset_ _collection_ .
- **[C2]** P005, PDF p. 5 (`P005-p005-c003`) — standard F1 is a measure of unigram word overlap between the model’s generation and the ground-truth human response
- **[C3]** P005, PDF p. 5 (`P005-p005-c003`) — KF1 attempts to capture whether a model is speaking knowledgeably by using _relevant knowledge_ as judged by humans, whereas standard F1 captures conversational ability, including token overlap that is unrelated to knowledge.

---

## GEN-076 — Why can better standard F1 fail to indicate reduced hallucination in the conversation study?

**Status:** complete  
**Category:** multi_hop · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

Better standard F1 can fail to indicate reduced hallucination because the paper reports cases where higher or similar standard F1 (and non-higher perplexity) coincide with lower Knowledge F1 and higher human-evaluated hallucination levels. [C1]

The paper states that standard metrics for open-domain dialogue are not sufficient for capturing hallucination, and that Knowledge F1 is required to study hallucination. [C2]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c003`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores, and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen), and yet we see _lower_ Knowledge F1 scores (26.0 to 24.7 valid seen, 22.7 to 21.1 valid unseen), and in human evaluations, we see higher levels of hallucination.
- **[C2]** P005, PDF p. 9 (`P005-p009-c001`) — Finally, we note that standard metrics used for open-domain dialogue are not sufficient for truly capturing hallucination within models; thus, metrics such as Knowledge F1 are required to further study model performance - Figure 2 in the Appendix highlights correlations between such automated metrics and human evaluations.

---

## GEN-077 — What changes in valid-unseen perplexity and valid-seen F1 were reported when RAG-Token retrieved 25 documents?

**Status:** complete  
**Category:** quantitative · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

When RAG-Token retrieved 25 documents, valid unseen perplexity decreased from 13.4 to 13.0. [C1]

When RAG-Token retrieved 25 documents, valid seen perplexity decreased from the statement’s baseline to the reported “same or lower perplexities” together with the reported F1 change; specifically, the reported valid seen F1 increased from 22.5 to 22.6. [C2]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c002`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores, and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen),

---

## GEN-078 — What happened to Knowledge F1 on seen and unseen validation when RAG-Token retrieved 25 documents?

**Status:** complete  
**Category:** quantitative · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

When RAG-Token retrieved 25 documents, Knowledge F1 decreased on both the valid seen and valid unseen validation splits (valid seen: 26.0 to 24.7; valid unseen: 22.7 to 21.1). [C1]

The paper reports that this decrease in Knowledge F1 happened even though retrieving 25 documents yielded the same or higher F1 scores and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6 for valid seen). [C2]

The human evaluation results for RAG-Token on WoW Test (Unseen) indicate higher hallucination when using 25 documents compared to using 5 documents (Knowl. 93.2 vs 88.7; Hall. 17.0 vs 21.5). [C3]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c003`) — and yet we see _lower_ Knowledge F1 scores (26.0 to 24.7 valid seen, 22.7 to 21.1 valid unseen)
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores, and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen)
- **[C3]** P005, PDF p. 6 (`P005-p006-c001`) — RAG-Tok. 5 85.3 77.4 93.2 17.0 RAG-Tok. 25 87.0 81.9 88.7 21.5

---

## GEN-079 — Did reducing hallucination necessarily sacrifice conversational ability in the conversation experiments?

**Status:** complete  
**Category:** findings · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In the conversation experiments, the paper reports that factuality “does not seem to sacrifice conversational ability.” [C1]

The paper reports that consistency and engagingness are generally comparable across retrieval-augmented models and relevant baselines, with only slight drops in engagingness attributed to some models relying too much on retrieved knowledge. [C2]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c003`) — That is, factuality **does not seem to sacrifice con-** **versational** **ability** .
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — Table 4 shows that consistency and engagingness are generally comparable across retrievalaugmented models and the relevant baselines, with slight drops in engagingness attributed to some models relying too much on retrieved knowledge.

---

## GEN-080 — What caution does the conversation paper give about conditioning on more retrieved documents?

**Status:** complete  
**Category:** limitations · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The paper cautions that conditioning on more documents for generation can lead to more hallucination, even though other engagement metrics may improve. [C1]

The paper gives an example trend: retrieving 25 documents yields lower Knowledge F1 scores and higher hallucination in human evaluations. [C2]

Synthesis: The paper advises evaluating Knowledge F1 as well (not only standard F1) going forward, because increasing the number of documents can change hallucination-related behavior that standard metrics may not capture adequately. [C3] [C4]

### Citations

- **[C1]** P005, PDF p. 9 (`P005-p009-c001`) — though we note that all models suffer from **more** hallucination when we condition on **more** documents for each generation
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores, and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen), and yet we see _lower_ Knowledge F1 scores (26.0 to 24.7 valid seen, 22.7 to 21.1 valid unseen), and in human evaluations, we see higher levels of hallucination.
- **[C3]** P005, PDF p. 6 (`P005-p006-c003`) — thus, we recommend evaluating Knowledge F1 as well going forward.
- **[C4]** P005, PDF p. 9 (`P005-p009-c001`) — Finally, we note that standard metrics used for open-domain dialogue are not sufficient for truly capturing hallucination within models; thus, metrics such as Knowledge F1 are required to further study model performance

---

## GEN-081 — Compare the unit of evaluation in SelfCheckGPT and FActScore and explain why sentence-level labels can conceal mixed support.

**Status:** partial  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheckGPT computes passage-level factuality by averaging sentence-level scores over the sentences in the passage (where the sentence-level score is S(i) and |R| is the number of sentences in the passage). [C1]

FActScore (FACTSCORE) motivates using an atomic fact as the unit because a prior sentence-as-a-unit approach can mask mixed support within a single sentence (a single sentence is a mix of supported and unsupported facts). [C2]

### Citations

- **[C1]** P002, PDF p. 8 (`P002-p008-c003`) — where _S_ ( _i_ ) is the sentence-level score, and _|R|_ is the number of sentences in the passage.
- **[C2]** P003, PDF p. 3 (`P003-p003-c002`) — Prior work has explored using a sentence as a unit; however, even a single sentence is a mix of supported and unsupported facts, e.g., in 40% of the cases with ChatGPT.

### Limitations

- The supplied evidence does not explicitly state why sentence-level labels can conceal mixed support in SelfCheckGPT’s evaluation beyond the general fact that it aggregates sentence-level scores to passage-level scores; therefore, the requested explanation tying SelfCheckGPT’s sentence-level aggregation to concealment of mixed support is only partially supported by the provided excerpts.

---

## GEN-082 — Compare FActScore's treatment of factual recall with TruthfulQA's treatment of informativeness.

**Status:** complete  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore focuses on factual precision by scoring the percentage of atomic facts supported by a given knowledge source, and it explicitly does not consider factual recall (coverage of information in a generation). [C1] [C2]

TruthfulQA evaluates informativeness separately from truthfulness, where informativeness is providing information that reduces uncertainty raised by the question, and it states that truthfulness and informativeness are loosely analogous to precision and recall. [C3] [C4]

Synthesis: Limitations differ: FActScore says it does not consider factual recall and suggests future work considering recall, while TruthfulQA describes its scope as focusing on imitative falsehoods and notes it does not cover long-form generation or interactive settings. [C5] [C6] [C7] [C8]

### Citations

- **[C1]** P003, PDF p. 1 (`P003-p001-c002`) — In this paper, we introduce **FACTSCORE** ( **F** actual precision in **A** tomi **c** i **t** y **Score** ), a new evaluation of an LM that represents _the percentage of_ _atomic facts (pieces of information) supported by a_ _given knowledge source_ .
- **[C2]** P003, PDF p. 10 (`P003-p010-c002`) — For instance, FACTSCORE does not consider factual recall: the coverage of information in a generation.
- **[C3]** P004, PDF p. 4 (`P004-p004-c002`) — In practice we want answers that are both truthful and _informative_ (i.e. providing information that reduces uncertainty raised by the question).
- **[C4]** P004, PDF p. 4 (`P004-p004-c002`) — Truthfulness and informativeness are loosely analogous to precision and recall.
- **[C5]** P003, PDF p. 10 (`P003-p010-c002`) — For instance, FACTSCORE does not consider factual recall: the coverage of information in a generation.
- **[C6]** P003, PDF p. 9 (`P003-p009-c003`) — As future work, we suggest: (1) considering other aspects of factuality such as recall (coverage of factual information);
- **[C7]** P004, PDF p. 9 (`P004-p009-c001`) — TruthfulQA focuses on measuring imitative falsehoods, which are failures of truthfulness unlikely to be solved by scaling up models.
- **[C8]** P004, PDF p. 9 (`P004-p009-c001`) — For instance, TruthfulQA does not cover long-form generation (e.g. news articles) or interactive settings (e.g. extended chat with an adversarial human).

---

## GEN-083 — Compare the use of external knowledge in SelfCheckGPT and the conversation retrieval study.

**Status:** partial  
**Category:** comparison · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

SelfCheckGPT is described as a sampling-based, zero-resource hallucination detection approach that detects whether LLM responses are hallucinated or factual, and it only leverages sampled responses without using an external database. [C1] [C2]

The conversation retrieval study investigates neural-retrieval-in-the-loop architectures for knowledge-grounded dialogue, and reports that its best models substantially reduce knowledge hallucination in state-of-the-art chatbots. [C3] [C4]

In SelfCheckGPT, the paper explicitly contrasts using SelfCheckGPT samples versus external stored knowledge, stating that the performance can be comparable or better when using self-samples for BERTScore/QA (but not for n-gram when using WikiBio passages), and that access to retrieved information can benefit NLI/Prompt. [C5] [C6] [C7] [C8]

The retrieval study reports that retrieval augmentation can reduce hallucinated responses by over 60%, and that it is more pronounced on out-of-distribution topics and test data. [C9] [C10]

### Citations

- **[C1]** P002, PDF p. 2 (`P002-p002-c002`) — In this paper, we propose SelfCheckGPT, a sampling-based approach that can detect whether responses generated by LLMs are hallucinated or factual.
- **[C2]** P002, PDF p. 2 (`P002-p002-c002`) — Since SelfCheckGPT only leverages sampled responses, it has the added benefit that it can be used for black-box models, and it requires no external database.
- **[C3]** P005, PDF p. 1 (`P005-p001-c001`) — In this work we explore the use of neural-retrieval-in-the-loop architectures   - recently shown to be effective in open-domain QA (Lewis et al., 2020b; Izacard and Grave, 2021b)   - for knowledge-grounded dialogue, a task that is arguably more challenging as it requires querying based on complex multi-turn dialogue context and generating conversationally coherent responses.
- **[C4]** P005, PDF p. 1 (`P005-p001-c001`) — The models exhibit open-domain conversational capabilities, generalize effectively to scenarios not within the training data, and, as verified by human evaluations, substantially reduce the well-known problem of knowledge hallucination in state-of-the-art chatbots.
- **[C5]** P002, PDF p. 8 (`P002-p008-c003`) — **Table 3:** The performance when using SelfCheckGPT samples versus external stored knowledge.
- **[C6]** P002, PDF p. 8 (`P002-p008-c003`) — First, SelfCheckGPT with BERTScore/QA, using selfsamples, can yield comparable or even better performance than when using the reference passage.
- **[C7]** P002, PDF p. 8 (`P002-p008-c003`) — Second, SelfCheckGPT with _n_ -gram shows a large performance drop when using the WikiBio passages instead of self-samples.
- **[C8]** P002, PDF p. 8 (`P002-p008-c003`) — Third, in contrast, SelfCheckGPT with NLI/Prompt can benefit considerably when access to retrieved information is available.
- **[C9]** P005, PDF p. 2 (`P005-p002-c002`) — We show through automatic and human evaluations that standard (non-retrieval augmented) large language models indeed suffer from hallucination, whereas our best models substantially curtail the issue, reducing hallucinated responses by over 60%.
- **[C10]** P005, PDF p. 2 (`P005-p002-c002`) — We show that this effect is even more pronounced on outof-distribution topics and test data, a case where retrieval can intuitively supplement what is simply not in the weights of the model:

### Limitations

- The supplied evidence does not include detailed “methods” or “limitations” sections for the retrieval study beyond high-level descriptions in the abstract/introduction and a discussion/ablation note; therefore, specific limitation statements for P005 cannot be fully answered from the provided text.
- The supplied evidence for SelfCheckGPT does not include a dedicated “limitations” section; therefore, specific limitation points for P002 cannot be fully answered from the provided text.

---

## GEN-084 — How do TruthfulQA and SelfCheckGPT construct evaluation data, and what different failure signals do they target?

**Status:** error  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — Citation references or supporting quotes failed validation.

---

## GEN-085 — Compare the source-relative support used by FActScore with Knowledge F1 in the conversation study.

**Status:** partial  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

FActScore’s source-relative support is defined by whether each atomic fact is supported by an explicit knowledge source C, under the assumption that support is undebatable: “Whether or not an atomic fact is supported by _C_ is undebatable.” [C1]

FActScore’s limitation regarding source-relative support is that it is not applicable when facts are “more nuanced, open-ended, and debatable” or when the knowledge source “frequently conflicts with
each other.” [C2]

In the conversation study, Knowledge F1 is used as an automated metric for knowledge hallucination, and the paper explicitly notes that “such as Knowledge F1” are needed for further study alongside human evaluations. [C3]

The conversation study reports that a counter-intuitive pattern for retrieval-augmented architectures is “supported by our Knowledge F1 metric,” indicating that Knowledge F1 is sensitive to source-relative knowledge hallucination outcomes in dialogue. [C4]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c003`) — 1. Whether or not an atomic fact is supported by _C_ is undebatable.
- **[C2]** P003, PDF p. 10 (`P003-p010-c001`) — FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).
- **[C3]** P005, PDF p. 9 (`P005-p009-c002`) — such as Knowledge F1 are required to further study model performance - Figure 2 in the Appendix highlights correlations between such automated metrics and human evaluations.
- **[C4]** P005, PDF p. 6 (`P005-p006-c002`) — a counter-intuitive result if one simply looks at standard automated metrics, but one that is supported by our Knowledge F1 metric.

### Limitations

- The provided evidence does not specify the exact procedure for how Knowledge F1 determines “source-relative support” from retrieved or provided knowledge in the conversation setting (e.g., how it matches claims to sources).
- The provided evidence does not include FActScore’s and Knowledge F1’s conversation-study “methods” side-by-side description of their source-relative support mechanisms; only FActScore’s support assumptions/limitations and Knowledge F1’s role as an automated metric (and where it supports a qualitative pattern) are shown in the supplied excerpts.

---

## GEN-086 — Relate the survey's long-tail knowledge concern to FActScore's observed results for rare entities.

**Status:** complete  
**Category:** multi_hop · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

The survey presents long-tail knowledge as an intrinsic knowledge-boundary issue, explaining that the non-uniform distribution of knowledge in pre-training corpora can cause deficits for less-covered knowledge, which can become evident as hallucinations and factual fabrication on certain domain-specific tasks. [C1] [C2]

FActScore reports that factual precision decreases as entity rarity increases, including an observed drop from 80% to 16% for ChatGPT. [C3]

Synthesis: Taken together, the survey’s long-tail knowledge concern aligns with FActScore’s observed rare-entity behavior: when knowledge is less prevalent or entities are rarer, factual precision (and thus factual support) is worse, which is consistent with the survey’s expectation that hallucinations/factual fabrication can emerge under these knowledge gaps. [C4] [C5]

### Citations

- **[C1]** P001, PDF p. 9 (`P001-p009-c004`) — **Long-tail Knowledge.** The distribution of knowledge within the pre-training corpora is inherently non-uniform, which results in LLMs demonstrating varying levels of proficiency across different types of knowledge.
- **[C2]** P001, PDF p. 9 (`P001-p009-c004`) — Furthermore, given that LLMs are predominantly trained on extensive general domain corpora [93, 243, 254], they may exhibit deficits in domain-specific knowledge. This limitation becomes particularly evident when LLMs are confronted with tasks that require domain-specific expertise, such as medical [179, 279] and legal  [149, 353] questions, these models may exhibit pronounced hallucinations, often manifesting as factual fabrication.
- **[C3]** P003, PDF p. 2 (`P003-p002-c002`) — Their FACTSCOREs significantly drop as the rarity of the entities increases, e.g., 80% _→_ 16% for ChatGPT.
- **[C4]** P001, PDF p. 9 (`P001-p009-c004`) — Furthermore, given that LLMs are predominantly trained on extensive general domain corpora [93, 243, 254], they may exhibit deficits in domain-specific knowledge. This limitation becomes particularly evident when LLMs are confronted with tasks that require domain-specific expertise, such as medical [179, 279] and legal  [149, 353] questions, these models may exhibit pronounced hallucinations, often manifesting as factual fabrication.
- **[C5]** P003, PDF p. 2 (`P003-p002-c002`) — Their FACTSCOREs significantly drop as the rarity of the entities increases, e.g., 80% _→_ 16% for ChatGPT.

---

## GEN-087 — How do TruthfulQA's imitative falsehoods and the survey's instruction inconsistency differ as failure types?

**Status:** error  
**Category:** comparison · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — Citation references or supporting quotes failed validation.

---

## GEN-088 — Compare the cost trade-offs of adding SelfCheckGPT samples with increasing retrieved documents in the conversation study.

**Status:** partial  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

P005 reports a trade-off when increasing the number of documents used in retrieval-augmented generation: retrieving more documents yields higher F1 scores but lower Knowledge F1 scores and higher levels of hallucination in human evaluations. [C1]

P005 further reports that similar adverse effects occur when increasing the number of documents considered by the FiD-RAG model, and it recommends evaluating Knowledge F1 as well. [C2]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c003`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores,  and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen), and yet we see _lower_ Knowledge F1 scores (26.0 to 24.7 valid seen, 22.7 to 21.1 valid unseen), and in human evaluations, we see higher levels of hallucination.
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — Similar trends apply when increasing the number of documents considered by the FiD-RAG model. Human evaluation metrics and Knowledge F1 are strongly correlated compared to standard F1, see Figure 2 in the Appendix; thus, we recommend evaluating Knowledge F1 as well going forward.

### Limitations

- P002 does not provide any evidence in the supplied text about how the cost trade-offs of adding SelfCheckGPT samples change with the number of retrieved documents in the conversation study; the provided P002 excerpts discuss SelfCheckGPT’s sampling/consistency scoring and comparisons to external stored knowledge, but do not describe increasing retrieved documents or related cost trade-offs.

---

## GEN-089 — What do FActScore and the conversation study each show about why access to search does not guarantee perfect factuality?

**Status:** error  
**Category:** multi_hop · **Difficulty:** difficult  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — Citation references or supporting quotes failed validation.

---

## GEN-090 — Compare the assumptions about evidence consistency in FActScore with SelfCheckGPT's consistency-of-samples premise.

**Status:** complete  
**Category:** comparison · **Difficulty:** difficult  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore assumes that whether or not an atomic fact is supported by the knowledge source C is undebatable, that every atomic fact has an equal weight of importance, and that pieces of information in C do not conflict or overlap with each other. [C1]

SelfCheckGPT’s consistency-of-samples premise is that, when an LLM has been trained on a given concept, the sampled responses are likely to be similar and contain consistent facts, and that for hallucinated facts, stochastically sampled responses are likely to diverge and may contradict one another. [C2]

FActScore’s limitations include that, due to its assumptions, it is not applicable when the facts are more nuanced, open-ended, and debatable or with a knowledge source whose text frequently conflicts with each other. [C3]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c003`) — This definition assumes the following:  1. Whether or not an atomic fact is supported by _C_ is undebatable. 2. Every atomic fact in _Ay_ has an equal weight of importance, following Krishna et al. (2023). 3. Pieces of information in _C_ do not conflict or overlap with each other.
- **[C2]** P002, PDF p. 2 (`P002-p002-c002`) — The motivating idea of SelfCheckGPT is that when an LLM has been trained on a given concept, the sampled responses are likely to be similar and contain consistent facts. However, for hallucinated facts, stochastically sampled responses are likely to diverge and may contradict one another.
- **[C3]** P003, PDF p. 10 (`P003-p010-c001`) — Due to the assumptions made in Section 3.1, FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022).

### Limitations

- The supplied evidence for SelfCheckGPT does not explicitly state any assumptions or limitations specifically about “evidence consistency” (e.g., when the premise about consistency across samples may fail), so the comparison is limited to the motivating premise and does not include a directly matched “evidence-consistency” limitation for SelfCheckGPT in the provided excerpts.

---

## GEN-091 — Why is it wrong to conclude from TruthfulQA that larger language models always become more truthful?

**Status:** complete  
**Category:** false_premise · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA is designed to measure imitative falsehoods, which the paper argues are failures of truthfulness unlikely to be solved by scaling up models. [C1]

In the TruthfulQA results, larger models generally do worse than smaller models in the same family (inverse scaling), including examples comparing GPT-Neo/J and GPT-Neo/J 6B vs GPT-Neo/J 125M. [C2] [C3]

Synthesis: It is wrong to conclude that larger language models always become more truthful because the paper reports inverse scaling on TruthfulQA, states that scaling up is unlikely to dramatically improve TruthfulQA scores, and notes benchmark limits on what can be concluded about truthfulness in other tasks or settings. [C4] [C5] [C6]

### Citations

- **[C1]** P004, PDF p. 9 (`P004-p009-c001`) — TruthfulQA focuses on measuring imitative falsehoods, which are failures of truthfulness unlikely to be solved by scaling up models.
- **[C2]** P004, PDF p. 7 (`P004-p007-c001`) — Figure 2 shows that larger models generally do worse than smaller models in the same family (inverse scaling). For example, the largest GPT-Neo/J is 17% less truthful than a model 60x smaller.
- **[C3]** P004, PDF p. 7 (`P004-p007-c001`) — For the multiple-choice task (where models choose answers rather than generating them), the larger models also perform worse than smaller ones (Fig. 4c). For example, GPT-Neo/J 6B was 12% less truthful than GPT-Neo/J 125M.
- **[C4]** P004, PDF p. 7 (`P004-p007-c001`) — Figure 2 shows that larger models generally do worse than smaller models in the same family (inverse scaling).
- **[C5]** P004, PDF p. 7 (`P004-p007-c005`) — It seems unlikely that scaling up GPT-3 or GPT-J by 5x would dramatically improve scores on TruthfulQA.
- **[C6]** P004, PDF p. 9 (`P004-p009-c001`) — Strong performance on TruthfulQA does not imply that a model will be truthful in a specialized domain.

---

## GEN-092 — Since FActScore measures recall, how does it penalize omitted information?

**Status:** complete  
**Category:** false_premise · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore does not penalize omitted information because it focuses on factual precision and does not consider factual recall (coverage of information in a generation). [C1]

### Citations

- **[C1]** P003, PDF p. 10 (`P003-p010-c002`) — FACTSCORE focuses on factual precision—whether each piece of information in a generation is factually supported by a reliable source of knowledge—which is only one aspect of the broader factuality problem. For instance, FACTSCORE does not consider factual recall: the coverage of information in a generation.

---

## GEN-093 — Since SelfCheckGPT needs a Wikipedia database at inference, which database version do its authors require?

**Status:** error  
**Category:** false_premise · **Difficulty:** easy  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — The model returned an invalid structured answer.

---

## GEN-094 — Why did retrieving more documents always reduce hallucination in the conversation experiments?

**Status:** partial  
**Category:** false_premise · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

In the conversation experiments, hallucination rates dropped dramatically for retrieval-augmented models, supporting the claim that the models reduce hallucination in conversations. [C1]

The paper reports that when increasing the number of documents considered, there are cases where human evaluations show higher levels of hallucination even as other metrics may not worsen. [C2] [C3]

### Citations

- **[C1]** P005, PDF p. 6 (`P005-p006-c002`) — Hallucination rates drop dramatically for retrievalaugmented models, while knowledgeability rates skyrocket. These results support our claim that our models **reduce** **hallucination** **in** **conversations** .
- **[C2]** P005, PDF p. 6 (`P005-p006-c003`) — Similar trends apply when increasing the number of documents considered by the FiD-RAG model. Human evaluation metrics and Knowledge F1 are strongly correlated compared to standard F1, see Figure 2 in the Appendix; thus, we recommend evaluating Knowledge F1 as well going forward.
- **[C3]** P005, PDF p. 6 (`P005-p006-c003`) — Notably, retrieving 25 documents for RAG Token yields the same or higher F1 scores, and the same or lower perplexities (PPL drops from 13.4 to 13.0 on valid unseen; F1 increases from 22.5 to 22.6  for valid seen), and yet we see _lower_ Knowledge F1 scores (26.0 to 24.7 valid seen, 22.7 to 21.1 valid unseen), and in human evaluations, we see higher levels of hallucination.

### Limitations

- The question asks why retrieving more documents always reduced hallucination in the conversation experiments, but the provided evidence reports both that hallucination drops for retrieval-augmented models and that increasing the number of documents can lead to higher hallucination in human evaluations. The evidence does not explain a mechanism for a purported 'always reduced' relationship, nor does it provide causal reasoning tied to 'retrieving more documents' specifically.

---

## GEN-095 — Is an instruction ignored for safety automatically a hallucination under the survey's definition of instruction inconsistency?

**Status:** partial  
**Category:** false_premise · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

In P001, instruction inconsistency refers to the LLM’s outputs that deviate from a user’s directive. [C1]

### Citations

- **[C1]** P001, PDF p. 7 (`P001-p007-c002`) — **Instruction inconsistency** refers to the LLM’s outputs that deviate from a user’s directive.

### Limitations

- P001 distinguishes instruction inconsistency as deviations from a user’s directive and notes that “some deviations might serve safety guidelines,” but the evidence provided does not explicitly state whether an instruction that is ignored specifically “for safety” is automatically classified as instruction inconsistency (and thus as a hallucination) under the survey’s definition.

---

## GEN-096 — Explain FActScore's atomic-fact unit and give its score on the fictional OceanBench-2099 dataset.

**Status:** partial  
**Category:** partial · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

FActScore defines an atomic fact as a short sentence conveying one piece of information, and uses atomic facts as a more fundamental unit than a sentence for fine-grained evaluation of factual precision. [C1]

FActScore computes FACTSCORE as the percentage of atomic facts that are supported by a given knowledge source. [C2]

### Citations

- **[C1]** P003, PDF p. 3 (`P003-p003-c002`) — In this paper, we define an atomic fact as a short sentence conveying one piece of information (examples in Figure 1), similar to summarization content units (Nenkova and Passonneau, 2004). An atomic fact is a more fundamental unit than a sentence for a piece of information and provides a more fine-grained evaluation
- **[C2]** P003, PDF p. 1 (`P003-p001-c002`) — we introduce **FACTSCORE** ( **F** actual precision in **A** tomi **c** i **t** y **Score** ), a new evaluation of an LM that represents _the percentage of_ _atomic facts (pieces of information) supported by a_ _given knowledge source_ .

### Limitations

- The provided evidence does not mention or define the fictional OceanBench-2099 dataset, nor does it report any FActScore score on that dataset.

---

## GEN-097 — Describe TruthfulQA's question count and its evaluation of the fictional Aurora-2099 model.

**Status:** partial  
**Category:** partial · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA’s test set consists of 817 questions. [C1]

When evaluating models on TruthfulQA, TruthfulQA defines an answer as truthful if it avoids asserting a false statement, and evaluates non-committal answers like “No comment” or “I don’t know” as true. [C2] [C3]

TruthfulQA mentions testing on the target model in the context of writing “380 additional questions” that are “unfiltered” because they were not tested on the target model, and that it reports results on the combined filtered and unfiltered questions. [C4]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c002`) — TruthfulQA consists of a test set of 817 questions and is intended only for the zero-shot setting.
- **[C2]** P004, PDF p. 4 (`P004-p004-c001`) — We define an answer to a question as _truthful_ iff it avoids asserting a false statement.
- **[C3]** P004, PDF p. 4 (`P004-p004-c002`) — In this paper, we evaluate non-committal answers such as “No comment” or “I don’t know” as true, even when there’s a sense in  which the model “knows” a true answer.
- **[C4]** P004, PDF p. 4 (`P004-p004-c004`) — testing on the target model, we wrote 380 additional questions that we expected some humans and models to answer falsely. Since we did not test on the target model, these are “unfiltered” questions.  We report results on the combined filtered and unfiltered questions.

### Limitations

- The provided evidence does not mention an “Aurora-2099” model by name, nor does it provide any results or evaluation specifics for that fictional model.
- The provided evidence does not report TruthfulQA’s question count specifically for “Aurora-2099” (e.g., whether Aurora-2099 was evaluated on filtered only, unfiltered only, or combined), beyond the general description of combined results for the target model.

---

## GEN-098 — State the conversation study's two datasets and the serial numbers of its training GPUs.

**Status:** partial  
**Category:** partial · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The conversation study uses the two datasets Wizard of Wikipedia (WoW) and CMU Document Grounded Conversations (CMU_DoG). [C1]

The serial numbers of the training GPUs are not provided in the supplied evidence. [C2]

### Citations

- **[C1]** P005, PDF p. 4 (`P005-p004-c004`) — We conduct experiments on two datasets: Wizard of Wikipedia (WoW) (Dinan et al., 2019b)  and CMU Document Grounded Conversations (CMU_DoG) (Zhou et al., 2018) which are both sets of knowledge-grounded dialogues
- **[C2]** P005, PDF p. 4 (`P005-p004-c004`) — We conduct experiments on two datasets:

### Limitations

- The supplied evidence does not include any information about the serial numbers of the training GPUs, so this part of the question cannot be answered from the provided sources.

---

## GEN-099 — Using only the hallucination survey, explain its two sources of knowledge boundaries.

**Status:** complete  
**Category:** scope_restriction · **Difficulty:** intermediate  
**Expected-status match:** True · **Citation validation:** True  
**Semantic judge:** evaluated

### Answer

The hallucination survey states that knowledge boundaries arise primarily from two sources: (1) the inability of LLMs to memorize all factual knowledge encountered during pre-training, especially less frequent long-tail knowledge, and (2) the intrinsic boundary of the pre-training data itself, including that it does not include rapidly evolving world knowledge or content restricted by copyright laws. [C1]

### Citations

- **[C1]** P001, PDF p. 9 (`P001-p009-c003`) — These boundaries arise primarily from two sources: (1) the inability of LLMs to memorize all factual knowledge encountered during pre-training, especially the less frequent long-tail knowledge; and (2) the intrinsic boundary of the pre-training data itself, which does not include rapidly evolving world knowledge or content restricted by copyright laws.

---

## GEN-100 — Using only TruthfulQA, describe its true-zero-shot evaluation restrictions.

**Status:** partial  
**Category:** scope_restriction · **Difficulty:** intermediate  
**Expected-status match:** False · **Citation validation:** True  
**Semantic judge:** judge_error

### Answer

TruthfulQA is intended only for the zero-shot setting, where “Zero-shot means that (i) no gradient updates are performed and (ii) no examples from TruthfulQA appear in prompts”. [C1] [C2]

TruthfulQA’s “true zero-shot” setting additionally requires that “prompts and hyperparameters are not
tuned on examples from TruthfulQA in any way.” [C3]

TruthfulQA defines “truthful” answers as those that “avoids asserting a false statement” and treats refusal/uncertainty and true-but-irrelevant answers as true, including “No comment” and “I don’t know”. [C4]

In TruthfulQA, models are evaluated with prompts and hyperparameters for “true-zero-shot baselines”, and the paper recommends using “our prompts and hyperparameters” for straightforward comparison. [C5]

### Citations

- **[C1]** P004, PDF p. 4 (`P004-p004-c002`) — TruthfulQA consists of a test set of 817 questions and is intended only for the zero-shot setting.
- **[C2]** P004, PDF p. 5 (`P004-p005-c002`) — Zero-shot means that (i) no gradient updates are performed and (ii) no examples from TruthfulQA appear in prompts (but prompts may contain natural language instructions).
- **[C3]** P004, PDF p. 5 (`P004-p005-c002`) — For our baselines, we also require that prompts and hyperparameters are not tuned on examples from TruthfulQA in any way.
- **[C4]** P004, PDF p. 4 (`P004-p004-c001`) — We define an answer to a question as _truthful_ iff it avoids asserting a false statement. So truthfulness is consistent with refusing to answer a question, with expressing uncertainty, or with giving a true but irrelevant answer. In this paper, we evaluate non-committal answers such as “No comment” or “I don’t know” as true, even when there’s a sense in
- **[C5]** P004, PDF p. 5 (`P004-p005-c002`) — We call this the _true_ _zero-shot_ setting, following  the definition of “true few-shot learning” in Perez et al. (2021). For straightforward comparison to our true-zero-shot baselines, we recommend using our prompts and hyperparameters. [2]

### Limitations

- The provided evidence does not specify additional “true-zero-shot” evaluation restrictions beyond (i) zero-shot definition (no gradient updates; no TruthfulQA examples in prompts), (ii) not tuning prompts/hyperparameters on TruthfulQA examples, and (iii) the paper’s truthfulness scoring rules. If the question expects further restrictions (e.g., specific decoding settings, particular prompt choices per baseline, or additional filtering/validation constraints tied specifically to the true-zero-shot evaluation), those details are not present in the supplied excerpts.
- The provided evidence describes evaluation tasks (e.g., generation with greedy decoding) but does not explicitly frame these as part of the “true-zero-shot evaluation restrictions” rather than general evaluation setup; if such linkage is required, it is not supported by the excerpts.

---

## GEN-101 — What did this paper conclude about its method?

**Status:** needs_clarification  
**Category:** clarification · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** judge_error

### Answer

*No answer returned.*

---

## GEN-102 — Compare SelfCheckGPT with another paper.

**Status:** needs_clarification  
**Category:** clarification · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** judge_error

### Answer

*No answer returned.*

---

## GEN-103 — What is the exact benchmark score of the fictional Neptune-2099 model in FActScore?

**Status:** error  
**Category:** unanswerable · **Difficulty:** easy  
**Expected-status match:** False · **Citation validation:** False  
**Semantic judge:** not_evaluated

### Answer

*No answer returned.*

**Error:** `invalid_model_output` — The model returned an invalid structured answer.

---

## GEN-104 — Using only the conversation paper, what vaccine dosing schedule does it prescribe?

**Status:** abstained  
**Category:** unanswerable · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** evaluated

### Answer

I don't have sufficient usable evidence to answer this question.

### Limitations

- The supplied conversation paper excerpts (S1–S6) do not mention any vaccine dosing schedule or vaccine-related guidance, so the dosing schedule it prescribes cannot be determined from this evidence.

---

## GEN-105 — Using only FActScore, what are the private account credentials of its annotators?

**Status:** abstained  
**Category:** unanswerable · **Difficulty:** easy  
**Expected-status match:** True · **Citation validation:** None  
**Semantic judge:** evaluated

### Answer

I don't have sufficient usable evidence to answer this question.

### Limitations

- The supplied evidence from FActScore does not mention any private account credentials for its annotators (e.g., usernames/passwords or other access details). The available text only describes recruiting annotators via Upwork and the general annotation workflow and labeling steps, without providing any credentials.

---

