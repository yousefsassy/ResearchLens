"""Streamlit frontend for ResearchLens.

Run locally:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import AskRequest, FeedbackRequest
from app.service import ResearchService


st.set_page_config(
    page_title="ResearchLens",
    page_icon="RL",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_service() -> ResearchService:
    return ResearchService()


SAMPLES = [
    "How does SelfCheckGPT detect hallucinations?",
    "What are the limitations of FActScore?",
    "What temperatures did SelfCheckGPT use for sampling?",
    "Compare SelfCheckGPT and FActScore.",
    "What are the four steps of Chain-of-Verification?",
    "What did HaluEval find about hallucination recognition?",
    "What is the exact benchmark score of the fictional Neptune-2099 model?",
]


def status_banner(result) -> None:
    if result.status == "complete":
        st.success("Complete answer")
    elif result.status == "partial":
        st.warning("Partial answer — some requested information is missing")
    elif result.status == "abstained":
        st.info("The corpus does not contain enough evidence to answer this")
    elif result.status == "needs_clarification":
        st.warning("Clarification needed")
    else:
        st.error("The request could not be completed")


def render_answer(result) -> None:
    status_banner(result)

    if result.clarification:
        st.write(result.clarification.question)
        if result.clarification.candidate_paper_ids:
            st.caption("Available papers: " + ", ".join(result.clarification.candidate_paper_ids))

    if result.error:
        st.error(f"{result.error.code}: {result.error.message}")

    if result.answer:
        st.markdown("### Answer")
        st.markdown(result.answer)

    if result.citations:
        st.markdown("### Sources")
        for citation in result.citations:
            title = citation.title or citation.paper_id
            meta = [citation.paper_id, f"PDF p. {citation.pdf_page}", citation.chunk_id]
            if citation.year:
                meta.insert(1, str(citation.year))
            if citation.section:
                meta.append(citation.section)
            st.markdown(f"**[{citation.citation_id}] {title}**")
            st.caption(" · ".join(meta))
            st.code(citation.quote, language=None)

    if result.limitations:
        st.markdown("### Limitations")
        for limitation in result.limitations:
            st.write(f"- {limitation}")

    if result.evidence:
        with st.expander(f"Retrieved evidence ({len(result.evidence)} passages)"):
            for item in result.evidence:
                st.markdown(f"**{item.source_id} · {item.paper_id} · PDF p. {item.pdf_page}**")
                if item.section:
                    st.caption(f"Section: {item.section}")
                st.text(item.text)

    with st.expander("Request metrics"):
        metrics = result.metrics
        st.write(f"Total: {metrics.total_seconds:.2f}s")
        st.write(f"Retrieval: {metrics.retrieval_seconds:.2f}s")
        st.write(f"Generation: {metrics.generation_seconds:.2f}s")
        st.write(f"Model: {metrics.model or 'unknown'}")
        st.write(f"Attempts: {metrics.attempts}")
        st.write(f"Input tokens: {metrics.prompt_tokens}")
        st.write(f"Output tokens: {metrics.completion_tokens}")

    request_key = result.metrics.request_id or str(abs(hash(result.question)))
    st.markdown("### Was this answer useful?")
    rating = st.feedback("thumbs", key=f"rating-{request_key}")
    comment = st.text_input("Optional comment", key=f"comment-{request_key}")
    if st.button("Send feedback", key=f"send-{request_key}"):
        if rating is None:
            st.warning("Choose thumbs up or thumbs down first.")
        else:
            get_service().record_feedback(FeedbackRequest(
                rating="up" if rating == 1 else "down",
                request_id=result.metrics.request_id,
                status=result.status,
                comment=comment,
            ))
            st.success("Feedback saved. Thank you.")


def main() -> None:
    service = get_service()
    papers = service.papers()
    paper_by_id = {paper.paper_id: paper for paper in papers}
    paper_ids = [paper.paper_id for paper in papers]

    st.title("ResearchLens")
    st.caption(
        "Citation-grounded question answering over a curated paper collection. "
        "Each question is independent; there is no conversation memory."
    )

    with st.sidebar:
        st.header("Scope")
        mode = st.radio(
            "Mode",
            ["Question answering", "Compare papers"],
            help="Comparison mode requires exactly two papers.",
        )
        compare = mode == "Compare papers"
        selected = st.multiselect(
            "Research papers",
            options=paper_ids,
            format_func=lambda paper_id: f"{paper_id} — {paper_by_id[paper_id].title}",
            max_selections=2 if compare else 1,
            help="Leave empty to search all papers in question-answering mode.",
        )

        st.subheader("Metadata filters")
        year_value = st.number_input("Year", min_value=0, max_value=2100, value=0, step=1)
        author = st.text_input("Author contains", placeholder="e.g. Manakul")
        section = st.text_input("Section contains", placeholder="e.g. Limitations")

        st.divider()
        st.caption(
            "Evidence is retrieved with BM25 + BGE and filtered before ranking. "
            "Answers are generated only from retrieved passages."
        )
        st.caption(f"Corpus: {len(papers)} papers")

    sample = st.selectbox("Sample question", ["", *SAMPLES])
    question = st.text_area(
        "Question",
        value=sample,
        height=110,
        placeholder="Ask a question about the indexed papers…",
    )

    if compare and len(selected) != 2:
        st.info("Select exactly two papers to compare.")
    if not compare and len(selected) > 1:
        st.info("Question-answering mode uses one paper or all papers. Switch to comparison mode to use two.")

    disabled = (
        len(question.strip()) < 3
        or (compare and len(selected) != 2)
        or (not compare and len(selected) > 1)
    )

    if st.button("Ask", type="primary", disabled=disabled):
        request = AskRequest(
            question=question,
            paper_ids=selected or None,
            answer_type="comparison" if compare else "auto",
            year=int(year_value) if year_value else None,
            author=author or None,
            section=section or None,
        )
        with st.spinner("Retrieving evidence and generating a grounded answer…"):
            try:
                result = service.ask(request)
            except Exception:
                st.error("The research service is unavailable. Check the server logs.")
            else:
                st.session_state["last_result"] = result

    result = st.session_state.get("last_result")
    if result is not None:
        render_answer(result)

    with st.expander("Sample API request"):
        api_url = os.environ.get("RESEARCHLENS_API_URL", "http://localhost:8000")
        st.code(
            f"""curl -s -X POST "{api_url}/ask" \\
  -H "Content-Type: application/json" \\
  -d '{{"question": "How does SelfCheckGPT detect hallucinations?", "paper_ids": ["P002"]}}'""",
            language="bash",
        )
        st.caption("The OpenAI key is only used by the backend; it is never sent to the browser.")


if __name__ == "__main__":
    main()
