
"""Reference and quote integrity checks; not a semantic verifier."""

import re

from .schemas import Citation, Evidence, ModelAnswer


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def validate_and_render(
    output: ModelAnswer,
    evidence: list[Evidence],
    answer_type: str,
    paper_ids: list[str],
) -> tuple[str, list[Citation]]:

    sources = {p.source_id: p for p in evidence}
    citations = []
    lines = []

    for claim_index, claim in enumerate(output.claims, 1):
        if not claim.text.strip() or re.search(
            r"\[\s*S\d+\s*\]", claim.text
        ):
            raise ValueError(
                f"Claim {claim_index}: empty claim or model-written source marker"
            )

        supporting_papers = set()
        markers = []

        for reference in claim.citations:
            source = sources.get(reference.source_id)
            quote = normalize_whitespace(reference.quote)

            if source is None:
                raise ValueError(
                    f"Claim {claim_index}: unknown source ID "
                    f"{reference.source_id!r}"
                )

            if not quote:
                raise ValueError(
                    f"Claim {claim_index}, source {source.source_id}: "
                    "empty citation quote"
                )

            normalized_source = normalize_whitespace(source.text)

            if quote not in normalized_source:
                raise ValueError(
                    f"Claim {claim_index}, source {source.source_id}: "
                    f"quote not found in chunk {source.chunk_id} "
                    f"(paper {source.paper_id}, page {source.pdf_page}). "
                    f"Quote: {reference.quote!r}"
                )

            supporting_papers.add(source.paper_id)

            citation_id = f"C{len(citations) + 1}"

            citations.append(
                Citation(
                    citation_id=citation_id,
                    claim_index=claim_index,
                    source_id=source.source_id,
                    quote=reference.quote,
                    chunk_id=source.chunk_id,
                    paper_id=source.paper_id,
                    pdf_filename=source.pdf_filename,
                    title=source.title,
                    pdf_page=source.pdf_page,
                )
            )

            markers.append(f"[{citation_id}]")

        if (
            answer_type == "comparison"
            and claim.kind == "synthesis"
            and not set(paper_ids) <= supporting_papers
        ):
            missing = set(paper_ids) - supporting_papers

            raise ValueError(
                f"Claim {claim_index}: comparison synthesis is missing "
                f"citations from papers {sorted(missing)}"
            )

        prefix = "Synthesis: " if claim.kind == "synthesis" else ""

        lines.append(
            f"{prefix}{claim.text.strip()} {' '.join(markers)}".strip()
        )

    if output.status == "abstained":
        return (
            "I don't have sufficient usable evidence to answer this question.",
            [],
        )

    return "\n\n".join(lines), citations
