import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "pages.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "inspection"


def main():
    if not INPUT_FILE.exists():
        raise SystemExit("pages.jsonl is missing. Run extraction first.")

    papers = defaultdict(list)

    # Group extracted pages by paper.
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            papers[record["paper_id"]].append(record)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_pages = 0
    total_warnings = 0

    for paper_id, pages in sorted(papers.items()):
        pages.sort(key=lambda page: page["pdf_page"])

        page_numbers = [page["pdf_page"] for page in pages]

        # Each PDF page should appear exactly once, numbered from 1.
        if page_numbers != list(range(1, len(pages) + 1)):
            raise SystemExit(
                f"{paper_id}: missing, duplicate, or unexpected page numbers."
            )

        output_file = OUTPUT_DIR / f"{paper_id}_extracted.txt"
        short_pages = []

        with output_file.open("w", encoding="utf-8") as file:
            for page in pages:
                text = page["text"]

                file.write(
                    f"\n{'=' * 60}\n"
                    f"{paper_id} | PDF PAGE {page['pdf_page']}\n"
                    f"{'=' * 60}\n\n"
                )
                file.write(text)
                file.write("\n")

                if len(text.strip()) < 100:
                    short_pages.append(page["pdf_page"])

        total_pages += len(pages)
        total_warnings += len(short_pages)

        print(f"{paper_id}: {len(pages)} pages")
        print(f"  Readable copy: {output_file.name}")

        if short_pages:
            print(f"  Inspect short/empty pages: {short_pages}")

    print(f"\nPapers: {len(papers)}")
    print(f"Pages: {total_pages}")
    print(f"Short/empty page warnings: {total_warnings}")
    print(f"Inspection files: {OUTPUT_DIR}")
    print("\nManual comparison with the PDFs is still required.")


if __name__ == "__main__":
    main()