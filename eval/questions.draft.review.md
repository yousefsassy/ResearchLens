# ResearchLens retrieval questions - DRAFT FOR HUMAN REVIEW

**All 20 records are unverified candidate labels. Do not use this draft for final accuracy evaluation.**

Four source-specific questions per paper cover definitions, taxonomy, detection, annotation, scoring, assumptions, limitations, benchmark construction, architecture, and generalization. This is a starter review set, not a representative or exhaustive benchmark. No cross-paper questions or unanswerable cases are included in this first batch.

Corpus: 638 chunks. Fingerprint: `817fa270d2b7842bd86dbdb0a5d5f89d08170eb3c5937a184851098f4cab1713`. All proposed chunk IDs exist, every PDF filename/page is valid, and supporting text is copied exactly from the current corpus. These checks establish structural validity, not human approval or completeness of relevance labels.

The JSONL uses the existing loader schema: `question_id`, `question`, `relevant_chunk_ids`, and optional `metadata`. It intentionally does not set `is_template`, because these are concrete candidates, not placeholders. **The unchanged loader accepts structurally valid drafts and ignores review status. Human approval is a workflow gate, not an enforced evaluation-script gate.**

## Review table

Excerpts below are shortened previews with whitespace collapsed. Full, unchanged supporting chunk text and draft reference answers appear after the table. All page numbers are one-based PDF pages, not printed article page numbers.

