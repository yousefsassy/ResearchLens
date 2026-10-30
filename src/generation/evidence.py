"""Paper-agnostic, coverage-aware selection of attributable retrieval evidence."""
from dataclasses import dataclass
import re

from .evidence_quality import near_duplicate, quality, supports_aspect
from .papers import Interpretation, Paper
from .schemas import Evidence
from src.profiling import timed, measure


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


def _unique(passages: list[Evidence]) -> list[Evidence]:
    seen_ids, seen_text, result = set(), set(), []
    for item in passages:
        key = (item.paper_id, " ".join(item.text.split()))
        if item.chunk_id not in seen_ids and key not in seen_text:
            result.append(item)
            seen_ids.add(item.chunk_id)
            seen_text.add(key)
    return result


def _ranked_pool(results: list[list[Evidence]], aspect=None) -> list[Evidence]:
    """Retain hybrid relevance, with bounded quality and aspect adjustments.

    Scores are normalized only within a query; raw BM25 and vector scales are
    never mixed. Rank remains available for injected retrievers without scores.
    """
    by_id, scores = {}, {}
    for query_index, rows in enumerate(results):
        weight = 1.0 if query_index == 0 else 0.65
        maximum = max((r.retrieval_score or 0.0 for r in rows), default=0.0)
        for rank, item in enumerate(rows):
            by_id.setdefault(item.chunk_id, item)
            relative = max(0.0, item.retrieval_score or 0.0) / maximum if maximum > 0 else 0.0
            relevance = 0.7 / (rank + 2) + 0.15 * relative
            scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + weight * relevance

    def score(item):
        informative = quality(item.text)
        return (scores[item.chunk_id] * (0.25 + 0.75 * informative)
                + (0.15 * informative if aspect and supports_aspect(item.text, aspect) else 0.0))

    return sorted(by_id.values(), key=lambda item: (-score(item), item.chunk_id))


def _aspect_query(name, aspect):
    prompts = {
        "methods": f"How does {name} work? Explain its proposed method, procedure and approach.",
        "limitations": f"What are the limitations, weaknesses, assumptions and applicability constraints of {name}?",
        "findings": f"What are the main findings, experimental results and measured performance of {name}?",
    }
    return prompts.get(aspect, f"{name}: {aspect}")


