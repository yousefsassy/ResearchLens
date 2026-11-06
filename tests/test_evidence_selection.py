import copy

import pytest

from src.generation.evidence import select_evidence
from src.generation.evidence_quality import quality
from src.generation.papers import Interpretation, Paper, interpret


@pytest.fixture
def catalog():
    return {key: Paper(paper_id=key, title=name, aliases=[name], pdf_filename=f"{key}.pdf")
            for key, name in [("A", "Amber"), ("B", "Birch")]}


def row(paper, label, text, score=0.03):
    return dict(chunk_id=f"{paper}-{label}", paper_id=paper, pdf_filename=f"{paper}.pdf",
                pdf_page=7, text=text, needs_review=False, review_flags=[],
                retrieval_score=score, vector_score=0.8, bm25_score=2.0, rrf_score=score)


def method(paper):
    return row(paper, "method", f"The {paper} method decomposes an input into independent statements. "
               "It then retrieves documents and compares each statement with the supporting text.")


def limitation(paper):
    return row(paper, "limit", f"The {paper} procedure requires access to a trusted document collection. "
               "Its applicability is restricted when documents are unavailable or incomplete.")


class Backend:
    def __init__(self, pools, failures=()):
        self.pools, self.failures, self.calls = pools, failures, []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        query = kwargs["question"]
        aspect = ("limitations" if query.startswith("What are the limitations") else
                  "methods" if query.startswith("How does") else
                  "findings" if query.startswith("What are the main findings") else "general")
        paper = kwargs["paper_ids"][0]
        if (paper, aspect) in self.failures:
            raise RuntimeError("private backend details")
        return copy.deepcopy(self.pools.get((paper, aspect), []))


def select(backend, catalog, aspects=("methods", "limitations"), budget=12000, question="Compare Amber and Birch"):
    return select_evidence(backend, question, Interpretation("comparison", ["A", "B"], list(aspects)), catalog, budget)


def test_requested_paper_aspect_coverage_and_metadata(catalog):
    pools = {(p, aspect): [method(p) if aspect == "methods" else limitation(p)]
             for p in catalog for aspect in ("methods", "limitations")}
    backend = Backend(pools)
    result = select(backend, catalog)
    assert not result.gaps
    assert {x.chunk_id for x in result.passages} == {"A-method", "B-method", "A-limit", "B-limit"}
    assert len(backend.calls) == 6
    assert all(c["mode"] == "hybrid" and not c["rerank"] and c["exclude_flagged"] for c in backend.calls)
    for index, item in enumerate(result.passages, 1):
        assert item.source_id == f"S{index}" and item.pdf_page == 7
        assert item.pdf_filename == f"{item.paper_id}.pdf"
        assert item.title == catalog[item.paper_id].title
        assert item.vector_score == 0.8 and item.bm25_score == 2.0
        assert item.text == next(r[0]["text"] for r in pools.values() if r[0]["chunk_id"] == item.chunk_id)


def test_figure_axes_do_not_displace_methods(catalog):
    pools = {}
    for p in catalog:
        axes = row(p, "axes", "Figure 2\nAccuracy\n0.1\n0.2\n0.3\n0.4\nSamples\n10\n20\n30", 0.04)
        pools[p, "general"] = pools[p, "methods"] = [axes, method(p)]
    result = select(Backend(pools), catalog, aspects=("methods",), budget=400)
    assert [x.chunk_id for x in result.passages] == ["A-method", "B-method"]
    assert not result.gaps


def test_missing_limitations_not_masked_by_general_results_or_heading(catalog):
    pools = {(p, aspect): [method(p)] for p in catalog for aspect in ("general", "methods", "limitations")}
    pools["A", "limitations"] = [row("A", "heading", "Limitations\n" + method("A")["text"])]
    result = select(Backend(pools), catalog)
    assert sum("No adequate supporting evidence" in gap and "limitations" in gap for gap in result.gaps) == 2
    assert not any("retrieval failed" in gap for gap in result.gaps)


def test_retrieval_failure_distinct_from_absent_evidence(catalog):
    backend = Backend({(p, "methods"): [method(p)] for p in catalog}, failures={("B", "limitations")})
    result = select(backend, catalog)
    assert any("No adequate supporting evidence retrieved for A: limitations" in gap for gap in result.gaps)
    assert any("Could not assess evidence for B: limitations; retrieval failed" in gap for gap in result.gaps)
    assert "private" not in str(result)
    assert len(result.passages) == 2


def test_budget_prioritizes_all_cells_before_redundant_extras(catalog):
    pools = {}
    for p in catalog:
        original = method(p)
        duplicate = {**original, "chunk_id": f"{p}-duplicate", "text": original["text"] + " Indeed."}
        pools[p, "methods"] = [original, duplicate]
        pools[p, "limitations"] = [limitation(p)]
    budget = sum(len(pool[0]["text"]) for pool in pools.values())
    result = select(Backend(pools), catalog, budget=budget)
    assert len(result.passages) == 4 and not result.gaps
    assert all("duplicate" not in x.chunk_id for x in result.passages)
    assert sum(len(x.text) for x in result.passages) <= budget
    too_small = select(Backend(pools), catalog, budget=170)
    assert any("was not selected within the evidence budget" in gap for gap in too_small.gaps)


