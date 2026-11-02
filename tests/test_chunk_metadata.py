import csv
import json

import pytest

from src.ingestion.chunk import (TARGET_CHARS, chunk_page,
                                 chunk_page_with_sections, detect_section)
from src.ingestion.metadata import load_paper_metadata


def test_manifest_has_one_complete_record_per_paper():
    papers = load_paper_metadata()

    assert set(papers) == {"P001", "P002", "P003", "P004", "P005"}
    assert papers["P002"]["year"] == 2023
    assert "Manakul" in papers["P002"]["authors"]
    assert papers["P003"]["pdf_filename"] == "P003_factscore.pdf"
    assert all(paper["source_url"].startswith("https://") for paper in papers.values())


def test_manifest_rejects_duplicate_or_missing_fields(tmp_path):
    path = tmp_path / "manifest.csv"
    columns = ["paper_id", "title", "authors", "year", "category", "source_url",
               "pdf_filename", "version", "license", "page_count"]
    rows = [
        dict(paper_id="P001", title="A", authors="A", year="2024", category="c",
             source_url="https://example.test", pdf_filename="a.pdf", version="v",
             license="l", page_count="1"),
        dict(paper_id="P001", title="B", authors="B", year="2024", category="c",
             source_url="https://example.test", pdf_filename="b.pdf", version="v",
             license="l", page_count="1"),
    ]

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="duplicate"):
        load_paper_metadata(path)

    rows[0]["year"] = "not-a-year"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows[:1])

    with pytest.raises(ValueError, match="year"):
        load_paper_metadata(path)


@pytest.mark.parametrize("text,expected", [
    ("**5.1** **SelfCheckGPT with BERTScore**\n\nBody", "5.1 SelfCheckGPT with BERTScore"),
    ("**Limitations**\n\nScope", "Limitations"),
    ("1 Introduction", "1 Introduction"),
    ("4.1 GPT-4 Evaluation", "4.1 GPT-4 Evaluation"),
    ("This is an ordinary sentence. It has a period.", None),
    ("78.84 80.00", None),
    ("4 Gopher is a 280-billion parameter model", None),
    ("200 samples (10 per category)", None),
    ("2023 MQAG: Multiple-choice question answering", None),
    ("Results show a large improvement.", None),
])
def test_detect_section(text, expected):
    assert detect_section(text) == expected


def legacy_chunk_page(text):
    """Frozen copy of the pre-metadata boundary algorithm for parity."""
    import re

    def split_long(value, max_chars):
        if len(value) <= max_chars:
            return [value]
        pieces, current = [], ""
        for sentence in re.split(r"(?<=[.!?])\s+", value):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > max_chars:
                if current:
                    pieces.append(current.strip())
                    current = ""
                for start in range(0, len(sentence), max_chars):
                    pieces.append(sentence[start:start + max_chars].strip())
                continue
            candidate = sentence if not current else current + " " + sentence
            if len(candidate) <= max_chars:
                current = candidate
            else:
                pieces.append(current.strip())
                current = sentence
        if current:
            pieces.append(current.strip())
        return pieces

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units = []
    for paragraph in paragraphs:
        units.extend(split_long(paragraph, TARGET_CHARS))

    chunks, current = [], ""
    for unit in units:
        candidate = unit if not current else current + "\n\n" + unit
        if len(candidate) <= TARGET_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
            if len(current) <= 200:
                overlap = current
            else:
                tail = current[-200:]
                first_space = tail.find(" ")
                overlap = tail[first_space + 1:].strip() if first_space != -1 else tail.strip()
            candidate = overlap + "\n\n" + unit if overlap else unit
            current = candidate if len(candidate) <= TARGET_CHARS else unit
        else:
            current = unit
    if current:
        chunks.append(current.strip())
    return chunks


def test_chunk_main_attaches_manifest_metadata(tmp_path, monkeypatch):
    from src.ingestion import chunk

    manifest = tmp_path / "papers_manifest.csv"
    columns = ["paper_id", "title", "authors", "year", "category", "source_url",
               "pdf_filename", "version", "license", "page_count"]
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerow(dict(paper_id="P001", title="A Paper", authors="A. Author",
                             year="2024", category="test",
                             source_url="https://example.test", pdf_filename="p1.pdf",
                             version="v1", license="test", page_count="1"))

    pages = tmp_path / "clean_pages.jsonl"
    pages.write_text(json.dumps({
        "paper_id": "P001", "pdf_filename": "p1.pdf", "pdf_page": 1,
        "text": ("Front matter.\n\n**1 Introduction**\n\n"
                 + "A long body sentence for chunking. " * 80),
        "needs_review": False, "review_flags": [],
    }) + "\n", encoding="utf-8")
    output = tmp_path / "chunks.jsonl"

    monkeypatch.setattr(chunk, "INPUT_FILE", pages)
    monkeypatch.setattr(chunk, "OUTPUT_FILE", output)
    monkeypatch.setattr(chunk, "DEFAULT_MANIFEST", manifest)
    chunk.main()

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows
    assert all(row["title"] == "A Paper" for row in rows)
    assert all(row["authors"] == "A. Author" and row["year"] == 2024 for row in rows)
    assert all(row["source_url"] == "https://example.test" for row in rows)
    assert any(row["section"] == "1 Introduction" for row in rows)


def test_section_metadata_does_not_change_chunk_boundaries():
    text = ("Front matter paragraph.\n\n**1 Introduction**\n\n"
            + "A sentence with enough words to build a chunk. " * 120
            + "\n\n**2 Methods**\n\nMethod details. " * 30
            + "\n\n**3 Results**\n\nResult details.")
    assert chunk_page(text) == legacy_chunk_page(text)
    sections = [section for _, section in chunk_page_with_sections(text)]
    assert sections[0] == "Front Matter"
    assert "1 Introduction" in sections
    assert all(isinstance(section, str) and section for section in sections)
