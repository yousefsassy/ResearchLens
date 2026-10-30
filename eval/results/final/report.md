# ResearchLens — Full Benchmark Report

- **Run mode:** live
- **Run complete:** YES (105/105 questions)
- **Dataset:** 1f09eaa462bc… (SHA-256 fingerprint)
- **Ground truth human-verified:** No
- **Offline tests:** PASS (see `tests.txt`)

## 1. Overall results

| Metric | Result | Meaning |
|---|---:|---|
| Questions processed | 105/105 | Full set only when all planned questions finish |
| Complete | 64/105 (61.0%) | Model-reported answer status |
| Partial | 25/105 (23.8%) | Model-reported answer status |
| Errors | 8/105 (7.6%) | Pipeline or validation failed |
| Abstained | 5/105 (4.8%) | May be correct for unanswerable items |
| Needs clarification | 3/105 (2.9%) | May be correct for ambiguous items |
| Expected-status agreement | 72.4% | Agreement with draft acceptable statuses; **not factual accuracy** |
| Citation validation | 91.8% (97 checked) | Valid source IDs/quotes/structure; **not semantic support** |
| Semantic factual accuracy | 94.5% | LLM judge, only 60/105 questions successfully judged |
| Semantic completeness | 90.4% | LLM judge, only 60/105 questions successfully judged |
| Semantic citation support | 96.4% | LLM judge, only 60/105 questions successfully judged |
| Judge coverage | 60/105 (57.1%) | Unjudged responses are **not** assigned a perfect score |
| Judge errors | 37 | Invalid/incomplete judge outputs or API failures |

**Interpretation:** semantic judgments and rubric labels are not human-verified; do not present these numbers as independent ground-truth accuracy.

## 2. Latency, calls, and cost

| Metric | Value |
|---|---:|
| Average total latency | 4.4 s |
| Median total latency | 3.7 s |
| P90 / P95 total latency | 8.1 / 9.6 s |
| Warm-response average | 4.2 s |
| Generation requests reserved | 117 |
| Judge requests reserved | 97 |
| Generation input / output tokens (known subtotals) | 696,450 / 37,495 |
| Judge input / output tokens (known subtotals) | 543,374 / 38,827 |
| Repair frequency | 14.7% |
| Estimated generation cost | Unknown (no verified pricing supplied) |

Cost estimates exclude judge usage. Account billing/credits must be checked separately.

## 3. By question category

| Group | N | Complete | Partial | Error | Expected-status match | Valid citations | Judged |
|---|---:|---:|---:|---:|---:|---:|---:|
| clarification | 2 | 0 | 0 | 0 | 100.0% | N/A | 0 |
| comparison | 12 | 3 | 6 | 3 | 33.3% | 75.0% | 3 |
| definitions | 6 | 4 | 2 | 0 | 66.7% | 100.0% | 5 |
| experimental_setup | 7 | 6 | 1 | 0 | 85.7% | 100.0% | 5 |
| extraction_sensitive | 3 | 0 | 1 | 1 | 33.3% | 50.0% | 2 |
| false_premise | 5 | 2 | 2 | 1 | 40.0% | 80.0% | 2 |
| findings | 5 | 4 | 1 | 0 | 80.0% | 100.0% | 3 |
| general | 4 | 3 | 0 | 1 | 75.0% | 75.0% | 2 |
| insufficient | 4 | 0 | 1 | 0 | 75.0% | 100.0% | 3 |
| limitations | 9 | 8 | 1 | 0 | 88.9% | 100.0% | 5 |
| methodology | 12 | 8 | 4 | 0 | 66.7% | 100.0% | 9 |
| multi_hop | 4 | 3 | 0 | 1 | 75.0% | 75.0% | 1 |
| paper_specific | 5 | 4 | 1 | 0 | 80.0% | 100.0% | 3 |
| partial | 3 | 0 | 3 | 0 | 100.0% | 100.0% | 2 |
| quantitative | 11 | 10 | 1 | 0 | 90.9% | 100.0% | 6 |
| scope_restriction | 2 | 1 | 1 | 0 | 50.0% | 100.0% | 1 |
| single_paper_factual | 8 | 8 | 0 | 0 | 100.0% | 100.0% | 6 |
| unanswerable | 3 | 0 | 0 | 1 | 66.7% | 0.0% | 2 |

