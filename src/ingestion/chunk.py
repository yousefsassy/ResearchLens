import json
import re
from pathlib import Path

from .metadata import DEFAULT_MANIFEST, load_paper_metadata


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "clean_pages.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"

TARGET_CHARS = 1500
OVERLAP_CHARS = 200
DEFAULT_SECTION = "Front Matter"

# Section headings are deliberately conservative. They are used as metadata
# for filtering, not as a claim that PDF extraction found every heading.
NAMED_SECTIONS = re.compile(
    r"^(Abstract|Introduction|Related Work|Background|Methods?|Methodology|"
    r"Approach|Experiments?|Experimental Setup|Evaluation|Results?|Discussion|"
    r"Limitations?|Conclusions?|References|Appendix(?:\s+[A-Z0-9.]+)?)\b",
    re.IGNORECASE,
)
NUMBERED_SECTION = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+([A-Za-z][^.]{1,80})$")


def split_paragraphs(text):
    """Split page text on paragraph boundaries while preserving content."""

    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


def split_long_text(text, max_chars):
    """
    Split text that is too large for one chunk.

    Prefer sentence boundaries. Fall back to character boundaries when
    a sentence itself is unusually long.
    """

    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)

    pieces = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        # If one sentence is longer than the maximum, split it directly.
        if len(sentence) > max_chars:
            if current:
                pieces.append(current.strip())
                current = ""

            start = 0

            while start < len(sentence):
                pieces.append(sentence[start:start + max_chars].strip())
                start += max_chars

            continue

        candidate = (
            sentence
            if not current
            else current + " " + sentence
        )

        if len(candidate) <= max_chars:
            current = candidate
        else:
            pieces.append(current.strip())
            current = sentence

    if current:
        pieces.append(current.strip())

    return pieces


def tail_overlap(text, max_chars):
    """
    Return the ending portion of a chunk for use as overlap.

    Prefer starting at a word boundary.
    """

    if len(text) <= max_chars:
        return text

    tail = text[-max_chars:]

    first_space = tail.find(" ")

    if first_space != -1:
        tail = tail[first_space + 1:]

    return tail.strip()


def detect_section(text):
    """Return a conservative section heading from the start of a text unit.

    PDF extraction often leaves Markdown markers around headings. The function
    removes those markers, accepts short numbered headings and common paper
    section names, and returns None for ordinary sentences.
    """
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]

    if not lines:
        return None

    first = re.sub(r"[*_#`]", "", lines[0]).strip()
    first = re.sub(r"\s+", " ", first)

    if not first or len(first) > 100:
        return None

    numbered = NUMBERED_SECTION.match(first)

    if numbered:
        title = numbered.group(2).strip()

        # A heading is short and does not end like a sentence. This avoids
        # treating a numbered list item or a number-heavy table row as a section.
        if len(title.split()) <= 12 and not title.endswith((".", "?", "!")):
            return f"{numbered.group(1)} {title}"

    named = NAMED_SECTIONS.match(first)

    if named:
        return named.group(1).strip().title()

    return None


def chunk_page_with_sections(text, start_section=DEFAULT_SECTION):
    """Create overlapping chunks and attach the section that contains each one.

    Chunk boundaries are identical to :func:`chunk_page`; sections are carried
    across pages by the caller so a paper that starts a page inside a section
    does not reset that section.
    """

    paragraphs = split_paragraphs(text)

    # Break unusually large paragraphs before building chunks.
    units = []

    for paragraph in paragraphs:
        units.extend(split_long_text(paragraph, TARGET_CHARS))

    chunks = []
    current = ""
    current_section = start_section or DEFAULT_SECTION
    chunk_section = current_section

    for unit in units:
        heading = detect_section(unit)

        if heading:
            current_section = heading

        candidate = (
            unit
            if not current
            else current + "\n\n" + unit
        )

        if len(candidate) <= TARGET_CHARS:
            if not current:
                chunk_section = current_section
            current = candidate
            continue

        if current:
            chunks.append((current.strip(), chunk_section))

            overlap = tail_overlap(current, OVERLAP_CHARS)

            candidate = (
                overlap + "\n\n" + unit
                if overlap
                else unit
            )

            # The overlap plus a large unit can exceed the target.
            if len(candidate) <= TARGET_CHARS:
                current = candidate
            else:
                current = unit

            chunk_section = current_section
        else:
            chunk_section = current_section
            current = unit

    if current:
        chunks.append((current.strip(), chunk_section))

    return chunks