def test_shared_passage_can_cover_multiple_aspects(catalog):
    pools = {}
    for p in catalog:
        shared = row(p, "shared", method(p)["text"] + " " + limitation(p)["text"])
        for aspect in ("methods", "limitations"):
            pools[p, aspect] = [shared]
    result = select(Backend(pools), catalog)
    assert len(result.passages) == 2 and not result.gaps


def test_deterministic_and_no_cross_paper_deduplication(catalog):
    text = "The method retrieves documents and compares each statement with the supporting text."
    pools = {(p, "methods"): [row(p, "same", text)] for p in catalog}
    first = select(Backend(pools), catalog, aspects=("methods",))
    second = select(Backend(pools), catalog, aspects=("methods",))
    assert first == second and len(first.passages) == 2


def test_numeric_findings_and_changed_values_are_retained(catalog):
    pools = {}
    for p in catalog:
        text = "The experiment measured accuracy of 81.2 percent using 400 trials with independent samples."
        pools[p, "findings"] = [row(p, "results1", text), row(p, "results2", text.replace("81.2", "87.3"))]
    result = select(Backend(pools), catalog, aspects=("findings",))
    assert len(result.passages) == 4 and not result.gaps
    assert any("81.2" in x.text for x in result.passages)
    assert any("87.3" in x.text for x in result.passages)


def test_labeled_numeric_tables_are_available_for_findings(catalog):
    text = "Metric Baseline Proposed\nAccuracy 81.2 87.3\nPrecision 70.1 75.2\nRecall 64.3 66.4"
    pools = {(p, "findings"): [row(p, "table", text)] for p in catalog}
    result = select(Backend(pools), catalog, aspects=("findings",))
    assert len(result.passages) == 2 and not result.gaps
    assert all(x.text == text for x in result.passages)


def test_near_duplicate_removal_preserves_negation(catalog):
    text = "The method can retrieve documents from remote collections and compare each independent statement with the supporting text."
    pools = {(p, "methods"): [row(p, "positive", text),
                              row(p, "negative", text.replace("can retrieve", "cannot retrieve"))]
             for p in catalog}
    result = select(Backend(pools), catalog, aspects=("methods",))
    assert len(result.passages) == 4


def test_hybrid_relevance_retained_among_informative_passages(catalog):
    pools = {}
    for p in catalog:
        strong = row(p, "strong", "The method compares each input statement against independently retrieved supporting documents.", 0.04)
        weak = row(p, "weak", "Our method provides an approach and procedure for a framework with algorithm steps.", 0.001)
        pools[p, "methods"] = [strong, weak]
    result = select(Backend(pools), catalog, aspects=("methods",), budget=210)
    assert [x.chunk_id for x in result.passages] == ["A-strong", "B-strong"]


def test_single_paper_quality_ranking_keeps_short_valid_evidence(catalog):
    useful = row("A", "short", "Amber uses consistency.")
    backend = Backend({("A", "general"): [row("A", "axes", "Figure\n1\n2\n3\n4"), useful]})
    result = select_evidence(backend, "Explain Amber", Interpretation("qa", ["A"], ["methods"]), catalog, 500)
    assert [x.chunk_id for x in result.passages] == ["A-short"]
    assert not result.gaps and len(backend.calls) == 1


def test_identical_requests_are_cached_only_within_question(catalog):
    backend = Backend({(p, "methods"): [method(p)] for p in catalog})
    question = "How does Amber work? Explain its proposed method, procedure and approach."
    select(backend, catalog, aspects=("methods",), question=question)
    assert len(backend.calls) == 3  # A general == A aspect, B scope is different.
    select(backend, catalog, aspects=("methods",), question=question)
    assert len(backend.calls) == 6


def test_aspect_detection_includes_how_it_works_and_constraints(catalog):
    result = interpret("Compare Amber and Birch: how each works and applicability constraints", None, "auto", catalog)
    assert result.aspects == ["methods", "limitations"]


@pytest.mark.parametrize("artifact", ["[1] Smith. 2020. Proceedings of Example Conference.\n" * 5,
                                      "Conference Header\n" * 10,
                                      "\ufffd\ufffd\ufffd broken extraction \ufffd\ufffd\ufffd"])
def test_artifact_penalties_do_not_rewrite_passages(artifact):
    assert quality(artifact) < quality(method("A")["text"])


def test_invalid_metadata_still_fails_closed(catalog):
    malformed = {**method("A"), "pdf_filename": "wrong.pdf"}
    with pytest.raises(ValueError, match="catalog"):
        select(Backend({("A", "methods"): [malformed]}), catalog)
