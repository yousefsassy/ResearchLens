"""Strict corpus loading and shared ranking/filter helpers."""
import copy
import hashlib
import json
from pathlib import Path
from typing import Iterable


def load_chunks(path: Path) -> list[dict]:
    """Preserve JSONL order and every field; fail with a line number on bad input."""
    records, seen = [], set()
    with Path(path).open(encoding="utf-8-sig") as source:
        for number, line in enumerate(source, 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
                for key in ("chunk_id", "paper_id", "pdf_filename", "text"):
                    if not isinstance(record.get(key), str) or not record[key].strip():
                        raise ValueError(f"{key} must be a nonempty string")
                if type(record.get("pdf_page")) is not int or record["pdf_page"] < 1:
                    raise ValueError("pdf_page must be a positive integer")
                if type(record.get("needs_review")) is not bool:
                    raise ValueError("needs_review must be boolean")
                flags = record.get("review_flags")
                if not isinstance(flags, list) or any(not isinstance(x, str) for x in flags):
                    raise ValueError("review_flags must be a list of strings")
                if record["chunk_id"] in seen:
                    raise ValueError(f"duplicate chunk_id: {record['chunk_id']}")
                json.dumps(record, allow_nan=False)
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path}: line {number}: {error}") from error
            seen.add(record["chunk_id"])
            records.append(record)
    if not records:
        raise ValueError(f"{path}: corpus is empty")
    return records


def corpus_fingerprint(chunks: list[dict]) -> str:
    payload = json.dumps(chunks, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_query(question: str, top_k: int) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a nonempty string")
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    return question.strip()


def validate_metadata_filters(year: int | None, author: str | None,
                              section: str | None) -> None:
    """Reject malformed filters before a backend can silently ignore them."""
    if year is not None and (type(year) is not int or year < 1):
        raise ValueError("year must be a positive integer")

    for name, value in (("author", author), ("section", section)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be a nonempty string")


def candidate_indices(chunks: list[dict], paper_ids: Iterable[str] | None,
                      exclude_flagged: bool, year: int | None = None,
                      author: str | None = None,
                      section: str | None = None) -> list[int]:
    if isinstance(paper_ids, str):
        raise ValueError("paper_ids must be a collection of IDs, not one string")

    validate_metadata_filters(year, author, section)
    allowed = None if paper_ids is None else set(paper_ids)
    author_query = author.casefold() if author is not None else None
    section_query = section.casefold() if section is not None else None
    indices = []

    for i, chunk in enumerate(chunks):
        if allowed is not None and chunk["paper_id"] not in allowed:
            continue
        if exclude_flagged and (chunk["needs_review"] or chunk["review_flags"]):
            continue
        if year is not None and chunk.get("year") != year:
            continue
        if author_query is not None and author_query not in str(
                chunk.get("authors", "")).casefold():
            continue
        if section_query is not None and section_query not in str(
                chunk.get("section", "")).casefold():
            continue
        indices.append(i)

    return indices


def make_result(chunk: dict, score: float, kind: str) -> dict:
    return {**copy.deepcopy(chunk), "retrieval_score": float(score),
            "rerank_score": None, f"{kind}_score": float(score)}


def rank_results(results: list[dict], score_key: str, top_k: int) -> list[dict]:
    ordered = sorted(results, key=lambda row: (-row[score_key], row["chunk_id"]))[:top_k]
    return [{**row, "rank": rank} for rank, row in enumerate(ordered, 1)]