@timed("evidence_selection_including_search")
def select_evidence(retriever, question: str, interpretation: Interpretation,
                    catalog: dict[str, Paper], context_chars: int) -> EvidenceSelection:
    if context_chars <= 0:
        raise ValueError("context_chars must be positive")
    seen, cache = {}, {}
    gaps = []

    def retrieve(query, scope):
        # Cache only within this question, including failed requests. Keep scope
        # in the key so one paper's results cannot leak into another's evidence.
        key = (query.strip(), tuple(scope) if scope is not None else None)
        if key in cache:
            return cache[key]
        try:
            with measure("aspect_search_including_initialization"):
                rows = retriever.search(question=query, top_k=8, mode="hybrid", rerank=False,
                                        paper_ids=scope, exclude_flagged=True)
        except (OSError, RuntimeError, ImportError):
            cache[key] = ([], True)
            return cache[key]
        output = []
        for row in rows:
            item = _evidence(row, catalog)
            if item is None or not item.text.strip():
                continue
            if scope and item.paper_id not in scope:
                raise ValueError("retriever returned evidence outside the requested paper scope")
            previous = seen.get(item.chunk_id)
            if previous and any(getattr(previous, field) != getattr(item, field)
                                for field in ("paper_id", "pdf_filename", "pdf_page", "text")):
                raise ValueError("conflicting records for one chunk ID")
            seen[item.chunk_id] = item
            output.append(item)
        cache[key] = (_unique(output), False)
        return cache[key]

    selected, used = [], 0

    def add(item, limit):
        nonlocal used
        if used + len(item.text) > limit or quality(item.text) < 0.15:
            return False
        if any(near_duplicate(item, previous)
               and all(not supports_aspect(item.text, aspect) or supports_aspect(previous.text, aspect)
                       for aspect in interpretation.aspects)
               for previous in selected):
            return False
        selected.append(item)
        used += len(item.text)
        return True

    if interpretation.answer_type != "comparison":
        candidates, failed = retrieve(question, interpretation.paper_ids or None)
        aspect = interpretation.aspects[0] if len(interpretation.aspects) == 1 else None
        ranked = _ranked_pool([candidates], aspect)
        # PDF chunk boundaries can leave a numeric value detached from its label.
        # Recover only the immediately preceding same-page chunk, using the local
        # corpus when available; injected search-only retrievers remain supported.
        preceding = {}
        for item in ranked:
            if re.match(r"^[*_\s]*\d+(?:\.\d+)?[*_\s]*\)", item.text):
                match = re.fullmatch(r"(.+-p\d+-c)(\d+)", item.chunk_id)
                if match and int(match[2]) > 1:
                    key = match[1] + str(int(match[2]) - 1).zfill(len(match[2]))
                    preceding[key] = item
        neighbors = {}
        if preceding:
            for row in getattr(retriever, "chunks", []):
                anchor = preceding.get(row.get("chunk_id"))
                if anchor and row.get("paper_id") == anchor.paper_id and row.get("pdf_page") == anchor.pdf_page:
                    neighbor = _evidence(row, catalog)
                    if neighbor is not None and neighbor.text.strip():
                        neighbors[anchor.chunk_id] = neighbor
        expanded = []
        for item in ranked:
            if item.chunk_id in neighbors:
                expanded.append(neighbors[item.chunk_id])
            expanded.append(item)
        for item in _unique(expanded):
            if len(selected) >= 6:
                break
            add(item, context_chars)
        if failed:
            gaps.append("Evidence could not be assessed because retrieval failed.")
        elif not selected:
            gaps.append("No adequate usable evidence fits the context budget.")
    else:
        paper_ids = interpretation.paper_ids
        aspects = list(dict.fromkeys(interpretation.aspects))
        buckets, failures = {}, {}
        for paper_id in paper_ids:
            paper = catalog[paper_id]
            name = paper.aliases[0] if paper.aliases else paper.title
            original, original_failed = retrieve(question, [paper_id])
            for aspect in aspects:
                targeted, failed = retrieve(_aspect_query(name, aspect), [paper_id])
                key = (paper_id, aspect)
                failures[key] = failed or original_failed
                buckets[key] = [item for item in _ranked_pool([targeted, original], aspect)
                                if supports_aspect(item.text, aspect)]
            buckets[(paper_id, "_general")] = [
                item for item in _ranked_pool([original])
                if quality(item.text) >= 0.35
                and (not aspects or any(supports_aspect(item.text, aspect) for aspect in aspects))
            ]

        cells = [(paper_id, aspect) for aspect in aspects for paper_id in paper_ids]

        def covered(cell):
            paper_id, aspect = cell
            return any(item.paper_id == paper_id and supports_aspect(item.text, aspect)
                       for item in selected)

        def add_from(cell, limit):
            paper_id, _ = cell
            if sum(item.paper_id == paper_id for item in selected) >= 6:
                return False
            return any(add(item, limit) for item in buckets[cell])

        # Reserve a fair share for remaining uncovered cells. Prefer the best
        # passage that fits, then revisit deferred cells with unused capacity.
        for cell in cells:
            if covered(cell):
                continue
            pending = sum(not covered(other) and bool(buckets[other]) for other in cells)
            if pending:
                add_from(cell, used + (context_chars - used) // pending)
        for cell in cells:
            if not covered(cell):
                add_from(cell, context_chars)

        # Only after coverage gets first choice may extra passages use the budget.
        ordered = cells + [(paper_id, "_general") for paper_id in paper_ids]
        while True:
            changed = False
            for cell in ordered:
                changed = add_from(cell, context_chars) or changed
            if not changed:
                break

        for paper_id in paper_ids:
            if not any(item.paper_id == paper_id for item in selected):
                gaps.append(f"No selected evidence for paper {paper_id}; do not compare unsupported findings.")
            for aspect in aspects:
                cell = (paper_id, aspect)
                if covered(cell):
                    continue
                if failures[cell]:
                    gaps.append(f"Could not assess evidence for {paper_id}: {aspect}; retrieval failed.")
                elif buckets[cell]:
                    gaps.append(f"Adequate candidate evidence for {paper_id}: {aspect} was not selected within the evidence budget.")
                else:
                    gaps.append(f"No adequate supporting evidence retrieved for {paper_id}: {aspect}.")

    return EvidenceSelection(
        passages=[item.model_copy(update={"source_id": f"S{i}"})
                  for i, item in enumerate(selected, 1)],
        gaps=list(dict.fromkeys(gaps)),
    )