| ID | Candidate question | Proposed relevant chunks | PDF references | Supporting-text preview | Decision |
|---|---|---|---|---|---|
| DRAFT-Q001 | According to the hallucination survey, how do intrinsic and extrinsic hallucinations differ? | P001-p005-c003 | P001_hallucination_survey.pdf, PDF p. 5 | Specifically, _intrinsic hallucinations_ pertain to the model outputs that directly conflict with the provided source context. On the other hand, _extrinsic hallucinations_ involve outputs that cannot be verified using the provided source context or external knowledge bases. This means the generated text is neither supported by nor directly contradicts the available information, rendering the output unverifiable and ... | PENDING |
| DRAFT-Q002 | In the survey taxonomy, what distinguishes factual contradiction from factual fabrication? | P001-p006-c003<br>P001-p006-c004 | P001_hallucination_survey.pdf, PDF p. 6<br>P001_hallucination_survey.pdf, PDF p. 6 | **Factual Contradiction** refers to situations where the LLM’s output contains facts that can be grounded in real-world information, but present contradictions. This type of hallucination occurs most frequently and arises from diverse sources, encompassing the LLM’s capture, storage, and expression of factual knowledge. Depending on the error type of contradictions, it can be further divided into two subcategories: _ ...<br>**Factual Fabrication** refers to instances where the LLM’s output contains facts that are unverifiable against established real-world knowledge. This can be further divided into _unverifiability_ _hallucination_ and _overclaim hallucination_ . ACM Transactions on Information Systems, Vol. 1, No. 1, Article 1. Publication date: January 2024. ... | PENDING |
| DRAFT-Q003 | What three subtypes of faithfulness hallucination does the survey identify, and what does each mean? | P001-p007-c002 | P001_hallucination_survey.pdf, PDF p. 7 | **Instruction inconsistency** refers to the LLM’s outputs that deviate from a user’s directive. While some deviations might serve safety guidelines, the inconsistencies here signify unintentional misalignment with non-malicious user instructions. As described in Table 1, the user’s actual intention is translation, However, the LLM erroneously deviated from the user’s instruction and performed a question-answering tas ... | PENDING |
| DRAFT-Q004 | Which three broad sources of LLM hallucination organize the survey discussion of causes? | P001-p007-c003 | P001_hallucination_survey.pdf, PDF p. 7 | LLM hallucinations have multifaceted origins, spanning the entire spectrum of LLMs’ capability acquisition process. In this section, we delve into the root causes of hallucinations in LLMs, primarily categorized into three key aspects: (1) _Data_ (§3.1), (2) _Training_ (§3.2), and (3) _Inference_ (§3.3). **3.1** **Hallucination from Data** Data for training LLMs are comprised of two primary components: (1) pre-trai ... | PENDING |
| DRAFT-Q005 | How can SelfCheckGPT detect possible hallucinations without an external knowledge database? | P002-p002-c002 | P002_selfcheckgpt.pdf, PDF p. 2 | The motivating idea of SelfCheckGPT is that when an LLM has been trained on a given concept, the sampled responses are likely to be similar and contain consistent facts. However, for hallucinated facts, stochastically sampled responses are likely to diverge and may contradict one another. By sampling multiple responses from an LLM, one can measure information consistency between the different responses and determine ... | PENDING |
| DRAFT-Q006 | How does SelfCheckGPT-Prompt convert Yes, No, and unrecognized responses into an inconsistency score? | P002-p005-c002 | P002_selfcheckgpt.pdf, PDF p. 5 | Initial investigation showed that GPT-3 (textdavinci-003) will output either Yes or No 98% of the time, while any remaining outputs can be set to N/A. The output from prompting when comparing the _i_ -th sentence against sample _S_ _[n]_ is converted to score _x_ _[n]_ _i_ [through the mapping {][Yes][:] [0.0,][ No][:] [1.0,] N/A: 0.5}. The final inconsistency score is then calculated as: Prompt( _i_ ) = [1] _S_ _N ... | PENDING |
| DRAFT-Q007 | Which sentence-level factuality labels and numeric values were used to annotate the SelfCheckGPT WikiBio passages? | P002-p005-c003 | P002_selfcheckgpt.pdf, PDF p. 5 | We then annotate the sentences of the generated passages using the guidelines shown in Figure 3 such that each sentence is classified as either: - **Major Inaccurate** (Non-Factual, **1** ): The sentence is entirely hallucinated, i.e. the sentence is unrelated to the topic. - **Minor** **Inaccurate** (Non-Factual, **0.5** ): The sentence consists of some non-factual information, but the sentence is related to the ... | PENDING |
| DRAFT-Q008 | How did the SelfCheckGPT authors obtain human passage-level factuality scores from sentence annotations? | P002-p006-c001 | P002_selfcheckgpt.pdf, PDF p. 6 | Furthermore, passage-level scores are obtained by averaging the sentence-level labels in each passage. The distribution of passage-level scores is shown in Figure 4, where we observe a large peak at +1.0. We refer to the points at this peak as _total_ _hallucination_, which occurs when the information of the response is unrelated to the real concept and is entirely fabricated by the LLM. 30 25 20 15 10 5 0 0. ... | PENDING |
| DRAFT-Q009 | Why does FActScore evaluate atomic facts instead of assigning one factuality label to each whole sentence? | P003-p003-c002 | P003_factscore.pdf, PDF p. 3 | **Key** **idea** **1:** **Atomic** **fact** **as** **a** **unit.** Long-form text consists of many pieces of information that can each be either true or false. Prior work has explored using a sentence as a unit; however, even a single sentence is a mix of supported and unsupported facts, e.g., in 40% of the cases with ChatGPT. Previous and concurrent work either (1) defines an additional label of partial support (Man ... | PENDING |
| DRAFT-Q010 | How does the Retrieve-to-LM variant of the FActScore estimator decide whether an atomic fact is supported? | P003-p006-c003 | P003_factscore.pdf, PDF p. 6 | **Retrieve** _→_ **LM** retrieves passages from the given knowledge source and then prompts the LMEVAL. It first retrieves _k_ passages, constructs the prompt by concatenating retrieved passages, the given atomic fact, and “True or False?”, and feeds it to the LMEVAL to get the prediction. **Nonparametric Probability (NP)** makes a judgment based on a nonparametric likelihood. It masks out each token in the atomic f ... | PENDING |
| DRAFT-Q011 | Why can FActScore miss incomplete answers, and which additional statistics do its authors recommend reporting? | P003-p010-c002 | P003_factscore.pdf, PDF p. 10 | **Beyond factual precision.** FACTSCORE focuses on factual precision—whether each piece of information in a generation is factually supported by a reliable source of knowledge—which is only one aspect of the broader factuality problem. For instance, FACTSCORE does not consider factual recall: the coverage of information in a generation. FACTSCORE does not penalize a model that abstains from responding too frequently ... | PENDING |
| DRAFT-Q012 | What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its applicability? | P003-p003-c003<br>P003-p010-c001 | P003_factscore.pdf, PDF p. 3<br>P003_factscore.pdf, PDF p. 10 | This definition assumes the following: 1. Whether or not an atomic fact is supported by _C_ is undebatable. 2. Every atomic fact in _Ay_ has an equal weight of importance, following Krishna et al. (2023). 3. Pieces of information in _C_ do not conflict or overlap with each other. In the rest of the paper, we propose to use people biographies as _X_ and Wikipedia as _C_ because they satisfy these assumptions to a re ...<br>Due to the assumptions made in Section 3.1, FACTSCORE is not applicable when the facts are more nuanced, open-ended, and debatable (Chen et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with each other (Wadden et al., 2022). Moreover, FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional or implicit deception. **Limitation in our est ... | PENDING |
| DRAFT-Q013 | What are the imitative falsehoods that TruthfulQA questions are designed to elicit? | P004-p004-c003 | P004_truthfulqa.pdf, PDF p. 4 | The questions in TruthfulQA were designed to be “adversarial” in the sense of testing for a _weak-_ _ness_ in the truthfulness of language models (rather than testing models on a useful task). In particular, the questions test a weakness to imitative falsehoods: false statements with high likelihood on the training distribution. We constructed the questions using the following adversarial procedure, with GPT-3-175B ( ... | PENDING |
| DRAFT-Q014 | Why can answering No comment to every TruthfulQA question count as truthful, yet still be undesirable? | P004-p004-c001<br>P004-p004-c002 | P004_truthfulqa.pdf, PDF p. 4<br>P004_truthfulqa.pdf, PDF p. 4 | We define an answer to a question as _truthful_ iff it avoids asserting a false statement. So truthfulness is consistent with refusing to answer a question, with expressing uncertainty, or with giving a true but irrelevant answer. In this paper, we evaluate non-committal answers such as “No comment” or “I don’t know” as true, even when there’s a sense in ...<br>which the model “knows” a true answer. [1] It follows from our definition that a model is perfectly truthful if it answers “No comment” for every question. In practice we want answers that are both truthful and _informative_ (i.e. providing information that reduces uncertainty raised by the question). So in assessing models, we also include evaluations of informativeness. Truthfulness and informativeness are loosely ... | PENDING |
| DRAFT-Q015 | How were the filtered and unfiltered subsets of TruthfulQA constructed, and how many questions did each contain? | P004-p004-c003 | P004_truthfulqa.pdf, PDF p. 4 | 1. We wrote questions that some humans would answer falsely. We tested them on the target model and filtered out questions that the model consistently answered correctly when multiple random samples were generated at nonzero temperatures. We produced 437 questions this way, which we call the “filtered” questions (Wallace and Boyd-Graber, 2018). 2. Using this experience of testing on the target model, we wrote 380 ad ... | PENDING |
| DRAFT-Q016 | What restrictions define the true zero-shot setting used for the TruthfulQA baselines? | P004-p005-c002 | P004_truthfulqa.pdf, PDF p. 5 | **Prompts.** TruthfulQA is intended as a zero-shot benchmark (Brown et al., 2020; Wei et al., 2021). Zero-shot means that (i) no gradient updates are performed and (ii) no examples from TruthfulQA appear in prompts (but prompts may contain natural language instructions). For our baselines, we also require that prompts and hyperparameters are not tuned on examples from TruthfulQA in any way. We call this the _true_ _ ... | PENDING |
| DRAFT-Q017 | In Retrieval Augmentation Reduces Hallucination in Conversation, how do RAG-Sequence and RAG-Token differ in their use of retrieved documents? | P005-p003-c002 | P005_retrieval_reduces_hallucination.pdf, PDF p. 3 | **RAG-Sequence** considers documents independently, generating an output sequence for each concatenated context separately and marginalizing over the output generations. **RAG-Token** marginalizes the output distribution over all documents, allowing the generator to attend over a different document for each token. Though **d** ( **z** _j_ ) remains fixed during training, token losses are propagated to the retriever i ... | PENDING |
| DRAFT-Q018 | How does Fusion-in-Decoder combine retrieved documents, and is its retriever updated during training in the baseline described by the conversation paper? | P005-p003-c003<br>P005-p004-c003 | P005_retrieval_reduces_hallucination.pdf, PDF p. 3<br>P005_retrieval_reduces_hallucination.pdf, PDF p. 4 | Izacard and Grave (2021b) introduce the **FiD** (Fusion-in-Decoder) method. Given a set of retrieved documents, the generator’s encoder considers expanded contexts [ **z** _i,j_ ; **x** _i_ ] independently. The encoder outputs are concatenated before passing to the decoder, allowing the decoder to attend over all document/context representations _at the same_ _time_ . Despite fixing the retriever throughout training, ...<br>Though FiD does not train its retriever, it more efficiently attends over larger sets of documents than RAG, as the independent encoder outputs are fused before decoding the final generation. FiD has been applied with great success to open-domain QA tasks primarily with BM25 retrievers or neural retrievers pre-trained on QA datasets (Izacard and Grave, 2021b; Xiong et al., 2021). However, knowledge-grounded dialogue ... | PENDING |
| DRAFT-Q019 | Why does the conversation paper propose DPR-Poly reranking, and how does it increase interaction between a dialogue context and candidate documents? | P005-p003-c004 | P005_retrieval_reduces_hallucination.pdf, PDF p. 3 | In DPR a dialogue context and a candidate document interact only via a final dot-product similarity score. However, allowing more interaction between the two yields superior results in various information retrieval and ranking tasks (Humeau et al., 2020; Khattab and Zaharia, 2020). Full crossattention is intractable when scaling to millions of candidate documents, so recent work allows latestage interaction between c ... | PENDING |
| DRAFT-Q020 | Which datasets were used in the conversation retrieval study, and what makes their unseen evaluation splits different from the training data? | P005-p004-c004 | P005_retrieval_reduces_hallucination.pdf, PDF p. 4 | **Datasets** : We conduct experiments on two datasets: Wizard of Wikipedia (WoW) (Dinan et al., 2019b) and CMU Document Grounded Conversations (CMU_DoG) (Zhou et al., 2018) which are both sets of knowledge-grounded dialogues collected through human-human crowdworker chats in English, where one of the crowdworkers had access to external knowledge from Wikipedia; WoW discusses various topics, and CMU_DoG discusses mov ... | PENDING |

## Manual review and approval

1. Open each cited PDF at the PDF page number. Read the surrounding paragraphs and compare them with the full chunks below; check column order, equations, tables, and qualifiers.
2. Confirm the question is clear and answerable. Check the draft answer against the paper; edit or reject it if the scope, terminology, or claim is wrong.
3. Judge every proposed chunk for direct relevance. For multi-part questions, note which part each chunk supports. Remove merely topical matches and search the rest of the corpus for other valid supporting chunks, including overlapping passages. These labels are not exhaustive.
4. Resolve extraction issues before approving. Original `needs_review` and `review_flags` are copied unchanged; empty flags do not prove correctness. Reviewer cautions below record additional issues without modifying ingestion outputs.
5. Record ACCEPT, EDIT, or REJECT, your name, date, corrected IDs, and reasons. For approved records only, set `metadata.human_verified` to true, `review_status` to approved, and populate `reviewer`, `reviewed_at` (ISO date), and `review_decision`. Leave pending or rejected records unverified.
6. Return decisions by question ID, for example: `DRAFT-Q006: EDIT - use these IDs ...; rationale ...`. Ask a second team member to review disputed or multi-passage labels. Do not approve all records solely because schema validation passed.
7. After approval, create a separate approved dataset from accepted records while preserving this draft as provenance. Recheck the corpus fingerprint and load it with the existing loader. Do not run final evaluation or expand this set until review is complete.

**Metric caveat:** existing Recall@k counts the fraction of labelled chunks retrieved; Hit@k and MRR reward any labelled match. For questions needing complementary chunks, these metrics do not certify that all evidence required for a full answer was retrieved. Overlapping or omitted valid chunks can affect scores. Freeze a relevance policy before final evaluation.

## Detailed evidence

### DRAFT-Q001 - PENDING

According to the hallucination survey, how do intrinsic and extrinsic hallucinations differ?

**Draft reference answer (unverified):** Intrinsic hallucinations directly conflict with the supplied source context. Extrinsic hallucinations cannot be verified from that context or external knowledge and are neither supported nor directly contradicted by the available information.

**Reviewer caution:** Check the definition as stated in this survey; terminology can differ across papers.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P001-p005-c003** - [P001_hallucination_survey.pdf, PDF page 5](../data/raw/P001_hallucination_survey.pdf#page=5)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
into the training loop has proven effective in enhancing the
alignment of LLMs, guiding them toward producing high-quality and harmless responses.

**2.3** **Hallucinations in Large Language Models**

The concept of hallucination traces its roots to the fields of pathology and psychology and is
defined as _the_ _perception_ _of_ _an_ _entity_ _or_ _event_ _that_ _is_ _absent_ _in_ _reality_ [202]. Within the realm
of NLP, hallucination is typically referred to as a phenomenon in which the generated content
appears nonsensical or unfaithful to the provided source content [89, 208]. This concept bears a
loose resemblance to the phenomenon of hallucination observed in human psychology. Generally,
hallucinations in natural language generation tasks can be categorized into two primary types:
_intrinsic hallucination_ and _extrinsic hallucination_ [126, 136, 174].

Specifically, _intrinsic hallucinations_ pertain to the model outputs that directly conflict with the
provided source context. On the other hand, _extrinsic hallucinations_ involve outputs that cannot be
verified using the provided source context or external knowledge bases. This means the generated
text is neither supported by nor directly contradicts the available information, rendering the output
unverifiable and potentially misleading.
```

### DRAFT-Q002 - PENDING

In the survey taxonomy, what distinguishes factual contradiction from factual fabrication?

**Draft reference answer (unverified):** Factual contradiction conflicts with real-world facts that can be grounded; factual fabrication contains claims unverifiable against established real-world knowledge.

**Reviewer caution:** The two proposed chunks supply different parts of the comparison. Use the prose definitions below Table 1 rather than its flattened layout.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P001-p006-c003** - [P001_hallucination_survey.pdf, PDF page 6](../data/raw/P001_hallucination_survey.pdf#page=6)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
incorrectly states that the Nile originates
from the "mountain ranges of central Africa", while the
**paragraph mentions that the Nile originates in the**
**Great Lakes region of central Africa.**

The first step correctly isolates the term with x to get
2x = 8. However, **the next step inaccurately divides**
**8 by 2 to yield a result of x = 3**, which is inconsistent
with the earlier reasoning.

Factuality
Hallucination

Faithfulness
Hallucination

Factual
Contradiction

Factual
Fabrication

Instruction
Inconsistency

Context
Inconsistency

Logical
Inconsistency

This shift is primarily attributed to their vast parametric factual knowledge. However, existing LLMs
occasionally exhibit tendencies to produce outputs that are either inconsistent with real-world
facts or unverifiable [168], posing challenges to the trustworthiness of artificial intelligence. In this
context, we categorize these factuality hallucinations into two primary types:

**Factual Contradiction** refers to situations where the LLM’s output contains facts that can be
grounded in real-world information, but present contradictions. This type of hallucination occurs
most frequently and arises from diverse sources, encompassing the LLM’s capture, storage, and
expression of factual knowledge. Depending on the error type of contradictions, it can be further
divided into two subcategories: _entity-error hallucination_ and _relation-error hallucination_ .
```

**P001-p006-c004** - [P001_hallucination_survey.pdf, PDF page 6](../data/raw/P001_hallucination_survey.pdf#page=6)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
and
expression of factual knowledge. Depending on the error type of contradictions, it can be further
divided into two subcategories: _entity-error hallucination_ and _relation-error hallucination_ .

- **Entity-error** **hallucination** refers to the situations where the generated text of LLMs
contains erroneous entities. As shown in Table 1, when asked about _"the_ _inventor_ _of_ _the_
_telephone"_, the model erroneously states _"Thomas Edison"_, conflicting with the real fact that it
was _"Alexander Graham Bell"_ .

- **Relation-error hallucination** refers to instances where the generated text of LLMs contains
wrong relations between entities. As shown in Table 1, when inquired about _"the inventor of_
_the light bulb"_, the model incorrectly claims _"Thomas Edison"_, despite the fact that _he improved_
_upon existing designs and did not invent it_ .

**Factual Fabrication** refers to instances where the LLM’s output contains facts that are unverifiable against established real-world knowledge. This can be further divided into _unverifiability_
_hallucination_ and _overclaim hallucination_ .

ACM Transactions on Information Systems, Vol. 1, No. 1, Article 1. Publication date: January 2024.
```

### DRAFT-Q003 - PENDING

What three subtypes of faithfulness hallucination does the survey identify, and what does each mean?

**Draft reference answer (unverified):** Instruction inconsistency deviates from a user directive; context inconsistency contradicts supplied contextual information; logical inconsistency involves internal contradictions in reasoning steps or between reasoning and the final answer.

**Reviewer caution:** The original PDF page 7 itself has an inconsistent x=4 arithmetic example compared with Table 1 on page 6. The question concerns the definitions only. Do not use that arithmetic example as factual evidence.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P001-p007-c002** - [P001_hallucination_survey.pdf, PDF page 7](../data/raw/P001_hallucination_survey.pdf#page=7)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
vital. Furthermore,
LLM’s faithfulness is also reflected in the logical consistency of its generated content. From this
perspective, we categorize three subtypes of faithfulness hallucinations:

**Instruction inconsistency** refers to the LLM’s outputs that deviate from a user’s directive.
While some deviations might serve safety guidelines, the inconsistencies here signify unintentional
misalignment with non-malicious user instructions. As described in Table 1, the user’s actual
intention is translation, However, the LLM erroneously deviated from the user’s instruction and
performed a question-answering task instead.

**Context inconsistency** points to instances where the LLM’s output is unfaithful with the user’s
provided contextual information. For example, as shown in Table 1, the user mentioned the Nile’s
source being in the Great Lakes region of central Africa, yet the LLM’s response contradicted the
context.

**Logical inconsistency** underscores when LLM outputs exhibit internal logical contradictions,
often observed in reasoning tasks. This manifests as inconsistency both among the reasoning steps
themselves and between the steps and the final answer. For example, as shown in Table 1, while
the reasoning step of dividing both sides of the equation by 2 is correct, the final answer of x=4 is
inconsistent with the reasoning chain, leading to an incorrect result.

**3** **HALLUCINATION CAUSES**
```

### DRAFT-Q004 - PENDING

Which three broad sources of LLM hallucination organize the survey discussion of causes?

**Draft reference answer (unverified):** The survey organizes causes into data, training, and inference.

**Reviewer caution:** The opening overlap contains the preceding arithmetic example; the supporting section is HALLUCINATION CAUSES.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P001-p007-c003** - [P001_hallucination_survey.pdf, PDF page 7](../data/raw/P001_hallucination_survey.pdf#page=7)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
step of dividing both sides of the equation by 2 is correct, the final answer of x=4 is
inconsistent with the reasoning chain, leading to an incorrect result.

**3** **HALLUCINATION CAUSES**

LLM hallucinations have multifaceted origins, spanning the entire spectrum of LLMs’ capability
acquisition process. In this section, we delve into the root causes of hallucinations in LLMs, primarily
categorized into three key aspects: (1) _Data_ (§3.1), (2) _Training_ (§3.2), and (3) _Inference_ (§3.3).

**3.1** **Hallucination from Data**

Data for training LLMs are comprised of two primary components: (1) pre-training data, through
which LLMs acquire their general capabilities and factual knowledge [388], and (2) alignment
data, which teach LLMs to follow user instructions and align with human preferences [322].
Although these data constantly expand the capability boundaries of LLMs, they inadvertently
become the principal contributors to LLM hallucinations. This primarily manifests in three aspects:
the presence of misinformation and biases in the flawed pre-training data sources (§3.1.1), the
knowledge boundary inherently bounded by the scope of the pre-training data (§3.1.2), and the
hallucinations induced by inferior alignment data (§3.1.3).
```

### DRAFT-Q005 - PENDING

How can SelfCheckGPT detect possible hallucinations without an external knowledge database?

**Draft reference answer (unverified):** It samples multiple responses from the same model and measures their information consistency. Known facts are expected to recur consistently, while hallucinated facts may diverge or contradict each other. Only sampled responses are needed, allowing black-box use.

**Reviewer caution:** Consistency is a detection heuristic, not a guarantee that a repeated claim is true. Check for other complete supporting passages in the corpus.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P002-p002-c002** - [P002_selfcheckgpt.pdf, PDF page 2](../data/raw/P002_selfcheckgpt.pdf#page=2)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
In this paper, we propose SelfCheckGPT, a
sampling-based approach that can detect whether
responses generated by LLMs are hallucinated or
factual. To the best of our knowledge, SelfCheckGPT is the first work to analyze model hallucination of general LLM responses, and is the first
zero-resource hallucination detection solution that
can be applied to black-box systems. The motivating idea of SelfCheckGPT is that when an LLM
has been trained on a given concept, the sampled responses are likely to be similar and contain consistent facts. However, for hallucinated facts, stochastically sampled responses are likely to diverge and
may contradict one another. By sampling multiple
responses from an LLM, one can measure information consistency between the different responses
and determine if statements are factual or hallucinated. Since SelfCheckGPT only leverages sampled responses, it has the added benefit that it can
be used for black-box models, and it requires no
external database. Five variants of SelfCheckGPT
for measuring informational consistency are considered: BERTScore, question-answering, _n_ -gram,
NLI, and LLM prompting. Through analysis of annotated articles generated by GPT-3, we show that
SelfCheckGPT is a highly effective hallucination
detection method that can even outperform greybox methods, and serves as a strong first baseline
for an increasingly important problem of LLMs.

**2** **Background and Related Work**

**2.1** **Hallucination of Large Language Models**
```

### DRAFT-Q006 - PENDING

How does SelfCheckGPT-Prompt convert Yes, No, and unrecognized responses into an inconsistency score?

**Draft reference answer (unverified):** It asks whether a sentence is supported by each sampled context, maps Yes to 0.0, No to 1.0, and N/A to 0.5, then averages these scores across samples.

**Reviewer caution:** Equation 11 is distorted in the chunk. The mapping and arithmetic mean were inspected in the original PDF, page 5, left column. Human reviewer must check both.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P002-p005-c002** - [P002_selfcheckgpt.pdf, PDF page 5](../data/raw/P002_selfcheckgpt.pdf#page=5)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
and its summary in zero-shot settings (Luo
et al., 2023). Thus, we query an LLM to assess
whether the _i_ -th sentence is supported by sample
_S_ _[n]_ (as the context) using the following prompt.

-----------------------------------------------Context: {}
Sentence: {}
Is the sentence supported by the context above?
Answer Yes or No:
-----------------------------------------------
Initial investigation showed that GPT-3 (textdavinci-003) will output either Yes or No 98% of
the time, while any remaining outputs can be set to
N/A. The output from prompting when comparing
the _i_ -th sentence against sample _S_ _[n]_ is converted to
score _x_ _[n]_ _i_ [through the mapping {][Yes][:] [0.0,][ No][:] [1.0,]

N/A: 0.5}. The final inconsistency score is then
calculated as:

Prompt( _i_ ) = [1]
_S_ _N_

_N_

_n_ =1

_n_ =1

_x_ _[n]_ _i_ (11)

**6** **Data and Annotation**

As, currently, there are no standard hallucination
detection datasets available, we evaluate our hallucination detection approaches by 1) generating synthetic Wikipedia articles using GPT-3 on the individuals/concepts from the WikiBio dataset (Lebret
et al., 2016); 2) manually annotating the factuality
of the passage at a sentence level; 3) evaluating the
system’s ability to detect hallucinations.
```

### DRAFT-Q007 - PENDING

Which sentence-level factuality labels and numeric values were used to annotate the SelfCheckGPT WikiBio passages?

**Draft reference answer (unverified):** Major Inaccurate has value 1 and describes an entirely hallucinated, off-topic sentence; Minor Inaccurate has value 0.5 for some nonfactual information in an on-topic sentence; Accurate has value 0 for accurate information.

**Reviewer caution:** These numbers are annotation labels from the paper, not ResearchLens relevance scores. Read the label definitions in the PDF right column.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P002-p005-c003** - [P002_selfcheckgpt.pdf, PDF page 5](../data/raw/P002_selfcheckgpt.pdf#page=5)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
from the WikiBio dataset (Lebret
et al., 2016); 2) manually annotating the factuality
of the passage at a sentence level; 3) evaluating the
system’s ability to detect hallucinations.

WikiBio is a dataset where each input contains
the first paragraph (along with tabular information)
of Wikipedia articles of a specific concept. We rank
the WikiBio test set in terms of paragraph length
and randomly sample 238 articles from the top
20% of longest articles (to ensure no very obscure
concept is selected). GPT-3 (text-davinci-003) is
then used to generate Wikipedia articles on a concept, using the prompt "This is a Wikipedia
passage about {concept}:". Table 1 provides
the statistics of GPT-3 generated passages.

#Passages #Sentences #Tokens/passage

238 1908 184.7 36.9
_±_

**Table 1:** The statistics of **WikiBio GPT-3 dataset** where the
number of tokens is based on the OpenAI GPT-2 tokenizer.

We then annotate the sentences of the generated

passages using the guidelines shown in Figure 3
such that each sentence is classified as either:

- **Major Inaccurate** (Non-Factual, **1** ): The sentence is entirely hallucinated, i.e. the sentence
is unrelated to the topic.

- **Minor** **Inaccurate** (Non-Factual, **0.5** ): The
sentence consists of some non-factual information, but the sentence is related to the topic.

- **Accurate** (Factual, **0** ): The information presented in the sentence is accurate.
```

### DRAFT-Q008 - PENDING

How did the SelfCheckGPT authors obtain human passage-level factuality scores from sentence annotations?

**Draft reference answer (unverified):** They averaged the sentence-level annotation labels within each passage. A score of +1.0 denotes total hallucination in their description.

**Reviewer caution:** This asks about human annotation aggregation, not a comparison of model performance. The chunk also contains plot-axis fragments; use the explanatory paragraph.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P002-p006-c001** - [P002_selfcheckgpt.pdf, PDF page 6](../data/raw/P002_selfcheckgpt.pdf#page=6)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
Major Inaccurate

**(Non-factual 1)**

Minor Inaccurate
**(Non-factual 0.5)**

Accurate
**(Factual 0)**

**Figure 3:** Flowchart of our annotation process

values of 0.595 and 0.748, indicating _moderate_ and
_substantial_ agreement (Viera et al., 2005) for the
3-class and 2-class scenarios, respectively. [4]

Furthermore, passage-level scores are obtained
by averaging the sentence-level labels in each passage. The distribution of passage-level scores is
shown in Figure 4, where we observe a large peak
at +1.0. We refer to the points at this peak as _total_
_hallucination_, which occurs when the information
of the response is unrelated to the real concept and
is entirely fabricated by the LLM.

30

25

20

15

10

5

0

0.0 0.2 0.4 0.6 0.8 1.0
Avg. Factuality per Document (0=Factual, +1=Non-Factual)

**Figure 4:** Document factuality scores histogram plot

**7** **Experiments**

The generative LLM used to generate passages for
our dataset is **GPT-3** (text-davinci-003), the stateof-the-art system at the time of creating and annotating the dataset. To obtain the main response, we
set the temperature to 0.0 and use standard beam
search decoding. For the stochastically generated
samples, we set the temperature to 1.0 and generate

43-class refers to when selecting between accurate, minor inaccurate, major inaccurate. 2-class refers to when minor/major inaccuracies are combined into one label.
```

### DRAFT-Q009 - PENDING

Why does FActScore evaluate atomic facts instead of assigning one factuality label to each whole sentence?

**Draft reference answer (unverified):** A single sentence can mix supported and unsupported information. An atomic fact conveys one piece of information, enabling finer-grained evaluation without treating partially supported sentences as wholly correct or wholly incorrect.

**Reviewer caution:** The end of this chunk contains an interleaved equation; the supporting prose is Key idea 1 in the PDF left column.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P003-p003-c002** - [P003_factscore.pdf, PDF page 3](../data/raw/P003_factscore.pdf#page=3)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
and
fine-grained evaluation of factual precision, but is
time-consuming and costly, motivating automatic
evaluation in Section 4.

**3.1** **Definition**

FACTSCORE is based on two key ideas.

**Key** **idea** **1:** **Atomic** **fact** **as** **a** **unit.** Long-form
text consists of many pieces of information that can
each be either true or false. Prior work has explored
using a sentence as a unit; however, even a single
sentence is a mix of supported and unsupported
facts, e.g., in 40% of the cases with ChatGPT. Previous and concurrent work either (1) defines an
additional label of partial support (Manakul
et al., 2023; Liu et al., 2023a) whose definition
may be subjective and can lead to low agreement,
or (2) takes the strictest definition of support
that requires every piece of information to be supported (Rashkin et al., 2021; Gao et al., 2022),
which ignores the partial support cases, e.g., assigning 0.0 to both generations in Figure 1 even
though the first generation is considerably more
accurate than the second.

In this paper, we define an atomic fact as a short
sentence conveying one piece of information (examples in Figure 1), similar to summarization content units (Nenkova and Passonneau, 2004). An
atomic fact is a more fundamental unit than a sentence for a piece of information and provides a
more fine-grained evaluation, e.g., in Figure 1, rat

FACTSCORE( ) = E _x_ [ _f_ ( _x_ ) _x_ responds] _._
_M_ _∈X_ _M_ _|M_
```

### DRAFT-Q010 - PENDING

How does the Retrieve-to-LM variant of the FActScore estimator decide whether an atomic fact is supported?

**Draft reference answer (unverified):** It retrieves k passages from the chosen knowledge source, concatenates them with the atomic fact and a True or False question, and feeds that prompt to the evaluation language model for its prediction.

**Reviewer caution:** This is one estimator variant, not the ensemble rule. Preserve the distinction between the subject LM and evaluation LM.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P003-p006-c003** - [P003_factscore.pdf, PDF page 6](../data/raw/P003_factscore.pdf#page=6)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
3.3) effective
and close to human, consistent with findings from
prior work (Chen et al., 2022). This section thus
focuses on how to validate each atomic fact against
a given knowledge source.

The validation is based on zero-shot prompting
of an LM referred to as an **LMEVAL** to distinguish
from an LMSUBJ. Specifically, a _prompt_ —whose
construction methods differ across four variants—
is fed into an LMEVAL. The prediction is then made
by comparing the conditional probability of True
and False from the LMEVAL. If the logit values
are unavailable (e.g., commercial LMs like ChatGPT), the prediction is made based on whether the
generated text contains True or False. [6]

The four variants we consider are as follows.

**No-context** **LM** uses <atomic-fact> True or
False? as a prompt, closely resembling Kadavath
et al. (2022). [7]

**Retrieve** _→_ **LM** retrieves passages from the given
knowledge source and then prompts the LMEVAL. It
first retrieves _k_ passages, constructs the prompt by
concatenating retrieved passages, the given atomic
fact, and “True or False?”, and feeds it to the
LMEVAL to get the prediction.

**Nonparametric Probability (NP)** makes a judgment based on a nonparametric likelihood. It masks
out each token in the atomic fact, computes its likelihood using a nonparametric masked LM (Min
et al., 2023), averages probabilities over all tokens,
and makes a prediction based on thresholding.
```

### DRAFT-Q011 - PENDING

Why can FActScore miss incomplete answers, and which additional statistics do its authors recommend reporting?

**Draft reference answer (unverified):** It measures factual precision rather than recall or coverage, so it does not penalize frequent abstention or generating fewer facts. The authors recommend also reporting the abstention percentage and average number of atomic facts.

**Reviewer caution:** The full question includes recommended statistics; chunks that only mention precision versus recall are partial evidence, not a complete alternative.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P003-p010-c002** - [P003_factscore.pdf, PDF page 10](../data/raw/P003_factscore.pdf#page=10)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
human-written text and its linguistic complexity.
Future work can investigate how the distribution
of model generation affects the performance of the
estimator and further improve the estimator.

**Beyond factual precision.** FACTSCORE focuses
on factual precision—whether each piece of information in a generation is factually supported
by a reliable source of knowledge—which is only
one aspect of the broader factuality problem. For
instance, FACTSCORE does not consider factual
recall: the coverage of information in a generation. FACTSCORE does not penalize a model that
abstains from responding too frequently or generates fewer facts, which can be unfair since there is
an inherent trade-off between precision and recall.
Moreover, the boundary between precision and recall is often blurry, e.g., it is possible that, even if
every piece of information in a generation is supported, it misses a significant piece of information
that should have been mentioned in order to be considered as correctly responding to the input prompt
(example in Table 6). We leave a more holistic
evaluation of factuality for future work, and recommend reporting FACTSCORE together with the
% of abstention and the average number of atomic

facts (as we did in Section 4.3).

**Acknowledgement**
```

### DRAFT-Q012 - PENDING

What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its applicability?

**Draft reference answer (unverified):** The definition assumes support is undebatable, atomic facts have equal importance, and information in the source does not conflict or overlap. Nuanced or debatable facts and frequently conflicting source text undermine these assumptions.

**Reviewer caution:** This requires two complementary passages. The current evaluator counts chunk recall; it does not require that all parts of a question are answered.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P003-p003-c003** - [P003_factscore.pdf, PDF page 3](../data/raw/P003_factscore.pdf#page=3)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
fundamental unit than a sentence for a piece of information and provides a
more fine-grained evaluation, e.g., in Figure 1, rat

FACTSCORE( ) = E _x_ [ _f_ ( _x_ ) _x_ responds] _._
_M_ _∈X_ _M_ _|M_

_x_ _responds_ means did not abstain from re_M_ _M_
sponding to the prompt _x_ . This definition assumes
the following:

1. Whether or not an atomic fact is supported by
_C_ is undebatable.
2. Every atomic fact in _Ay_ has an equal weight of
importance, following Krishna et al. (2023).
3. Pieces of information in _C_ do not conflict or
overlap with each other.

In the rest of the paper, we propose to use people
biographies as _X_ and Wikipedia as _C_ because they
satisfy these assumptions to a reasonable degree
(Section 3.3). We discuss in which cases these
assumptions hold or may not hold in more detail in
the Limitation section.

FACTSCORE considers _precision_ but not _recall_,
e.g., a model that abstains from answering too often
or generates text with fewer facts may have a higher
FACTSCORE, even if these are not desired. We
leave the evaluation of factual recall for future work
(more discussion in the Limitation section).

**3.2** **Studied LMs**

We evaluate three LMs (referred to as LMSUBJ,

an LM as a subject): (1) **InstructGPT**
(text-davinci-003, updated from Ouyang et al.

ing the first generation higher than the second.
```

**P003-p010-c001** - [P003_factscore.pdf, PDF page 10](../data/raw/P003_factscore.pdf#page=10)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
leave further study for future work.

Due to the assumptions made in Section 3.1,
FACTSCORE is not applicable when the facts are
more nuanced, open-ended, and debatable (Chen
et al., 2019; Xu et al., 2023) or with a knowledge source whose text frequently conflicts with
each other (Wadden et al., 2022). Moreover,
FACTSCORE may not be suitable for the humanwritten text that is nuanced and includes intentional
or implicit deception.

**Limitation in our estimator.** While our estimator closely approximates humans and provides consistent ranking over a large set of LMs, it is not perfect in individual judgments, and the best variant
depends on the degree of how close a generation is
to human-written text and its linguistic complexity.
Future work can investigate how the distribution
of model generation affects the performance of the
estimator and further improve the estimator.
```

### DRAFT-Q013 - PENDING

What are the imitative falsehoods that TruthfulQA questions are designed to elicit?

**Draft reference answer (unverified):** They are false statements with high likelihood under the language model training distribution. TruthfulQA deliberately probes this weakness in model truthfulness.

**Reviewer caution:** Keep the paper-specific definition, rather than equating all errors or hallucinations with imitative falsehoods.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P004-p004-c003** - [P004_truthfulqa.pdf, PDF page 4](../data/raw/P004_truthfulqa.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
on interpretability, it
would be hard to systematically decide whether a language
model really “knows” an answer such that it could be generated by the model under different conditions or prompting.

The reference answers are used for human evaluation, automated evaluation (see Section 3.2), and a
multiple-choice task (Section 3.1). Their construction is described in Appendix C.1.

The questions in TruthfulQA were designed to
be “adversarial” in the sense of testing for a _weak-_
_ness_ in the truthfulness of language models (rather
than testing models on a useful task). In particular,
the questions test a weakness to imitative falsehoods: false statements with high likelihood on the
training distribution. We constructed the questions
using the following adversarial procedure, with
GPT-3-175B (QA prompt) as the target model:

1. We wrote questions that some humans would
answer falsely. We tested them on the target model and filtered out questions that the
model consistently answered correctly when
multiple random samples were generated at
nonzero temperatures. We produced 437 questions this way, which we call the “filtered”
questions (Wallace and Boyd-Graber, 2018).

2. Using this experience of testing on the target model, we wrote 380 additional questions
that we expected some humans and models to
answer falsely. Since we did not test on the
target model, these are “unfiltered” questions.
```

### DRAFT-Q014 - PENDING

Why can answering No comment to every TruthfulQA question count as truthful, yet still be undesirable?

**Draft reference answer (unverified):** Truthfulness is defined as avoiding false assertions, allowing refusal or uncertainty. A model that always says No comment can therefore be truthful but uninformative, which is why informativeness is evaluated separately.

**Reviewer caution:** These adjacent chunks overlap; the second may independently provide sufficient evidence. Decide whether both should be labelled relevant after reading their complete text.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P004-p004-c001** - [P004_truthfulqa.pdf, PDF page 4](../data/raw/P004_truthfulqa.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
eral truth about the real world. Claims that are only
true according to a belief system or tradition (e.g.
“Libras have friendly personalities”) are counted as

false. TruthfulQA mostly concerns factual claims,
and true factual claims are usually supported by
reliable, publicly available evidence. Overall, our
standard for truth is similar to the standards used
for scientific articles or Wikipedia. As an illustration of our standard, see Figure 1 (which shows
only answers that we count as false) and Figure 16
(which shows both true and false answers).

How do we evaluate models using this standard
of truth? Statements generated by models may be
ambiguous or inaccurate to varying degrees. We assign statements a scalar truth score in [0 _,_ 1], which
can be interpreted as the probability the statement
is true. Results in Figures 2 and 4 threshold these
scores for greater interpretability but scalar scores
are reported in Appendix B.2.

We define an answer to a question as _truthful_ iff it
avoids asserting a false statement. So truthfulness
is consistent with refusing to answer a question,
with expressing uncertainty, or with giving a true
but irrelevant answer. In this paper, we evaluate
non-committal answers such as “No comment” or
“I don’t know” as true, even when there’s a sense in
```

**P004-p004-c002** - [P004_truthfulqa.pdf, PDF page 4](../data/raw/P004_truthfulqa.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
expressing uncertainty, or with giving a true
but irrelevant answer. In this paper, we evaluate
non-committal answers such as “No comment” or
“I don’t know” as true, even when there’s a sense in

which the model “knows” a true answer. [1] It follows
from our definition that a model is perfectly truthful
if it answers “No comment” for every question. In
practice we want answers that are both truthful
and _informative_ (i.e. providing information that
reduces uncertainty raised by the question). So in
assessing models, we also include evaluations of
informativeness. Truthfulness and informativeness
are loosely analogous to precision and recall.

**2.2** **Constructing TruthfulQA**

TruthfulQA consists of a test set of 817 questions
and is intended only for the zero-shot setting. All
questions were written by the authors and were designed to elicit imitative falsehoods. The questions
are diverse in style and cover 38 categories, where
diversity is important because a truthful model
should be truthful regardless of the topic.

Most questions are one-sentence long with a median length of 9 words. Each question has sets
of true and false reference answers and a source
that supports the answers (e.g. a Wikipedia page).

1Given the current state of research on interpretability, it
would be hard to systematically decide whether a language
model really “knows” an answer such that it could be generated by the model under different conditions or prompting.
```

### DRAFT-Q015 - PENDING

How were the filtered and unfiltered subsets of TruthfulQA constructed, and how many questions did each contain?

**Draft reference answer (unverified):** For the filtered set, the authors tested questions on GPT-3-175B and removed questions it consistently answered correctly, yielding 437. They then wrote 380 additional anticipated difficult questions without testing them on the target model, forming the unfiltered set.

**Reviewer caution:** The counts refer to this paper version. Confirm both counts and the difference in testing procedures in the PDF right column.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P004-p004-c003** - [P004_truthfulqa.pdf, PDF page 4](../data/raw/P004_truthfulqa.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
on interpretability, it
would be hard to systematically decide whether a language
model really “knows” an answer such that it could be generated by the model under different conditions or prompting.

The reference answers are used for human evaluation, automated evaluation (see Section 3.2), and a
multiple-choice task (Section 3.1). Their construction is described in Appendix C.1.

The questions in TruthfulQA were designed to
be “adversarial” in the sense of testing for a _weak-_
_ness_ in the truthfulness of language models (rather
than testing models on a useful task). In particular,
the questions test a weakness to imitative falsehoods: false statements with high likelihood on the
training distribution. We constructed the questions
using the following adversarial procedure, with
GPT-3-175B (QA prompt) as the target model:

1. We wrote questions that some humans would
answer falsely. We tested them on the target model and filtered out questions that the
model consistently answered correctly when
multiple random samples were generated at
nonzero temperatures. We produced 437 questions this way, which we call the “filtered”
questions (Wallace and Boyd-Graber, 2018).

2. Using this experience of testing on the target model, we wrote 380 additional questions
that we expected some humans and models to
answer falsely. Since we did not test on the
target model, these are “unfiltered” questions.
```

### DRAFT-Q016 - PENDING

What restrictions define the true zero-shot setting used for the TruthfulQA baselines?

**Draft reference answer (unverified):** No gradient updates are performed, no TruthfulQA examples appear in prompts, and prompts and hyperparameters are not tuned on TruthfulQA examples. Natural-language instructions are allowed.

**Reviewer caution:** This describes the historical benchmark protocol, not a requirement that ResearchLens itself use a particular prompting method.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P004-p005-c002** - [P004_truthfulqa.pdf, PDF page 5](../data/raw/P004_truthfulqa.pdf#page=5)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
et al., 2020) is a T5
model (Raffel et al., 2019) fine-tuned on diverse QA tasks. This is a different transformer architecture, training objective, and
pre-training dataset than the other models.

For each model family, we evaluate different
sizes of model. For GPT-3-175B only, we evaluate
different prompts.

Appendix B.3 presents additional results from
the Anthropic (Askell et al., 2021), Gopher (Rae
et al., 2021), WebGPT (Nakano et al., 2021), and
InstructGPT (Ouyang et al., 2021) models, which
were externally evaluated on TruthfulQA.

**Prompts.** TruthfulQA is intended as a zero-shot
benchmark (Brown et al., 2020; Wei et al., 2021).
Zero-shot means that (i) no gradient updates are
performed and (ii) no examples from TruthfulQA

appear in prompts (but prompts may contain natural
language instructions). For our baselines, we also
require that prompts and hyperparameters are not
tuned on examples from TruthfulQA in any way.
We call this the _true_ _zero-shot_ setting, following

the definition of “true few-shot learning” in Perez
et al. (2021). For straightforward comparison to
our true-zero-shot baselines, we recommend using
our prompts and hyperparameters. [2]
```

### DRAFT-Q017 - PENDING

In Retrieval Augmentation Reduces Hallucination in Conversation, how do RAG-Sequence and RAG-Token differ in their use of retrieved documents?

**Draft reference answer (unverified):** RAG-Sequence generates an output sequence independently for each concatenated context and marginalizes over sequence outputs. RAG-Token marginalizes the output distribution over documents, allowing a different document to contribute at each token.

**Reviewer caution:** Use the RAG and FiD subsection; this describes the paper architectures, not the NumPy index implemented in ResearchLens.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P005-p003-c002** - [P005_retrieval_reduces_hallucination.pdf, PDF page 3](../data/raw/P005_retrieval_reduces_hallucination.pdf#page=3)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
the prior output tokens, where **p** _θ_ ( **y** _i|_ **x** _i,_ **z** _i,j_ )
is the full sequence score. In some cases subscripts
_i_ and _j_ are omitted for clarity.

**3.1** **RAG and FiD**

Neural retrievers have been shown to outperform
word-similarity-based architectures such as BM25,
and, with the help of GPU-based similarity search
libraries such as FAISS (Johnson et al., 2019), can
scale to knowledge sources of millions of documents. We first discuss these new architectures.

Lewis et al. (2020b) introduced the **RAG**
(retrieval-augmented generation) architecture. The
RAG model utilizes a Dense Passage Retriever
(DPR) pre-trained to rank correct passages in various QA settings (Karpukhin et al., 2020). A large
FAISS index stores **d** ( **z** _j_ ), with **q** ( **x** _i_ ) as the query
for relevant documents. **RAG-Sequence** considers documents independently, generating an output sequence for each concatenated context separately and marginalizing over the output generations. **RAG-Token** marginalizes the output distribution over all documents, allowing the generator
to attend over a different document for each token.
Though **d** ( **z** _j_ ) remains fixed during training, token
losses are propagated to the retriever itself, and the
context representations **q** ( **x** _i_ ) are updated in order
to better fit the retriever for the task.
```

### DRAFT-Q018 - PENDING

How does Fusion-in-Decoder combine retrieved documents, and is its retriever updated during training in the baseline described by the conversation paper?

**Draft reference answer (unverified):** FiD encodes each document-context pair independently, concatenates their encoder outputs, and lets the decoder attend over all of them together. The baseline FiD retriever is fixed during training.

**Reviewer caution:** The page 4 chunk also describes FiD-RAG. Distinguish that proposed extension from the fixed-retriever FiD baseline; page 3 is the primary direct explanation.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P005-p003-c003** - [P005_retrieval_reduces_hallucination.pdf, PDF page 3](../data/raw/P005_retrieval_reduces_hallucination.pdf#page=3)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
remains fixed during training, token
losses are propagated to the retriever itself, and the
context representations **q** ( **x** _i_ ) are updated in order
to better fit the retriever for the task.

Izacard and Grave (2021b) introduce the **FiD**
(Fusion-in-Decoder) method. Given a set of retrieved documents, the generator’s encoder considers expanded contexts [ **z** _i,j_ ; **x** _i_ ] independently. The
encoder outputs are concatenated before passing
to the decoder, allowing the decoder to attend over
all document/context representations _at the same_
_time_ . Despite fixing the retriever throughout training, FiD demonstrates superior performance on a

number of QA tasks, demonstrating its efficacy in
attending over several documents.

**3.2** **Improving Neural Retrieval**

The introduction of neural retrieval is a major driver
of the performance gains achieved in QA tasks by
the RAG and FiD models; when substituting a nonneural retriever, performance in open-domain QA
tasks suffers dramatically (Lewis et al., 2020b). It
follows that further improving retrieval should in
turn lead to additional improvements.
```

**P005-p004-c003** - [P005_retrieval_reduces_hallucination.pdf, PDF page 4](../data/raw/P005_retrieval_reduces_hallucination.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
_T_ _[∗]_ = 1 _≤_ _T_ _[∗]_ _≤_ _T_,
such that the most recent _T_ _[∗]_ turns are considered

independently, and all turns prior are considered
jointly, yielding _T_ _[∗]_ + 1 total context “turns”.

Finally, we consider the notion of RAG-Turn as
a means of simply boosting the the total number
of documents; **RAG-Turn Token** and **RAG-Turn**
**Sequence** are outlined in Appendix B.

**3.4** **Improving Fusion-in-Decoder**

Though FiD does not train its retriever, it more
efficiently attends over larger sets of documents
than RAG, as the independent encoder outputs are
fused before decoding the final generation. FiD has
been applied with great success to open-domain
QA tasks primarily with BM25 retrievers or neural retrievers pre-trained on QA datasets (Izacard
and Grave, 2021b; Xiong et al., 2021). However,
knowledge-grounded dialogue offers a more challenging (or at the very least, materially different)
retrieval task than question answering. We thus
explore whether we can improve upon out-of-thebox FiD by incorporating retrievers trained _in_ _a_
_RAG setup_ ; we refer to models with a DPR-based
retriever trained with RAG, and then used with FiD,
as **FiD-RAG**, and apply relevant suffixes to denote
comparison to our other retrieval methods.

**4** **Experiments**

**Datasets** : We conduct experiments on two datasets:
Wizard of Wikipedia (WoW) (Dinan et al., 2019b)
```

### DRAFT-Q019 - PENDING

Why does the conversation paper propose DPR-Poly reranking, and how does it increase interaction between a dialogue context and candidate documents?

**Draft reference answer (unverified):** DPR only combines context and document via a final dot product, while full cross-attention over millions of candidates is intractable. DPR-Poly reranks a retrieved subset using Poly-encoder attention to produce candidate-aware context representations.

**Reviewer caution:** Do not describe Poly-encoders as identical to the cross-encoder used by ResearchLens; they are different architectures.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P005-p003-c004** - [P005_retrieval_reduces_hallucination.pdf, PDF page 3](../data/raw/P005_retrieval_reduces_hallucination.pdf#page=3)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
a nonneural retriever, performance in open-domain QA
tasks suffers dramatically (Lewis et al., 2020b). It
follows that further improving retrieval should in
turn lead to additional improvements.

In DPR a dialogue context and a candidate document interact only via a final dot-product similarity score. However, allowing more interaction
between the two yields superior results in various
information retrieval and ranking tasks (Humeau
et al., 2020; Khattab and Zaharia, 2020). Full crossattention is intractable when scaling to millions of
candidate documents, so recent work allows latestage interaction between context and candidate
outputs while keeping the bulk of the computation
separate (Khattab and Zaharia, 2020), with some
work demonstrating this to be especially effective
in dialogue-based candidate ranking tasks for next
utterance prediction (Humeau et al., 2020).

One way to introduce greater interaction without
extensive additional computational cost is to rerank a subset of documents retrieved via DPR with
a more candidate-aware approach. For this method,
we employ Poly-encoders (Humeau et al., 2020),
which introduce an additional attention mechanism
that yields candidate-aware context representations
prior to a final scoring computation. We denote
this method **DPR-Poly** ; one can also choose to
initialize the Poly-encoder with the DPR model
weights, a method we denote **Joint DPR-Poly**
```

### DRAFT-Q020 - PENDING

Which datasets were used in the conversation retrieval study, and what makes their unseen evaluation splits different from the training data?

**Draft reference answer (unverified):** The datasets are Wizard of Wikipedia and CMU Document Grounded Conversations. Unseen splits contain topics for WoW or movies for CMU_DoG not discussed in training; WoW supplied these splits and the authors constructed them for CMU_DoG.

**Reviewer caution:** Read the dataset paragraph, not the adjacent automatic-metric list. The question concerns source-paper experiments, not results from ResearchLens.

Reviewer: __________  Date: __________  Decision: ACCEPT / EDIT / REJECT
Corrected chunk IDs / rationale: ____________________________________

**P005-p004-c004** - [P005_retrieval_reduces_hallucination.pdf, PDF page 4](../data/raw/P005_retrieval_reduces_hallucination.pdf#page=4)

Source flags: needs_review=False; review_flags=[]. Full supporting chunk:

```text
relevant suffixes to denote
comparison to our other retrieval methods.

**4** **Experiments**

**Datasets** : We conduct experiments on two datasets:
Wizard of Wikipedia (WoW) (Dinan et al., 2019b)

and CMU Document Grounded Conversations
(CMU_DoG) (Zhou et al., 2018) which are both
sets of knowledge-grounded dialogues collected
through human-human crowdworker chats in English, where one of the crowdworkers had access
to external knowledge from Wikipedia; WoW discusses various topics, and CMU_DoG discusses
movies. For each, we consider “seen” and “unseen” validation and test splits, where the “unseen”
split contains topics (for WoW) or movies (for
CMU_DoG) _not_ _discussed_ _in_ _the_ _training_ _data_ .
WoW provides these splits, and we constructed

our own for CMU_DoG. We employ the standard
KiLT Wikipedia dump (Petroni et al., 2021) as our
knowledge source for retrieval for both datasets [1] .
More dataset details are in Appendix C.

**Metrics** : We employ standard automatic metrics, including perplexity (PPL), unigram overlap
(F1), BLEU-4 (B4) and ROUGE-L (RL) of the generated responses. We consider an additional metric,
Knowledge F1 (KF1), described in Section 4.2,

1
[https://github.com/facebookresearch/KILT](https://github.com/facebookresearch/KILT)
```
