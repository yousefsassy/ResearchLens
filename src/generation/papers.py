"""Small deterministic paper resolver, without LLM-based bibliographic guesses."""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, TypeAdapter

from .schemas import Clarification, StrictModel


class Paper(StrictModel):
    paper_id: str
    pdf_filename: str
    title: str
    aliases: list[str] = Field(min_length=1)


@dataclass
class Interpretation:
    answer_type: Literal["qa", "comparison"]
    paper_ids: list[str]
    aspects: list[str]
    clarification: Clarification | None = None


def load_catalog(path: Path) -> dict[str, Paper]:
    papers = TypeAdapter(list[Paper]).validate_python(json.loads(path.read_text(encoding="utf-8")))
    if not papers or len({p.paper_id for p in papers}) != len(papers):
        raise ValueError("paper catalog must contain unique IDs")
    return {p.paper_id: p for p in papers}


def _mentions(text: str, alias: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I))


def interpret(question: str, paper_ids, answer_type: str, catalog: dict[str, Paper]) -> Interpretation:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a nonempty string")
    if answer_type not in {"auto", "qa", "comparison"}:
        raise ValueError("answer_type must be auto, qa, or comparison")
    if paper_ids is not None and (not isinstance(paper_ids, (list, tuple)) or
                                  any(not isinstance(p, str) for p in paper_ids)):
        raise ValueError("paper_ids must be a list or tuple of IDs")
    explicit = list(dict.fromkeys(paper_ids)) if paper_ids is not None else None
    named = [p.paper_id for p in catalog.values()
             if any(_mentions(question, a) for a in [p.paper_id, p.title, *p.aliases])]
    compare = bool(re.search(r"\b(compare|comparison|versus|vs|differences?|similarities|differ)\b", question, re.I))
    paper_comparison = compare and (len(explicit or named) >= 2 or bool(re.search(
        r"\b(papers|studies|another paper|other paper)\b", question, re.I)) or
        bool(named and re.search(r"\b(versus|vs)\b|\bcompare\b.+\band\b", question, re.I)))
    kind = "comparison" if answer_type == "comparison" or (
        answer_type == "auto" and (paper_comparison or len(explicit or named) == 2)) else "qa"
    scope = named if explicit is None else explicit
    aspects = [name for name, pattern in {
        "methods": r"\b(method\w*|approach\w*|mechanism\w*)\b",
        "findings": r"\b(finding\w*|result\w*|experiment\w*|performance)\b",
        "limitations": r"\b(limit\w*|weakness\w*|assumption\w*)\b",
    }.items() if re.search(pattern, question, re.I)] or ["methods", "findings", "limitations"]
    result = Interpretation(kind, scope, aspects)

    def clarify(message):
        result.clarification = Clarification(question=message, candidate_paper_ids=list(catalog))
        return result

    if any(p not in catalog for p in scope):
        return clarify("Choose paper IDs present in the ResearchLens catalog.")
    if explicit is not None and any(p not in explicit for p in named):
        return clarify("The named papers conflict with the supplied paper IDs. Which papers should be used?")
    unknown_ids = {p.upper() for p in re.findall(r"\bP\d{3}\b", question, re.I)} - set(catalog)
    ambiguous = re.search(r"\b(this|that|another|other|a specific)\s+paper\b", question, re.I)
    # Unknown named papers cannot be resolved exhaustively by aliases. Treat explicit
    # paper references conservatively, while keeping general research questions usable.
    unresolved = not named and re.search(r"\b(paper|study)\b|[\"“]", question, re.I)
    if unknown_ids or (ambiguous and explicit is None) or (unresolved and explicit is None):
        return clarify("Identify the intended paper(s) using catalog IDs or recognized titles.")
    if explicit == []:
        return clarify("The explicit paper scope is empty. Choose a paper or omit paper_ids for general QA.")
    if kind == "comparison" and len(scope) != 2:
        return clarify("A comparison requires exactly two identified papers; specify both paper IDs.")
    if kind == "qa" and len(scope) > 1:
        return clarify("Use comparison mode for two papers, or select one paper for scoped QA.")
    # Unknown second names in comparisons must not be replaced with an arbitrary paper.
    return result
