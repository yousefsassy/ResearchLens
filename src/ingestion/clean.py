import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "pages.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "clean_pages.jsonl"
REPORT_FILE = OUTPUT_DIR / "cleaning_report.json"


# Problems confirmed by comparing P002 against the original PDF.
# These apply to the specific PDF version we inspected.
KNOWN_ISSUES = {
    ("P002", 1): ["figure_and_footnote_interrupt_prose"],
    ("P002", 3): ["damaged_equations"],
    ("P002", 9): ["table_4_merged_model_columns"],
    ("P002", 12): ["incorrect_column_reading_order"],
    ("P002", 13): ["table_5_damaged_headers"],
}


def clean_text(text):
    """Apply conservative formatting changes without rewriting content."""

    changes = []

    # Normalize line endings and common invisible spacing characters.
    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
    )

    # Remove trailing whitespace without flattening paragraphs or tables.
    normalized = "\n".join(
        line.rstrip() for line in normalized.split("\n")
    )

    # Keep paragraph breaks, but collapse excessive empty lines.
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()

    if normalized != text:
        changes.append("normalized_whitespace")

    # Remove a numeric footer only from the very end of the page.
    # Require a blank line before it, and meaningful text before that.
    match = re.search(r"\n\n(\d{1,5})$", normalized)

    if match:
        preceding_text = normalized[:match.start()]

        # A heuristic, not a guarantee: log every removal for inspection.
        if len(preceding_text) > 200:
            changes.append(
                f"removed_possible_page_footer:{match.group(1)}"
            )
            normalized = preceding_text.rstrip()

    return normalized, changes


def remove_confirmed_artifacts(record, text):
    """Remove verified PDF headers and footers."""
    paper_id = record["paper_id"]
    page = record["pdf_page"]
    changes = []

    title = (
        "A Survey on Hallucination in Large Language Models: "
        "Principles, Taxonomy, Challenges, and Open Questions"
    )

    headers = {
        ("P001", 31): f"1:31\n\n{title}",
        ("P001", 50): "Huang, et al.\n\n1:50",
        ("P001", 53): f"1:53\n\n{title}",
    }

    header = headers.get((paper_id, page))

    if header and (
        text == header or text.startswith(header + "\n")
    ):
        text = text[len(header):].lstrip("\n").strip()
        changes.append("removed_verified_running_header")

    if (paper_id, page) == ("P003", 24):
        revised = re.sub(r"\n\s*12099\s*$", "", text).rstrip()

        if revised != text:
            text = revised
            changes.append("removed_verified_page_footer:12099")

    return text, changes


def find_review_flags(record, text):
    """Identify content that needs checking against the source PDF."""

    flags = []

    if len(text.strip()) < 100:
        flags.append("short_or_empty_page")

    if "\ufffd" in text:
        flags.append("replacement_character_detected")

    # Figure-text blocks can include diagrams, charts, or equations.
    # Preserve them for now; do not assume they are trustworthy prose.
    if "<!-- Start of picture text -->" in text:
        flags.append("picture_text_needs_review")

    # A Markdown table is not automatically damaged.
    # Flag it so its rows and column labels can be checked.
    if any(line.lstrip().startswith("|") for line in text.splitlines()):
        flags.append("table_needs_review")

    key = (record["paper_id"], record["pdf_page"])
    flags.extend(KNOWN_ISSUES.get(key, []))

    return sorted(set(flags))


def write_jsonl(path, records):
    """Replace an output file only after its contents are written."""

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    temporary_path.replace(path)


def main():
    if not INPUT_FILE.exists():
        raise SystemExit("pages.jsonl is missing. Run extraction first.")

    cleaned_records = []
    report_entries = []
    seen_pages = set()

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)

                paper_id = record["paper_id"]
                page_number = record["pdf_page"]
                original_text = record["text"]

                if not isinstance(paper_id, str):
                    raise ValueError("paper_id must be a string")

                if type(page_number) is not int or page_number < 1:
                    raise ValueError("pdf_page must be a positive integer")

                if not isinstance(original_text, str):
                    raise ValueError("text must be a string")

            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
                raise SystemExit(
                    f"Invalid record on line {line_number}: {error}"
                ) from error

            page_key = (paper_id, page_number)

            if page_key in seen_pages:
                raise SystemExit(f"Duplicate page record: {page_key}")

            seen_pages.add(page_key)

            cleaned_text, changes = clean_text(original_text)
            cleaned_text, artifact_changes = remove_confirmed_artifacts(
                record, cleaned_text
            )
            changes.extend(artifact_changes)
            flags = find_review_flags(record, cleaned_text)

            # Copy the original record to preserve its source metadata.
            cleaned_record = {
                **record,
                "text": cleaned_text,
                "cleaning_changes": changes,
                "review_flags": flags,
                "needs_review": bool(flags),
            }

            cleaned_records.append(cleaned_record)

            if changes or flags:
                report_entries.append({
                    "paper_id": paper_id,
                    "pdf_page": page_number,
                    "changes": changes,
                    "review_flags": flags,
                })

    if not cleaned_records:
        raise SystemExit("No page records found. No outputs were written.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT_FILE, cleaned_records)

    flagged_count = sum(
        record["needs_review"] for record in cleaned_records
    )

    report = {
        "total_pages": len(cleaned_records),
        "pages_needing_review": flagged_count,
        "note": (
            "Flags identify review candidates. No flag does not guarantee "
            "correct extraction. Original pages.jsonl remains unchanged."
        ),
        "entries": report_entries,
    }

    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Cleaning complete!")
    print(f"Pages processed: {len(cleaned_records)}")
    print(f"Pages needing review: {flagged_count}")
    print(f"Cleaned pages: {OUTPUT_FILE}")
    print(f"Review report: {REPORT_FILE}")


if __name__ == "__main__":
    main()