## 4. By difficulty

| Group | N | Complete | Partial | Error | Expected-status match | Valid citations | Judged |
|---|---:|---:|---:|---:|---:|---:|---:|
| difficult | 25 | 16 | 6 | 3 | 68.0% | 88.0% | 11 |
| easy | 21 | 13 | 2 | 2 | 81.0% | 88.2% | 14 |
| intermediate | 59 | 35 | 17 | 3 | 71.2% | 94.5% | 35 |

## 5. Failure categories

Counts can overlap because one answer may have multiple failure categories.

| Failure category | Count |
|---|---:|
| status_mismatch | 29 |
| citation_validation | 8 |
| invalid_model_output | 8 |
| judge_flagged_factual_issue | 4 |
| judge_flagged_citation_support | 3 |
| judge_flagged_missing_component | 2 |

## 6. Judge failures (diagnostics)

| Error stage | Count |
|---|---:|
| judgment_validation | 37 |

## 7. Questions needing review

These are **review candidates**, not automatically incorrect answers. Full details are in `per_question.csv`.

| ID | Status | Why review? | Question |
|---|---|---|---|
| GEN-003 | complete | judge error (citations_item_ids) | What three subtypes of faithfulness hallucination does the survey identify, and what does each mean? |
| GEN-004 | error | error, status mismatch, invalid citations | What hallucination detection approaches are described in this corpus? |
| GEN-006 | complete | judge error (citation_source_mismatch) | What assumptions underlie FActScore, and why do debatable facts or conflicting knowledge sources limit its app |
| GEN-007 | complete | judge error (citations_item_ids) | What are the imitative falsehoods that TruthfulQA questions are designed to elicit? |
| GEN-009 | partial | partial, status mismatch | What limitations do the SelfCheckGPT authors identify? |
| GEN-010 | error | error, status mismatch, invalid citations | Compare the methodologies of SelfCheckGPT and FActScore. |
| GEN-011 | complete | judge error (citations_item_ids) | Compare the evaluation units and findings of SelfCheckGPT and FActScore. |
| GEN-012 | partial | partial, status mismatch, judge error (claims_verdict_or_reference) | Compare the limitations of SelfCheckGPT and FActScore. |
| GEN-013 | partial | partial | Compare methods, findings, and limitations of SelfCheckGPT and FActScore. |
| GEN-014 | needs_clarification | judge error (invalid_answer_excerpt) | What does the MissingStudy paper conclude? |
| GEN-015 | partial | partial, status mismatch | What did SelfCheckGPT report for an experiment on the fictional ResearchLens-2099 dataset? |
| GEN-018 | partial | partial, status mismatch | What numerical conclusion follows from the damaged equation on SelfCheckGPT PDF page 3? |
| GEN-020 | error | error, status mismatch, invalid citations | What model names appear in the damaged Table 5 headers on SelfCheckGPT PDF page 13? |
| GEN-021 | partial | partial, status mismatch | According to the survey, what distinguishes entity-error from relation-error hallucination? |
| GEN-023 | complete | judge error (citations_item_ids) | In the survey, when is a deviation from a user instruction considered instruction inconsistency? |
| GEN-026 | complete | judge error (citations_item_ids) | What three data-related mechanisms can cause hallucinations according to the survey? |
| GEN-028 | complete | judge error (claims_verdict_or_reference) | How does the survey connect entity popularity and domain-specific knowledge to hallucination risk? |
| GEN-029 | partial | partial, status mismatch, judge error (claims_verdict_or_reference) | Why might a previously correct answer become a hallucination risk under the survey's discussion of temporal kn |
| GEN-030 | complete | judge error (citations_item_ids) | According to the survey, how can licensing restrictions affect an LLM's knowledge coverage? |
| GEN-035 | partial | partial, status mismatch | What additional access and supervision does the hidden-state classifier discussed in SelfCheckGPT require? |
| GEN-036 | partial | partial, status mismatch | How does SelfCheckGPT's MQAG variant test consistency using generated questions? |
| GEN-038 | partial | partial, status mismatch | Why does SelfCheckGPT include the main response when training its n-gram approximation? |
| GEN-039 | complete | judge error (citations_item_ids) | Which NLI model and class logits are used in SelfCheckGPT-NLI? |
| GEN-040 | complete | judge error (citations_item_ids) | How many WikiBio articles were sampled for SelfCheckGPT, and from which part of the length distribution? |
| GEN-041 | complete | judge error (citations_item_ids) | What are SelfCheckGPT's three sentence annotation labels and their numeric values? |
| GEN-043 | partial | partial, status mismatch | What temperatures were used for SelfCheckGPT's main response and stochastic samples, and how many samples were |
| GEN-044 | partial | partial, status mismatch | What trade-off does SelfCheckGPT report as the number of sampled responses increases? |
| GEN-046 | partial | partial, status mismatch | Does FActScore assess global truth or support relative to a chosen knowledge source? |
| GEN-047 | partial | partial, status mismatch, judge error (citations_item_ids) | Why did FActScore evaluate biographies against Wikipedia? |
| GEN-052 | complete | judge error (citations_item_ids) | What FActScores were reported for InstructGPT, ChatGPT, and PerplexityAI in the human evaluation? |
| GEN-053 | complete | judge error (claims_verdict_or_reference) | How does FActScore's equal-importance assumption treat individual atomic facts? |
| GEN-055 | complete | judge error (citations_item_ids) | Why should good aggregate FActScore estimator performance not be interpreted as perfect individual judgments? |
| GEN-057 | complete | judge error (citations_item_ids) | Under TruthfulQA's definition, can a truthful answer be irrelevant or noncommittal? |
| GEN-058 | complete | judge error (claims_verdict_or_reference) | Why does TruthfulQA evaluate informativeness as well as truthfulness? |
| GEN-061 | complete | judge error (citations_item_ids) | How do TruthfulQA's filtered and unfiltered question sets differ in construction and size? |
| GEN-066 | complete | judge error (citations_item_ids) | What relationship between model size, truthfulness, and informativeness is reported for TruthfulQA's studied f |
| GEN-069 | partial | partial, status mismatch | In the conversation paper, how does RAG-Sequence differ from RAG-Token? |
| GEN-074 | complete | judge error (citations_verdict_or_reference) | Which standard automatic response metrics are listed in the conversation paper? |
| GEN-076 | complete | judge error (points_verdict_or_reference) | Why can better standard F1 fail to indicate reduced hallucination in the conversation study? |
| GEN-077 | complete | judge error (citations_item_ids) | What changes in valid-unseen perplexity and valid-seen F1 were reported when RAG-Token retrieved 25 documents? |
| GEN-078 | complete | judge error (citations_item_ids) | What happened to Knowledge F1 on seen and unseen validation when RAG-Token retrieved 25 documents? |
| GEN-081 | partial | partial, status mismatch, judge error (claims_verdict_or_reference) | Compare the unit of evaluation in SelfCheckGPT and FActScore and explain why sentence-level labels can conceal |
| GEN-082 | complete | judge error (citation_source_mismatch) | Compare FActScore's treatment of factual recall with TruthfulQA's treatment of informativeness. |
| GEN-083 | partial | partial, status mismatch, judge error (citations_item_ids) | Compare the use of external knowledge in SelfCheckGPT and the conversation retrieval study. |
| GEN-084 | error | error, status mismatch, invalid citations | How do TruthfulQA and SelfCheckGPT construct evaluation data, and what different failure signals do they targe |
| GEN-085 | partial | partial, status mismatch, judge error (claims_verdict_or_reference) | Compare the source-relative support used by FActScore with Knowledge F1 in the conversation study. |
| GEN-086 | complete | judge error (claims_verdict_or_reference) | Relate the survey's long-tail knowledge concern to FActScore's observed results for rare entities. |
| GEN-087 | error | error, status mismatch, invalid citations | How do TruthfulQA's imitative falsehoods and the survey's instruction inconsistency differ as failure types? |
| GEN-088 | partial | partial, status mismatch | Compare the cost trade-offs of adding SelfCheckGPT samples with increasing retrieved documents in the conversa |
| GEN-089 | error | error, status mismatch, invalid citations | What do FActScore and the conversation study each show about why access to search does not guarantee perfect f |
| GEN-091 | complete | judge error (claims_verdict_or_reference) | Why is it wrong to conclude from TruthfulQA that larger language models always become more truthful? |
| GEN-093 | error | error, status mismatch, invalid citations | Since SelfCheckGPT needs a Wikipedia database at inference, which database version do its authors require? |
| GEN-094 | partial | partial, status mismatch, judge error (citations_item_ids) | Why did retrieving more documents always reduce hallucination in the conversation experiments? |
| GEN-095 | partial | partial, status mismatch | Is an instruction ignored for safety automatically a hallucination under the survey's definition of instructio |
| GEN-096 | partial | partial | Explain FActScore's atomic-fact unit and give its score on the fictional OceanBench-2099 dataset. |
| GEN-097 | partial | partial, judge error (citations_item_ids) | Describe TruthfulQA's question count and its evaluation of the fictional Aurora-2099 model. |
| GEN-098 | partial | partial | State the conversation study's two datasets and the serial numbers of its training GPUs. |
| GEN-100 | partial | partial, status mismatch, judge error (citations_item_ids) | Using only TruthfulQA, describe its true-zero-shot evaluation restrictions. |
| GEN-101 | needs_clarification | judge error (invalid_answer_excerpt) | What did this paper conclude about its method? |
| GEN-102 | needs_clarification | judge error (invalid_answer_excerpt) | Compare SelfCheckGPT with another paper. |
| GEN-103 | error | error, status mismatch, invalid citations | What is the exact benchmark score of the fictional Neptune-2099 model in FActScore? |

