"""Paper-level metadata loading for traceable chunks and metadata filters."""
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "papers_manifest.csv"

REQUIRED_COLUMNS = (
    "paper_id",
    "title",
    "authors",
    "year",
    "category",
    "source_url",
    "pdf_filename",
    "version",
    "license",
    "page_count",
)


def load_paper_metadata(path: Path = DEFAULT_MANIFEST) -> dict[str, dict]:
    """Load and validate one metadata record per paper.

    The manifest is intentionally small and human-editable. Invalid rows fail
    before chunking so that citations cannot silently lose their provenance.
    """
    path = Path(path)

    if not path.exists():
        raise ValueError(f"paper manifest is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = tuple(reader.fieldnames or ())

        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise ValueError(
                f"paper manifest is missing columns: {', '.join(missing)}"
            )

        papers = {}

        for line_number, row in enumerate(reader, start=2):
            cleaned = {
                name: (row.get(name) or "").strip()
                for name in REQUIRED_COLUMNS
            }

            if not any(cleaned.values()):
                continue

            paper_id = cleaned["paper_id"]

            if not paper_id:
                raise ValueError(
                    f"paper manifest line {line_number}: paper_id is required"
                )

            if paper_id in papers:
                raise ValueError(
                    f"paper manifest line {line_number}: duplicate paper_id {paper_id}"
                )

            for name in ("title", "authors", "source_url", "pdf_filename",
                         "version", "license"):
                if not cleaned[name]:
                    raise ValueError(
                        f"paper manifest line {line_number}: {name} is required"
                    )

            for name in ("year", "page_count"):
                try:
                    value = int(cleaned[name])
                except ValueError as error:
                    raise ValueError(
                        f"paper manifest line {line_number}: {name} must be an integer"
                    ) from error

                if value < 1:
                    raise ValueError(
                        f"paper manifest line {line_number}: {name} must be positive"
                    )

                cleaned[name] = value

            papers[paper_id] = cleaned

    if not papers:
        raise ValueError("paper manifest is empty")

    return papers
