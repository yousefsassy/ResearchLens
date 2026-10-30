"""Rebuild the versioned benchmark from curated questions and indexed source text.

References are machine-checked against the corpus; rubrics are not human verified.
Existing draft questions remain unchanged in their original file.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.generation.papers import interpret, load_catalog

# question | category | difficulty | reference chunk IDs | expected answer points (~ separated)
SPECS = """
According to the survey, what distinguishes entity-error from relation-error hallucination?|definitions|easy|P001-p006-c004|Entity errors name erroneous entities.~Relation errors assert wrong relations between entities.
What does factual fabrication mean in the survey's taxonomy?|definitions|easy|P001-p006-c004|Facts unverifiable against established real-world knowledge; includes unverifiability and overclaim hallucination.
In the survey, when is a deviation from a user instruction considered instruction inconsistency?|single_paper_factual|intermediate|P001-p007-c002|Unintentional misalignment with non-malicious instructions, distinguished from safety-motivated deviations.
How does the survey distinguish logical inconsistency within reasoning steps from inconsistency with a final answer?|methodology|intermediate|P001-p007-c002|Logical contradictions can occur among steps or between steps and the final answer.
Which two kinds of training data does the survey discuss, and what capabilities do they provide?|single_paper_factual|easy|P001-p007-c003|Pre-training supplies general capabilities and factual knowledge.~Alignment data teach instruction following and alignment with preferences.
What three data-related mechanisms can cause hallucinations according to the survey?|methodology|intermediate|P001-p007-c003|Misinformation and biases in pre-training, knowledge boundaries, and inferior alignment data.
What two sources of knowledge boundaries does the survey identify?|limitations|intermediate|P001-p009-c003|Failure to memorize all knowledge, especially long-tail facts.~Boundaries of the training corpus, including changing and copyright-restricted information.
How does the survey connect entity popularity and domain-specific knowledge to hallucination risk?|findings|intermediate|P001-p009-c004|Accuracy is associated with document volume or entity popularity.~General-domain training can leave specialized knowledge deficits.
Why might a previously correct answer become a hallucination risk under the survey's discussion of temporal knowledge boundaries?|limitations|intermediate|P001-p010-c001|Internal knowledge becomes outdated; queries beyond its temporal scope can elicit outdated answers or fabricated facts.
According to the survey, how can licensing restrictions affect an LLM's knowledge coverage?|limitations|intermediate|P001-p010-c001|Restrictions can exclude proprietary and copyrighted knowledge, creating gaps that contribute to hallucinations.
What relationship between new factual knowledge during supervised fine-tuning and hallucinations does the survey report?|findings|difficult|P001-p010-c002|The cited study reports difficulty learning new knowledge during SFT and correlation with increased hallucination; do not assert a universal causal law.
How do pre-training knowledge boundaries and alignment data together explain hallucination risks in the survey?|multi_hop|difficult|P001-p009-c003,P001-p010-c002|Pre-training cannot cover or retain all knowledge.~Alignment may introduce facts beyond those boundaries and is associated with increased hallucination.
Which five SelfCheckGPT consistency variants are listed by the authors?|single_paper_factual|easy|P002-p002-c002|BERTScore, question answering, n-gram, NLI, and LLM prompting.
Why can perturbing factual texts produce an imperfect hallucination-detection dataset, according to SelfCheckGPT's related work?|limitations|intermediate|P002-p002-c003|Perturbed factual texts may not reflect genuine LLM hallucinations.
What additional access and supervision does the hidden-state classifier discussed in SelfCheckGPT require?|methodology|intermediate|P002-p002-c003|It uses internal hidden representations and labeled supervised training data; these states may be unavailable through APIs.
How does SelfCheckGPT's MQAG variant test consistency using generated questions?|methodology|intermediate|P002-p004-c002|Generate multiple-choice questions from the main response.~An independent answering system answers using sampled responses; consistency should yield similar answers.
Which backbone is used for BERTScore in SelfCheckGPT?|single_paper_factual|easy|P002-p004-c002|RoBERTa-Large.
Why does SelfCheckGPT include the main response when training its n-gram approximation?|methodology|difficult|P002-p004-c003|Including the response smooths the counts by increasing each response token's count by one.
Which NLI model and class logits are used in SelfCheckGPT-NLI?|methodology|difficult|P002-p005-c001|DeBERTa-v3-large fine-tuned on MNLI.~Entailment and contradiction logits are used; neutral is ignored.
How many WikiBio articles were sampled for SelfCheckGPT, and from which part of the length distribution?|quantitative|intermediate|P002-p005-c003|238 articles were randomly sampled from the longest 20 percent of WikiBio test paragraphs.
What are SelfCheckGPT's three sentence annotation labels and their numeric values?|quantitative|easy|P002-p005-c003|Major inaccurate: 1; minor inaccurate: 0.5; accurate: 0.
How were annotator disagreements resolved in the SelfCheckGPT dataset?|experimental_setup|intermediate|P002-p005-c004|For the doubly annotated subset, agreement is retained; disagreements receive the worse-case label.
What temperatures were used for SelfCheckGPT's main response and stochastic samples, and how many samples were drawn?|quantitative|intermediate|P002-p006-c001,P002-p006-c002|Main response temperature 0.0.~Stochastic temperature 1.0 with 20 samples.
What trade-off does SelfCheckGPT report as the number of sampled responses increases?|findings|intermediate|P002-p009-c001|Performance improves smoothly with diminishing gains while computational costs increase; n-gram needs the most samples before plateauing.
What is an atomic fact in FActScore, and why is a sentence sometimes too coarse a unit?|definitions|intermediate|P003-p003-c002|A short statement conveying one piece of information.~A sentence can mix supported and unsupported information.
Does FActScore assess global truth or support relative to a chosen knowledge source?|definitions|easy|P003-p003-c004|Support is evaluated relative to a particular knowledge source considered trustworthy by the user.
Why did FActScore evaluate biographies against Wikipedia?|experimental_setup|intermediate|P003-p004-c001|Biographies are specific and objective, span diverse people, and Wikipedia offers reasonable coverage and self-consistency.
How many people entities were sampled in FActScore's human evaluation, and where were they sampled from?|quantitative|easy|P003-p004-c001|183 entities sampled from Wikidata with corresponding Wikipedia pages.
How were machine-generated atomic facts used to assist FActScore's human annotators?|methodology|intermediate|P003-p004-c002|InstructGPT supplies preliminary atomic facts that annotators can revise to save annotation time.
Which three annotation labels does FActScore assign to atomic facts?|single_paper_factual|easy|P003-p004-c002|Irrelevant, Supported, and Not-supported; relevant facts are validated against English Wikipedia.
What hourly pay range and per-generation annotation cost does FActScore report?|quantitative|intermediate|P003-p004-c002|Freelancers received 15-25 USD per hour; annotation cost was about 4 USD per generation.
What FActScores were reported for InstructGPT, ChatGPT, and PerplexityAI in the human evaluation?|quantitative|intermediate|P003-p004-c003|InstructGPT 42.5 percent; ChatGPT 58.3 percent; PerplexityAI 71.5 percent.
How does FActScore's equal-importance assumption treat individual atomic facts?|limitations|intermediate|P003-p003-c003|Every atomic fact is given equal importance.
Why is FActScore unsuitable for some nuanced or intentionally deceptive human-written text?|limitations|difficult|P003-p010-c001|Nuance, debatable claims, conflicting sources, and intentional or implicit deception can violate its applicability assumptions.
Why should good aggregate FActScore estimator performance not be interpreted as perfect individual judgments?|limitations|difficult|P003-p010-c001|Individual judgments are imperfect and the best estimator variant depends on linguistic complexity and similarity to human-written text.
How many generations and models were included in FActScore's larger automated case study, and what human cost was estimated?|quantitative|intermediate|P003-p002-c002|6500 generations from 13 models; estimated human evaluation cost 26000 USD.
Under TruthfulQA's definition, can a truthful answer be irrelevant or noncommittal?|definitions|easy|P004-p004-c001|Yes; truthfulness requires avoiding false assertions and allows refusal, uncertainty, or true irrelevant answers.
Why does TruthfulQA evaluate informativeness as well as truthfulness?|methodology|intermediate|P004-p004-c002|Always answering No comment can be perfectly truthful; informativeness measures useful reduction of the question's uncertainty.
How many questions and categories does TruthfulQA contain?|quantitative|easy|P004-p004-c002|817 questions across 38 categories.
What is the median question length in TruthfulQA, and what reference material accompanies a question?|experimental_setup|intermediate|P004-p004-c002|Median length is 9 words; questions have true and false reference answers and a supporting source.
How do TruthfulQA's filtered and unfiltered question sets differ in construction and size?|experimental_setup|intermediate|P004-p004-c003|437 filtered questions were tested against GPT-3-175B.~380 unfiltered questions were written without testing on that target.
What disagreement rate did TruthfulQA's external validator report on its sample of reference answers?|quantitative|intermediate|P004-p004-c004|The validator disagreed on 7 percent of 100 sampled questions.
What four model families were evaluated in the main TruthfulQA baseline experiments?|single_paper_factual|easy|P004-p005-c001|GPT-3, GPT-Neo/J, GPT-2, and UnifiedQA.
What makes TruthfulQA's baseline setting true zero-shot?|experimental_setup|difficult|P004-p005-c002|No gradient updates and no TruthfulQA examples in prompts.~Prompts and hyperparameters must not be tuned on TruthfulQA examples.
How does TruthfulQA score its multiple-choice task?|methodology|difficult|P004-p005-c004|Compute likelihoods of reference answers conditional on the question and prompt; sum normalized likelihood over true answers.
What relationship between model size, truthfulness, and informativeness is reported for TruthfulQA's studied families?|findings|intermediate|P004-p007-c001|Larger models were generally less truthful within families but more informative; restrict the finding to the studied setting.
How were TruthfulQA's matched control questions constructed and what scaling trend did they show?|methodology|difficult|P004-p007-c003|Edit 1-3 words into straightforward trivia or commonsense questions.~Control truthfulness improved with model size.
What did TruthfulQA's paraphrase experiment suggest, and what alternative explanation remains difficult to rule out?|limitations|difficult|P004-p007-c004|Scores changed little and inverse scaling remained.~Non-imitative semantic weaknesses were harder to rule out.
In the conversation paper, how does RAG-Sequence differ from RAG-Token?|methodology|intermediate|P005-p003-c002|Sequence marginalizes separately generated document-conditioned sequences.~Token marginalizes across documents at each token.
How does Fusion-in-Decoder combine retrieved documents in the conversation paper's description?|methodology|intermediate|P005-p003-c003|Encode document-context pairs independently and concatenate encoder outputs so the decoder attends to all representations together.
Which dialogue datasets are used by the conversation paper, and what topics do they cover?|experimental_setup|easy|P005-p004-c004|Wizard of Wikipedia covers varied topics; CMU_DoG covers movies.
What distinguishes seen and unseen splits in the conversation experiments?|experimental_setup|intermediate|P005-p004-c004|Unseen topics or movies were not discussed in training; WoW supplies splits while CMU_DoG splits were constructed by the authors.
What external knowledge collection is used for retrieval in the conversation experiments?|single_paper_factual|easy|P005-p004-c004|The standard KILT Wikipedia dump, used for both datasets.
Which standard automatic response metrics are listed in the conversation paper?|single_paper_factual|easy|P005-p004-c004|Perplexity, unigram F1, BLEU-4, and ROUGE-L, with Knowledge F1 as an additional metric.
What does Knowledge F1 compare, and how does it differ from standard F1?|definitions|intermediate|P005-p005-c003|Standard F1 measures overlap with the human response.~Knowledge F1 measures overlap with the knowledge grounding that response.
Why can better standard F1 fail to indicate reduced hallucination in the conversation study?|multi_hop|difficult|P005-p005-c003,P005-p006-c003|F1 includes conversational word overlap unrelated to knowledge.~More retrieved documents improved F1 while Knowledge F1 fell and human-rated hallucination rose.
What changes in valid-unseen perplexity and valid-seen F1 were reported when RAG-Token retrieved 25 documents?|quantitative|difficult|P005-p006-c003|Perplexity changed from 13.4 to 13.0 on valid unseen; F1 from 22.5 to 22.6 on valid seen.
What happened to Knowledge F1 on seen and unseen validation when RAG-Token retrieved 25 documents?|quantitative|difficult|P005-p006-c003|Seen KF1 fell from 26.0 to 24.7; unseen KF1 from 22.7 to 21.1.
Did reducing hallucination necessarily sacrifice conversational ability in the conversation experiments?|findings|intermediate|P005-p006-c003|Consistency and engagingness were generally comparable, with slight engagingness drops for some models; the authors did not find an overall sacrifice.
What caution does the conversation paper give about conditioning on more retrieved documents?|limitations|intermediate|P005-p009-c001|All studied models suffered more hallucination when conditioned on more documents; do not equate retrieval volume with factuality.
Compare the unit of evaluation in SelfCheckGPT and FActScore and explain why sentence-level labels can conceal mixed support.|comparison|difficult|P002-p005-c003,P003-p003-c002|SelfCheckGPT annotates sentences.~FActScore uses atomic facts because a sentence can contain supported and unsupported information.
Compare FActScore's treatment of factual recall with TruthfulQA's treatment of informativeness.|comparison|difficult|P003-p010-c002,P004-p004-c002|FActScore measures precision and recommends abstention rate and fact count alongside it.~TruthfulQA separately measures informativeness because noncommittal answers can be truthful.
Compare the use of external knowledge in SelfCheckGPT and the conversation retrieval study.|comparison|intermediate|P002-p002-c002,P005-p004-c004|SelfCheckGPT measures consistency of samples without an external database.~The conversation study retrieves from KILT Wikipedia for generation.
How do TruthfulQA and SelfCheckGPT construct evaluation data, and what different failure signals do they target?|comparison|difficult|P004-p004-c003,P002-p005-c003|TruthfulQA authors elicit likely false answers with adversarial questions.~SelfCheckGPT generates WikiBio passages and annotates sentence factuality.
Compare the source-relative support used by FActScore with Knowledge F1 in the conversation study.|comparison|difficult|P003-p003-c004,P005-p005-c003|FActScore checks atomic support against a trusted source.~Knowledge F1 measures lexical overlap with human grounding knowledge; the two measures are not interchangeable.
Relate the survey's long-tail knowledge concern to FActScore's observed results for rare entities.|multi_hop|difficult|P001-p009-c004,P003-p002-c002|The survey associates accuracy with document volume and popularity.~FActScore reports decreasing scores with rarity, including ChatGPT from 80 to 16 percent.
How do TruthfulQA's imitative falsehoods and the survey's instruction inconsistency differ as failure types?|comparison|intermediate|P004-p001-c004,P001-p007-c002|Imitative falsehoods have high likelihood under training data.~Instruction inconsistency deviates from a non-malicious user directive.
Compare the cost trade-offs of adding SelfCheckGPT samples with increasing retrieved documents in the conversation study.|comparison|difficult|P002-p009-c001,P005-p006-c003|More samples improve consistency detection with diminishing returns and added computation.~More documents can worsen hallucination despite improving ordinary metrics; no shared quantitative ranking.
What do FActScore and the conversation study each show about why access to search does not guarantee perfect factuality?|multi_hop|difficult|P003-p004-c003,P005-p006-c003|Search-augmented PerplexityAI attained 71.5 percent FActScore.~More retrieved documents sometimes increased human-rated hallucination.
Compare the assumptions about evidence consistency in FActScore with SelfCheckGPT's consistency-of-samples premise.|comparison|difficult|P003-p003-c003,P002-p002-c002|FActScore assumes nonconflicting knowledge and undebatable support.~SelfCheckGPT expects sampled responses to agree on known facts and diverge on hallucinated ones.
Why is it wrong to conclude from TruthfulQA that larger language models always become more truthful?|false_premise|intermediate|P004-p007-c001|The studied families generally showed inverse scaling in truthfulness, even though informativeness increased; do not universalize the finding.
Since FActScore measures recall, how does it penalize omitted information?|false_premise|intermediate|P003-p010-c002|Reject the premise: FActScore measures precision, not recall, and may miss important omitted information.
Since SelfCheckGPT needs a Wikipedia database at inference, which database version do its authors require?|false_premise|easy|P002-p002-c002|Reject the premise: SelfCheckGPT requires no external database for its sampling-based consistency check.
Why did retrieving more documents always reduce hallucination in the conversation experiments?|false_premise|intermediate|P005-p009-c001|Reject the premise: conditioning on more documents increased hallucination in the studied models.
Is an instruction ignored for safety automatically a hallucination under the survey's definition of instruction inconsistency?|false_premise|intermediate|P001-p007-c002|No; the definition concerns unintentional deviation from non-malicious instructions and distinguishes safety guidelines.
Explain FActScore's atomic-fact unit and give its score on the fictional OceanBench-2099 dataset.|partial|intermediate|P003-p003-c002|An atomic fact conveys one piece of information.~The fictional benchmark score is unavailable and must not be invented.
Describe TruthfulQA's question count and its evaluation of the fictional Aurora-2099 model.|partial|intermediate|P004-p004-c002|TruthfulQA has 817 questions.~No evaluation of the fictional model is available.
State the conversation study's two datasets and the serial numbers of its training GPUs.|partial|intermediate|P005-p004-c004|Wizard of Wikipedia and CMU_DoG.~GPU serial numbers are not provided and should be reported as missing.
Using only the hallucination survey, explain its two sources of knowledge boundaries.|scope_restriction|intermediate|P001-p009-c003|Incomplete memorization, especially long-tail knowledge.~Boundaries of the pre-training corpus, including evolving and restricted information.
Using only TruthfulQA, describe its true-zero-shot evaluation restrictions.|scope_restriction|intermediate|P004-p005-c002|No gradient updates or benchmark examples in prompts, and no tuning on benchmark questions.
What did this paper conclude about its method?|clarification|easy||Ask which paper is intended before answering.
Compare SelfCheckGPT with another paper.|clarification|easy||Ask the user to identify the second paper.
What is the exact benchmark score of the fictional Neptune-2099 model in FActScore?|unanswerable|easy||Abstain; no such reported evaluation exists in the indexed papers.
Using only the conversation paper, what vaccine dosing schedule does it prescribe?|unanswerable|easy||Abstain; the paper does not prescribe a vaccine dosing schedule.
Using only FActScore, what are the private account credentials of its annotators?|unanswerable|easy||Abstain; no credentials are provided by the research evidence.
"""


def build(target=None):
    corpus = {r["chunk_id"]: r for r in map(json.loads, (ROOT / "data/processed/chunks.jsonl").read_text(encoding="utf-8").splitlines())}
    original = [json.loads(line) for line in (ROOT / "eval/generation_questions.draft.jsonl").read_text(encoding="utf-8").splitlines()]
    extra_refs = {
        "GEN-004": ["P002-p002-c002", "P003-p003-c004"],
        "GEN-009": ["P002-p009-c001", "P002-p008-c001"],
        "GEN-010": ["P002-p002-c002", "P003-p001-c002"],
        "GEN-011": ["P002-p005-c003", "P002-p006-c003", "P003-p003-c002", "P003-p004-c003"],
        "GEN-012": ["P002-p009-c001", "P003-p010-c001"],
        "GEN-013": ["P002-p002-c002", "P003-p003-c003", "P002-p009-c001", "P003-p010-c001"],
    }
    cases = []
    legacy_points = {
        "GEN-001": "Data, training, and inference.",
        "GEN-002": "Intrinsic hallucination conflicts with the source context.~Extrinsic hallucination cannot be verified using the source context or external knowledge.",
        "GEN-003": "Instruction inconsistency deviates from non-malicious instructions.~Context inconsistency conflicts with supplied context.~Logical inconsistency contradicts reasoning steps or the final answer.",
        "GEN-004": "SelfCheckGPT tests consistency across sampled responses.~FActScore validates atomic facts against an external knowledge source.",
        "GEN-005": "Facts known to the model tend to recur consistently across samples while hallucinated facts may diverge.~Only sampled responses are needed, without an external database.",
        "GEN-006": "Support is assumed undebatable, atomic facts equally important, and knowledge nonconflicting.~Nuanced debatable facts or conflicting sources violate these assumptions.",
        "GEN-007": "Imitative falsehoods are false statements with high likelihood on the training distribution.",
        "GEN-008": "FActScore measures precision rather than recall and can miss crucial omissions.~Report abstention percentage and average atomic-fact count alongside it.",
        "GEN-009": "More samples incur additional computational cost with diminishing performance gains.~Prompt-based consistency checking can be computationally heavy.",
        "GEN-010": "SelfCheckGPT checks consistency across generated samples without an external database.~FActScore decomposes text into atomic facts and measures support against a knowledge source.",
        "GEN-011": "SelfCheckGPT annotates sentence factuality and reports probability baselines associated with factuality.~FActScore uses atomic facts and reports 42.5, 58.3 and 71.5 percent for InstructGPT, ChatGPT and PerplexityAI.~Different units and tasks prevent a direct ranking of the two methods from these metrics.",
        "GEN-012": "SelfCheckGPT sampling increases computational cost and has diminishing gains.~FActScore is restricted by debatable facts and conflicting knowledge sources.",
    }
    for case in original:
        case.pop("fixed_evidence", None)
        refs = [r["chunk_id"] for r in case["reference_sources"] if "chunk_id" in r]
        refs = extra_refs.get(case["question_id"], refs)
        case["reference_sources"] = []
        case["difficulty"] = "difficult" if case["category"] == "comparison" else "intermediate"
        case["expected_answerability"] = {"complete": "answerable", "partial": "partial", "abstained": "unanswerable", "needs_clarification": "clarification"}[case["expected_status"]]
        case["acceptable_statuses"] = [case["expected_status"]]
        case["required_aspects"] = []
        case["important_points"] = [dict(point_id=k, text=v, reference_chunk_ids=refs) for k, v in case["required_components"].items()]
        if case["question_id"] in legacy_points:
            case["important_points"] = [dict(point_id=f"C{i}", text=v, reference_chunk_ids=refs)
                                        for i,v in enumerate(legacy_points[case["question_id"]].split("~"), 1)]
        if not case["important_points"]:
            case["important_points"] = [dict(point_id="C1", text="Request the missing paper identity." if case["expected_status"] == "needs_clarification" else "Do not fabricate the requested unsupported information; explain the evidence gap and abstain.", reference_chunk_ids=[])]
        if case["question_id"] == "GEN-013":
            case["acceptable_statuses"] = ["complete", "partial"]
            case["notes"] += " Original partial expectation was a fixed-evidence stress case; end-to-end retrieval can support both papers."
            case["important_points"] = [dict(point_id="C1", text="SelfCheckGPT uses sample consistency; FActScore validates atomic facts against a knowledge source. Attribute findings and limitations to each paper.", reference_chunk_ids=refs)]
        for chunk_id in refs:
            source = corpus[chunk_id]
            case["reference_sources"].append({k: source[k] for k in ["chunk_id", "paper_id", "pdf_page", "pdf_filename"]} | {"quote": source["text"]})
        cases.append(case)
    for index, line in enumerate(SPECS.strip().splitlines(), 21):
        question, category, difficulty, raw_refs, points = line.split("|")
        refs = raw_refs.split(",") if raw_refs else []
        papers = list(dict.fromkeys(corpus[r]["paper_id"] for r in refs))
        if not papers and "FActScore" in question:
            papers = ["P003"]
        if not papers and "conversation paper" in question:
            papers = ["P005"]
        status = {"partial": "partial", "unanswerable": "abstained", "clarification": "needs_clarification"}.get(category, "complete")
        components = {f"C{i}": point for i, point in enumerate(points.split("~"), 1)}
        sources = [{k: corpus[r][k] for k in ["chunk_id", "paper_id", "pdf_page", "pdf_filename"]} | {"quote": corpus[r]["text"]} for r in refs]
        cases.append(dict(question_id=f"GEN-{index:03}", question=question, category=category,
            difficulty=difficulty, paper_ids=papers or None, answer_type="comparison" if len(papers) == 2 else "auto",
            expected_status=status, acceptable_statuses=[status],
            expected_answerability={"complete":"answerable", "partial":"partial", "abstained":"unanswerable", "needs_clarification":"clarification"}[status],
            required_components=components, important_points=[dict(point_id=k, text=v, reference_chunk_ids=refs) for k,v in components.items()],
            required_aspects={"methodology":["methods"], "limitations":["limitations"], "findings":["findings"], "quantitative":["findings"]}.get(category, []),
            reference_sources=sources, human_verified=False, reviewer=None,
            notes="Corpus-grounded draft rubric, not human-verified ground truth. Do not infer universal conclusions from a paper-specific result.",
            tracks=["end-to-end"]))
    assert len(cases) >= 100
    catalog = load_catalog(ROOT / "data/papers_generation.json")
    for case in cases:
        case["required_aspects"] = interpret(case["question"], case["paper_ids"], case["answer_type"], catalog).aspects
        if case["expected_answerability"] in {"clarification", "unanswerable"}:
            case["required_aspects"] = []
    target = target or ROOT / "eval/benchmark.v1.jsonl"
    if target.exists():
        raise ValueError("Benchmark exists; review changes instead of overwriting it.")
    target.write_text("".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8")
    print(f"Created {len(cases)} benchmark cases.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    build(parser.parse_args().output)
