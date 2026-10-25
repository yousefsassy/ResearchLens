import json
from pathlib import Path

import pymupdf4llm


# Find the project folder from this script's location.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "pages.jsonl"


def extract_paper(pdf_path):
    """Extract one PDF into records containing text and source information."""

    # Example: P002_selfcheckgpt.pdf -> P002
    paper_id = pdf_path.stem.split("_")[0]

    print(f"Extracting {pdf_path.name}...", flush=True)

    # Return one text record per PDF page.
    # Our initial collection contains text-based PDFs, so OCR is disabled.
    pages = pymupdf4llm.to_markdown(
        str(pdf_path),
        page_chunks=True,
        use_ocr=False,
    )

    records = []

    for page_number, page in enumerate(pages, start=1):
        text = page["text"].strip()

        record = {
            "paper_id": paper_id,
            "pdf_filename": pdf_path.name,
            "pdf_page": page_number,
            "text": text,
        }

        records.append(record)

        # Short text is a warning to inspect, not necessarily an error.
        if len(text) < 100:
            print(
                f"  Check page {page_number}: "
                f"only {len(text)} characters extracted."
            )

    print(f"  Extracted {len(records)} pages.")

    return records


def main():
    pdf_files = sorted(
        path
        for path in RAW_DIR.glob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        raise SystemExit(
            f"No PDFs found. Put your research papers in:\n{RAW_DIR}"
        )

    # Paper IDs must be unique so citations cannot become ambiguous.
    paper_ids = [path.stem.split("_")[0] for path in pdf_files]

    if len(paper_ids) != len(set(paper_ids)):
        raise SystemExit(
            "Duplicate paper IDs found. Use a different P001/P002/etc. "
            "prefix for each PDF."
        )

    all_records = []

    for pdf_path in pdf_files:
        try:
            records = extract_paper(pdf_path)
        except Exception as error:
            raise SystemExit(
                f"Extraction failed for {pdf_path.name}: {error}\n"
                "The existing pages.jsonl file has not been changed."
            ) from error

        all_records.extend(records)

    # Save only after every PDF has been extracted successfully.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = OUTPUT_FILE.with_suffix(".jsonl.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    temporary_file.replace(OUTPUT_FILE)

    print("\nExtraction complete!")
    print(f"Papers: {len(pdf_files)}")
    print(f"Pages: {len(all_records)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()