## 8. Per-question results

| ID | Category | Status | Status match | Citations valid | Judge status | Accuracy* | Completeness* | Time (s) |
|---|---|---|---|---|---|---:|---:|---:|
| GEN-001 | general | complete | True | True | evaluated | 100.0% | 100.0% | 17.3 |
| GEN-002 | general | complete | True | True | evaluated | 100.0% | 100.0% | 4.6 |
| GEN-003 | general | complete | True | True | judge_error | N/A | N/A | 3.9 |
| GEN-004 | general | error | False | False | not_evaluated | N/A | N/A | 8.0 |
| GEN-005 | paper_specific | complete | True | True | evaluated | 100.0% | 100.0% | 6.6 |
| GEN-006 | paper_specific | complete | True | True | judge_error | N/A | N/A | 3.4 |
| GEN-007 | paper_specific | complete | True | True | judge_error | N/A | N/A | 4.6 |
| GEN-008 | paper_specific | complete | True | True | evaluated | 100.0% | 100.0% | 4.4 |
| GEN-009 | paper_specific | partial | False | True | evaluated | 50.0% | 25.0% | 3.9 |
| GEN-010 | comparison | error | False | False | not_evaluated | N/A | N/A | 11.9 |
| GEN-011 | comparison | complete | True | True | judge_error | N/A | N/A | 5.2 |
| GEN-012 | comparison | partial | False | True | judge_error | N/A | N/A | 7.3 |
| GEN-013 | comparison | partial | True | True | evaluated | 100.0% | 100.0% | 6.8 |
| GEN-014 | insufficient | needs_clarification | True | None | judge_error | N/A | N/A | 0.0 |
| GEN-015 | insufficient | partial | False | True | evaluated | 100.0% | 50.0% | 2.1 |
| GEN-016 | insufficient | abstained | True | None | evaluated | N/A | 100.0% | 3.1 |
| GEN-017 | insufficient | abstained | True | None | evaluated | N/A | 100.0% | 1.5 |
| GEN-018 | extraction_sensitive | partial | False | True | evaluated | 0.0% | 50.0% | 2.6 |
| GEN-019 | extraction_sensitive | abstained | True | None | evaluated | N/A | 100.0% | 3.5 |
| GEN-020 | extraction_sensitive | error | False | False | not_evaluated | N/A | N/A | 3.2 |
| GEN-021 | definitions | partial | False | True | evaluated | 100.0% | 100.0% | 6.8 |
| GEN-022 | definitions | complete | True | True | evaluated | 100.0% | 100.0% | 4.0 |
| GEN-023 | single_paper_factual | complete | True | True | judge_error | N/A | N/A | 2.9 |
| GEN-024 | methodology | complete | True | True | evaluated | 100.0% | 100.0% | 3.1 |
| GEN-025 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 3.9 |
| GEN-026 | methodology | complete | True | True | judge_error | N/A | N/A | 2.7 |
| GEN-027 | limitations | complete | True | True | evaluated | 100.0% | 100.0% | 2.9 |
| GEN-028 | findings | complete | True | True | judge_error | N/A | N/A | 5.9 |
| GEN-029 | limitations | partial | False | True | judge_error | N/A | N/A | 6.3 |
| GEN-030 | limitations | complete | True | True | judge_error | N/A | N/A | 3.3 |
| GEN-031 | findings | complete | True | True | evaluated | 100.0% | 100.0% | 2.2 |
| GEN-032 | multi_hop | complete | True | True | evaluated | 100.0% | 50.0% | 6.4 |
| GEN-033 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 1.8 |
| GEN-034 | limitations | complete | True | True | evaluated | 100.0% | 100.0% | 1.8 |
| GEN-035 | methodology | partial | False | True | evaluated | 100.0% | 100.0% | 4.1 |
| GEN-036 | methodology | partial | False | True | evaluated | 100.0% | 100.0% | 3.5 |
| GEN-037 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 2.7 |
| GEN-038 | methodology | partial | False | True | evaluated | 100.0% | 50.0% | 2.2 |
| GEN-039 | methodology | complete | True | True | judge_error | N/A | N/A | 4.8 |
| GEN-040 | quantitative | complete | True | True | judge_error | N/A | N/A | 2.5 |
| GEN-041 | quantitative | complete | True | True | judge_error | N/A | N/A | 3.8 |
| GEN-042 | experimental_setup | complete | True | True | evaluated | 100.0% | 100.0% | 2.1 |
| GEN-043 | quantitative | partial | False | True | evaluated | 100.0% | 100.0% | 3.6 |
| GEN-044 | findings | partial | False | True | evaluated | 0.0% | 50.0% | 3.8 |
| GEN-045 | definitions | complete | True | True | evaluated | 100.0% | 100.0% | 3.9 |
| GEN-046 | definitions | partial | False | True | evaluated | 100.0% | 100.0% | 8.2 |
| GEN-047 | experimental_setup | partial | False | True | judge_error | N/A | N/A | 6.8 |
| GEN-048 | quantitative | complete | True | True | evaluated | 100.0% | 100.0% | 3.0 |
| GEN-049 | methodology | complete | True | True | evaluated | 100.0% | 100.0% | 4.6 |
| GEN-050 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 2.2 |
| GEN-051 | quantitative | complete | True | True | evaluated | 100.0% | 100.0% | 1.8 |
| GEN-052 | quantitative | complete | True | True | judge_error | N/A | N/A | 3.7 |
| GEN-053 | limitations | complete | True | True | judge_error | N/A | N/A | 2.9 |
| GEN-054 | limitations | complete | True | True | evaluated | 100.0% | 50.0% | 2.8 |
| GEN-055 | limitations | complete | True | True | judge_error | N/A | N/A | 3.0 |
| GEN-056 | quantitative | complete | True | True | evaluated | 100.0% | 100.0% | 2.2 |
| GEN-057 | definitions | complete | True | True | judge_error | N/A | N/A | 2.6 |
| GEN-058 | methodology | complete | True | True | judge_error | N/A | N/A | 3.7 |
| GEN-059 | quantitative | complete | True | True | evaluated | 100.0% | 100.0% | 2.7 |
| GEN-060 | experimental_setup | complete | True | True | evaluated | 100.0% | 100.0% | 3.0 |
| GEN-061 | experimental_setup | complete | True | True | judge_error | N/A | N/A | 8.4 |
| GEN-062 | quantitative | complete | True | True | evaluated | 100.0% | 100.0% | 2.6 |
| GEN-063 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 2.9 |
| GEN-064 | experimental_setup | complete | True | True | evaluated | 100.0% | 100.0% | 3.7 |
| GEN-065 | methodology | complete | True | True | evaluated | 100.0% | 100.0% | 2.6 |
| GEN-066 | findings | complete | True | True | judge_error | N/A | N/A | 4.6 |
| GEN-067 | methodology | complete | True | True | evaluated | 100.0% | 100.0% | 2.7 |
| GEN-068 | limitations | complete | True | True | evaluated | 100.0% | 100.0% | 3.0 |
| GEN-069 | methodology | partial | False | True | evaluated | 100.0% | 100.0% | 8.6 |
| GEN-070 | methodology | complete | True | True | evaluated | 100.0% | 100.0% | 2.6 |
| GEN-071 | experimental_setup | complete | True | True | evaluated | 100.0% | 100.0% | 4.8 |
| GEN-072 | experimental_setup | complete | True | True | evaluated | 100.0% | 50.0% | 2.8 |
| GEN-073 | single_paper_factual | complete | True | True | evaluated | 100.0% | 100.0% | 2.1 |
| GEN-074 | single_paper_factual | complete | True | True | judge_error | N/A | N/A | 2.1 |
| GEN-075 | definitions | complete | True | True | evaluated | 100.0% | 100.0% | 2.8 |
| GEN-076 | multi_hop | complete | True | True | judge_error | N/A | N/A | 4.4 |
| GEN-077 | quantitative | complete | True | True | judge_error | N/A | N/A | 2.6 |
| GEN-078 | quantitative | complete | True | True | judge_error | N/A | N/A | 4.4 |
| GEN-079 | findings | complete | True | True | evaluated | 100.0% | 100.0% | 2.8 |
| GEN-080 | limitations | complete | True | True | evaluated | 100.0% | 100.0% | 4.8 |
| GEN-081 | comparison | partial | False | True | judge_error | N/A | N/A | 9.9 |
| GEN-082 | comparison | complete | True | True | judge_error | N/A | N/A | 9.6 |
| GEN-083 | comparison | partial | False | True | judge_error | N/A | N/A | 6.6 |
| GEN-084 | comparison | error | False | False | not_evaluated | N/A | N/A | 12.0 |
| GEN-085 | comparison | partial | False | True | judge_error | N/A | N/A | 6.2 |
| GEN-086 | multi_hop | complete | True | True | judge_error | N/A | N/A | 9.6 |
| GEN-087 | comparison | error | False | False | not_evaluated | N/A | N/A | 8.1 |
| GEN-088 | comparison | partial | False | True | evaluated | 100.0% | 50.0% | 4.1 |
| GEN-089 | multi_hop | error | False | False | not_evaluated | N/A | N/A | 12.4 |
| GEN-090 | comparison | complete | True | True | evaluated | 100.0% | 100.0% | 5.9 |
| GEN-091 | false_premise | complete | True | True | judge_error | N/A | N/A | 3.7 |
| GEN-092 | false_premise | complete | True | True | evaluated | 100.0% | 100.0% | 3.0 |
| GEN-093 | false_premise | error | False | False | not_evaluated | N/A | N/A | 3.0 |
| GEN-094 | false_premise | partial | False | True | judge_error | N/A | N/A | 4.2 |
| GEN-095 | false_premise | partial | False | True | evaluated | 100.0% | 50.0% | 5.9 |
| GEN-096 | partial | partial | True | True | evaluated | 100.0% | 50.0% | 4.7 |
| GEN-097 | partial | partial | True | True | judge_error | N/A | N/A | 5.3 |
| GEN-098 | partial | partial | True | True | evaluated | 50.0% | 100.0% | 4.0 |
| GEN-099 | scope_restriction | complete | True | True | evaluated | 100.0% | 100.0% | 3.5 |
| GEN-100 | scope_restriction | partial | False | True | judge_error | N/A | N/A | 6.8 |
| GEN-101 | clarification | needs_clarification | True | None | judge_error | N/A | N/A | 0.0 |
| GEN-102 | clarification | needs_clarification | True | None | judge_error | N/A | N/A | 0.0 |
| GEN-103 | unanswerable | error | False | False | not_evaluated | N/A | N/A | 2.0 |
| GEN-104 | unanswerable | abstained | True | None | evaluated | N/A | 100.0% | 2.9 |
| GEN-105 | unanswerable | abstained | True | None | evaluated | N/A | 100.0% | 2.5 |

*Accuracy and completeness shown only for successfully judged questions. They are unverified automated judgments.*

## Files

- `report.md`: this report
- `per_question.csv`: all question-level metrics and answers
- `answers.md`: readable answers with source paper/pages and limitations
- `results.jsonl`: complete evidence, citations, prompts' outputs and judge details per case
- `summary.json`: machine-readable summary
- `manifest.json`: settings and dataset fingerprint
- `request-budget.json`: reserved API requests (if available)
- `tests.txt`: offline test log (if tests were run)

