"""Append corpus-expansion questions to the frozen v1 benchmark.

The v1 questions and references are copied unchanged. Only new questions for
P006-P008 are added. Run from the repository root:

    python eval/expand_benchmark_v2.py
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generation.citations import normalize_whitespace


V1 = ROOT / "eval/benchmark.v1.jsonl"
V2 = ROOT / "eval/benchmark.v2.jsonl"
CORPUS = ROOT / "data/processed/chunks.jsonl"


def build():
    if V2.exists():
        raise SystemExit(f"{V2} already exists; preserve the frozen benchmark")

    chunks = {
        row["chunk_id"]: row
        for row in map(json.loads, CORPUS.read_text(encoding="utf-8").splitlines())
    }
    cases = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]

    def add(question_id, question, category, difficulty, paper_id, refs, points, aspects=()):
        reference_sources = []
        for chunk_id, quote in refs:
            source = chunks[chunk_id]
            if source["paper_id"] != paper_id:
                raise ValueError(f"{chunk_id} is not from {paper_id}")
            if normalize_whitespace(quote) not in normalize_whitespace(source["text"]):
                raise ValueError(f"quote not found in {chunk_id}: {quote!r}")
            reference_sources.append({
                "chunk_id": chunk_id,
                "paper_id": source["paper_id"],
                "pdf_filename": source["pdf_filename"],
                "pdf_page": source["pdf_page"],
                "quote": quote,
            })
        if len({item["chunk_id"] for item in reference_sources}) != len(reference_sources):
            raise ValueError(f"{question_id}: duplicate reference chunk")
        important_points = [
            {"point_id": f"C{i}", "text": text, "reference_chunk_ids": [chunk_id]}
            for i, (text, chunk_id) in enumerate(points, 1)
        ]
        cases.append({
            "question_id": question_id,
            "question": question,
            "category": category,
            "difficulty": difficulty,
            "paper_ids": [paper_id],
            "answer_type": "auto",
            "expected_status": "complete",
            "acceptable_statuses": ["complete"],
            "expected_answerability": "answerable",
            "required_components": {p["point_id"]: p["text"] for p in important_points},
            "important_points": important_points,
            "required_aspects": list(aspects),
            "reference_sources": reference_sources,
            "fixed_evidence": [],
            "human_verified": False,
            "reviewer": None,
            "notes": "Draft question added for the eight-paper corpus; not human-verified.",
            "tracks": ["end-to-end"],
        })

    # P006 - Survey of Hallucination in Natural Language Generation
    add(
        "GEN-106",
        "What are the two main types of hallucination described in the NLG survey?",
        "definitions", "easy", "P006",
        [("P006-p004-c003",
          "The generated output that contradicts the source content.")],
        [
            ("Intrinsic hallucination contradicts the source content.", "P006-p004-c003"),
            ("Extrinsic hallucination cannot be verified from the source content.", "P006-p004-c003"),
        ],
    )
    add(
        "GEN-107",
        "Why is extrinsic hallucination not always considered erroneous in the NLG survey?",
        "limitations", "intermediate", "P006",
        [("P006-p004-c003",
          "Notably, the extrinsic hallucination is not always erroneous because it could be from factually\ncorrect external information")],
        [
            ("It can come from factually correct external information.", "P006-p004-c003"),
            ("It can improve informativeness but remains risky because it is unverifiable from the source.", "P006-p004-c003"),
        ],
        aspects=["limitations"],
    )
    add(
        "GEN-108",
        "Which downstream NLG tasks does the NLG survey cover?",
        "methodology", "easy", "P006",
        [("P006-p001-c002",
          "abstractive summarization, dialogue generation, generative question answering,\ndata-to-text generation, machine translation, and visual-language generation")],
        [
            ("Abstractive summarization and dialogue generation.", "P006-p001-c002"),
            ("Generative question answering and data-to-text generation.", "P006-p001-c002"),
            ("Machine translation and visual-language generation.", "P006-p001-c002"),
        ],
        aspects=["methods"],
    )
    add(
        "GEN-109",
        "What are the two broad categories of hallucination mitigation methods in the NLG survey?",
        "methodology", "intermediate", "P006",
        [("P006-p002-c002",
          "5.1 Data-Related Methods 12\n5.2 Modeling and Inference Methods 12")],
        [
            ("Data-related methods.", "P006-p002-c002"),
            ("Modeling and inference methods.", "P006-p002-c002"),
        ],
        aspects=["methods"],
    )

    # P007 - HaluEval
    add(
        "GEN-110",
        "What is HaluEval and how many samples does it contain?",
        "definitions", "easy", "P007",
        [("P007-p001-c005",
          "a large collection\nof 35,000 hallucinated/normal samples for LLMs\nanalysis and evaluation. HaluEval includes 5,000\n_general_ user queries with ChatGPT responses and\n30,000 _task-specific_ examples from three tasks")],
        [
            ("HaluEval contains 35,000 hallucinated or normal samples for evaluating LLMs.", "P007-p001-c005"),
            ("It includes 5,000 general user queries and 30,000 task-specific examples.", "P007-p001-c005"),
        ],
    )
    add(
        "GEN-111",
        "Which three tasks does HaluEval cover?",
        "single_paper_factual", "easy", "P007",
        [("P007-p001-c005",
          "question answering, knowledge-grounded dialogue,\nand text summarization")],
        [
            ("Question answering.", "P007-p001-c005"),
            ("Knowledge-grounded dialogue.", "P007-p001-c005"),
            ("Text summarization.", "P007-p001-c005"),
        ],
    )
    add(
        "GEN-112",
        "What automatic framework does HaluEval use to generate hallucinated samples?",
        "methodology", "intermediate", "P007",
        [("P007-p001-c002", "propose a two-stage framework")],
        [
            ("HaluEval uses a sampling-then-filtering framework.", "P007-p001-c002"),
            ("The framework generates candidate hallucinations and filters for plausible, difficult examples.", "P007-p001-c002"),
        ],
        aspects=["methods"],
    )
    add(
        "GEN-113",
        "What did HaluEval find about LLMs' ability to recognize hallucinations, and what helps them?",
        "findings", "intermediate", "P007",
        [("P007-p001-c002",
          "existing LLMs face great\nchallenges in recognizing the hallucinations in\ntexts. However, our experiments also prove\nthat providing external knowledge or adding\nreasoning steps can help LLMs recognize hallucinations.")],
        [
            ("Existing LLMs struggle to recognize hallucinations.", "P007-p001-c002"),
            ("External knowledge or added reasoning steps help LLMs recognize hallucinations.", "P007-p001-c002"),
        ],
        aspects=["findings"],
    )

    # P008 - Chain-of-Verification
    add(
        "GEN-114",
        "What are the four steps of Chain-of-Verification?",
        "methodology", "easy", "P008",
        [("P008-p003-c003", "performs four core steps")],
        [
            ("Generate a baseline response.", "P008-p003-c003"),
            ("Plan verification questions.", "P008-p003-c003"),
            ("Execute the verifications.", "P008-p003-c003"),
            ("Generate a final verified response.", "P008-p003-c003"),
        ],
        aspects=["methods"],
    )
    add(
        "GEN-115",
        "How does CoVe plan verification questions?",
        "methodology", "intermediate", "P008",
        [("P008-p004-c001",
          "a series of verification questions that test the factual claims in the original baseline response")],
        [
            ("Planning is conditioned on the original query and the baseline response.", "P008-p004-c001"),
            ("The questions test factual claims and are not templated.", "P008-p004-c001"),
        ],
        aspects=["methods"],
    )
    add(
        "GEN-116",
        "How do joint and 2-step CoVe verification execution differ?",
        "methodology", "difficult", "P008",
        [("P008-p004-c003", "separate the planning and execution into separate steps")],
        [
            ("Joint execution uses a single prompt for planning and execution.", "P008-p004-c003"),
            ("2-step execution separates planning from execution so answers do not condition on the baseline response.", "P008-p004-c003"),
        ],
        aspects=["methods"],
    )
    add(
        "GEN-117",
        "What factual-precision score improvement did factor+revise CoVe achieve on longform generation?",
        "quantitative", "intermediate", "P008",
        [("P008-p008-c002", "63.7 (factored) _→_ 71.4 (factor+revise)")],
        [
            ("Factored CoVe reached 63.7 FActScore.", "P008-p008-c002"),
            ("Factor+revise CoVe improved the score to 71.4.", "P008-p008-c002"),
        ],
        aspects=["findings"],
    )

    if len({case["question_id"] for case in cases}) != len(cases):
        raise ValueError("duplicate question IDs")
    V2.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    print(f"Created {V2} with {len(cases)} cases ({len(cases) - 105} new).")


if __name__ == "__main__":
    build()