def chunk_page(text):
    """Create overlapping chunks from one cleaned PDF page."""

    return [chunk_text for chunk_text, _ in chunk_page_with_sections(text)]


def write_jsonl(path, records):
    """Write output atomically."""

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    temporary_path.replace(path)


def main():
    if not INPUT_FILE.exists():
        raise SystemExit(
            "clean_pages.jsonl is missing. Run cleaning first."
        )

    try:
        papers = load_paper_metadata(DEFAULT_MANIFEST)
    except ValueError as error:
        raise SystemExit(f"Paper metadata error: {error}") from error

    output_records = []
    seen_chunk_ids = set()
    current_sections = {}

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                page = json.loads(line)

                paper_id = page["paper_id"]
                pdf_filename = page["pdf_filename"]
                pdf_page = page["pdf_page"]
                text = page["text"]

            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise SystemExit(
                    f"Invalid record on line {line_number}: {error}"
                ) from error

            if not isinstance(text, str):
                raise SystemExit(
                    f"Invalid text on line {line_number}: expected string."
                )

            if not text.strip():
                continue

            paper = papers.get(paper_id)

            if paper is None:
                raise SystemExit(
                    f"Paper {paper_id} is missing from {DEFAULT_MANIFEST}"
                )

            if paper["pdf_filename"] != pdf_filename:
                raise SystemExit(
                    f"Paper {paper_id} has pdf_filename {paper['pdf_filename']!r} "
                    f"in the manifest but {pdf_filename!r} in clean_pages.jsonl"
                )

            start_section = current_sections.get(paper_id, DEFAULT_SECTION)
            page_chunks = chunk_page_with_sections(text, start_section)

            # Carry the last heading seen on this page forward, even when a
            # chunk starts in one section and ends in another.
            page_section = start_section
            for paragraph in split_paragraphs(text):
                heading = detect_section(paragraph)
                if heading:
                    page_section = heading

            if page_chunks:
                current_sections[paper_id] = page_section

            for chunk_number, (chunk_text, section) in enumerate(
                page_chunks,
                start=1,
            ):
                chunk_id = (
                    f"{paper_id}-p{pdf_page:03d}-c{chunk_number:03d}"
                )

                if chunk_id in seen_chunk_ids:
                    raise SystemExit(
                        f"Duplicate chunk ID generated: {chunk_id}"
                    )

                seen_chunk_ids.add(chunk_id)

                record = {
                    "chunk_id": chunk_id,
                    "paper_id": paper_id,
                    "pdf_filename": pdf_filename,
                    "pdf_page": pdf_page,
                    "chunk_index": chunk_number,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "year": paper["year"],
                    "category": paper["category"],
                    "source_url": paper["source_url"],
                    "license": paper["license"],
                    "section": section,
                    "needs_review": page.get("needs_review", False),
                    "review_flags": page.get("review_flags", []),
                }

                output_records.append(record)

    if not output_records:
        raise SystemExit(
            "No chunks were generated. Output was not written."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    write_jsonl(OUTPUT_FILE, output_records)

    review_chunks = sum(
        record["needs_review"]
        for record in output_records
    )

    print("Chunking complete!")
    print(f"Chunks generated: {len(output_records)}")
    print(f"Chunks needing review: {review_chunks}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()