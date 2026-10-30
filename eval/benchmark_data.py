"""Versioned benchmark contracts and corpus-reference integrity checks."""
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from eval.generation_eval import EvalCase
from src.generation.schemas import StrictModel

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "eval/benchmark.v1.jsonl"
DEFAULT_CORPUS = ROOT / "data/processed/chunks.jsonl"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


class Point(StrictModel):
    point_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    reference_chunk_ids: list[str]


class Reference(StrictModel):
    chunk_id: str
    paper_id: str
    pdf_filename: str
    pdf_page: int = Field(ge=1)
    quote: str = Field(min_length=1)


class BenchmarkCase(EvalCase):
    difficulty: Literal["easy", "intermediate", "difficult"]
    expected_answerability: Literal["answerable", "partial", "unanswerable", "clarification"]
    acceptable_statuses: list[Literal["complete", "partial", "abstained", "needs_clarification"]] = Field(min_length=1)
    important_points: list[Point]
    required_aspects: list[Literal["methods", "findings", "limitations"]]
    reference_sources: list[Reference]

    @model_validator(mode="after")
    def check_references(self):
        ids = {r.chunk_id for r in self.reference_sources}
        if len(ids) != len(self.reference_sources):
            raise ValueError("duplicate reference")
        if len({p.point_id for p in self.important_points}) != len(self.important_points):
            raise ValueError("duplicate point ID")
        if any(not set(point.reference_chunk_ids) <= ids for point in self.important_points):
            raise ValueError("unknown point reference")
        if self.expected_answerability in {"answerable", "partial"} and (not ids or not self.important_points):
            raise ValueError("answerable cases require references and points")
        if self.expected_status not in self.acceptable_statuses:
            raise ValueError("expected status must be acceptable")
        mapping = {"complete": "answerable", "partial": "partial", "abstained": "unanswerable", "needs_clarification": "clarification"}
        if mapping[self.expected_status] != self.expected_answerability:
            raise ValueError("status and answerability disagree")
        return self


def load_benchmark(path=DEFAULT_DATASET, corpus_path=DEFAULT_CORPUS):
    cases = [BenchmarkCase.model_validate_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases or len({c.question_id for c in cases}) != len(cases):
        raise ValueError("benchmark IDs must be unique")
    if len({" ".join(c.question.lower().split()) for c in cases}) != len(cases):
        raise ValueError("benchmark questions must be unique")
    corpus = {row["chunk_id"]: row for row in map(json.loads, Path(corpus_path).read_text(encoding="utf-8").splitlines())}
    for case in cases:
        for ref in case.reference_sources:
            source = corpus.get(ref.chunk_id)
            if source is None or any(getattr(ref, key) != source[key] for key in ("paper_id", "pdf_page", "pdf_filename")):
                raise ValueError(f"invalid reference location in {case.question_id}")
            if ref.quote not in source["text"]:
                raise ValueError(f"reference quote changed in {case.question_id}")
    return cases
