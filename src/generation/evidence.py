"""Adapt Phase 2 results without changing its ranking or citation metadata."""
from dataclasses import dataclass

from .papers import Interpretation, Paper
from .schemas import Evidence


@dataclass
class EvidenceSelection:
    passages: list[Evidence]
    gaps: list[str]


def _evidence(row: dict, catalog: dict[str, Paper]) -> Evidence | None:
    if row.get("needs_review") or row.get("review_flags"):
        return None
    paper = catalog.get(row.get("paper_id"))
    if paper is None or row.get("pdf_filename") != paper.pdf_filename:
        raise ValueError("retrieved source does not match the paper catalog")
    fields = {name: row[name] for name in Evidence.model_fields if name in row}
    return Evidence(**{**fields, "source_id": "", "title": paper.title})


def select_evidence(retriever, question: str, interpretation: Interpretation,
                    catalog: dict[str, Paper], context_chars: int) -> EvidenceSelection:
    groups: dict[str, list[Evidence]] = {}
    gaps = []
    seen_ids: dict[str, Evidence] = {}

    def retrieve(query, scope):
        rows = retriever.search(question=query, top_k=8, mode="hybrid", rerank=False,
                                paper_ids=scope, exclude_flagged=True)
        output = []
        for row in rows:
            item = _evidence(row, catalog)
            if item is None:
                continue
            if scope and item.paper_id not in scope:
                raise ValueError("retriever returned evidence outside the requested paper scope")
            if not item.text.strip():
                continue
            if item.chunk_id in seen_ids and seen_ids[item.chunk_id] != item:
                # Scores may vary with aspect query; source identity/text must not.
                old = seen_ids[item.chunk_id]
                if any(getattr(old, k) != getattr(item, k) for k in
                       ("paper_id", "pdf_filename", "pdf_page", "text")):
                    raise ValueError("conflicting records for one chunk ID")
            seen_ids[item.chunk_id] = item
            output.append(item)
        return output

    if interpretation.answer_type == "comparison":
        for paper_id in interpretation.paper_ids:
            pool = []
            for aspect in interpretation.aspects:
                query = f"{question}\n{catalog[paper_id].aliases[0]}: {aspect}"
                candidates = retrieve(query, [paper_id])
                unique = _unique(candidates)[:2]
                if not unique:
                    gaps.append(f"No usable retrieved evidence for {paper_id}: {aspect}.")
                pool.extend(unique)
            groups[paper_id] = _unique(pool)[:6]
    else:
        groups["qa"] = _unique(retrieve(question, interpretation.paper_ids or None))[:6]

    # Round-robin whole passages, so a context cap cannot consume one paper's
    # entire allocation before considering the other paper.
    selected = []
    used = 0
    for position in range(max((len(pool) for pool in groups.values()), default=0)):
        for pool in groups.values():
            if position >= len(pool):
                continue
            item = pool[position]
            if used + len(item.text) > context_chars:
                gaps.append(f"Context budget excluded chunk {item.chunk_id}.")
                continue
            selected.append(item.model_copy(update={"source_id": f"S{len(selected) + 1}"}))
            used += len(item.text)
    if interpretation.answer_type == "comparison":
        for paper_id in interpretation.paper_ids:
            if not any(p.paper_id == paper_id for p in selected):
                gaps.append(f"No selected evidence for paper {paper_id}; do not compare unsupported findings.")
    return EvidenceSelection(selected, list(dict.fromkeys(gaps)))


def _unique(passages: list[Evidence]) -> list[Evidence]:
    ids, texts, output = set(), set(), []
    for item in passages:
        # Preserve independently attributable identical statements across papers.
        text_key = (item.paper_id, item.text)
        if item.chunk_id not in ids and text_key not in texts:
            output.append(item)
            ids.add(item.chunk_id)
            texts.add(text_key)
    return output
