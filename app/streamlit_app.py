"""Streamlit frontend for ResearchLens.

Run locally:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import os
import hmac
from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import AskRequest, FeedbackRequest
from app.client import APIClientError, ResearchAPIClient


st.set_page_config(
    page_title="ResearchLens",
    page_icon="RL",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_client(api_url: str, api_token: str = "") -> ResearchAPIClient:
    return ResearchAPIClient(api_url, api_token=api_token)


def api_url() -> str:
    return os.environ.get("RESEARCHLENS_API_URL", "http://127.0.0.1:8000")


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


def render_answer(result, client, response_key) -> None:
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

    request_key = response_key
    sent_key = f"feedback-sent-{request_key}"
    st.markdown("### Was this answer useful?")
    rating = st.feedback("thumbs", key=f"rating-{request_key}")
    comment = st.text_input("Optional comment", key=f"comment-{request_key}")
    if st.button("Send feedback", key=f"send-{request_key}", disabled=st.session_state.get(sent_key, False)):
        if rating is None:
            st.warning("Choose thumbs up or thumbs down first.")
        else:
            try:
                client.record_feedback(FeedbackRequest(
                    submission_id=request_key,
                    rating="up" if rating == 1 else "down",
                    request_id=result.metrics.request_id or request_key,
                    status=result.status,
                    comment=comment,
                ))
            except ValidationError:
                st.error("Feedback is invalid. Keep the comment under 1,000 characters.")
            except APIClientError as error:
                st.error(str(error))
            else:
                st.session_state[sent_key] = True
                st.rerun()
    if st.session_state.get(sent_key, False):
        st.success("Feedback saved. Thank you.")


def main(client_factory=None, *, require_demo_password=False) -> None:
    st.title("ResearchLens")
    password = os.environ.get("RESEARCHLENS_DEMO_PASSWORD", "")
    if require_demo_password and len(password) < 12:
        st.error("Configure a private demonstration passcode of at least 12 characters in server secrets.")
        st.stop()
    if password and not st.session_state.get("demo_authorized", False):
        st.info("Enter the demonstration passcode supplied by the project team.")
        supplied = st.text_input("Demo passcode", type="password", key="demo_passcode")
        if st.button("Enter demo"):
            if hmac.compare_digest(supplied.encode(), password.encode()):
                st.session_state["demo_authorized"] = True
                st.session_state.pop("demo_passcode", None)
                st.rerun()
            else:
                st.error("Incorrect demonstration passcode.")
        st.stop()
    st.caption(
        "Citation-grounded question answering over a curated paper collection. "
        "Each question is independent; there is no conversation memory."
    )
    try:
        client = (client_factory() if client_factory else
                  get_client(api_url(), os.environ.get("RESEARCHLENS_API_TOKEN", "")))
        health = client.health()
        papers = client.papers()
    except APIClientError as error:
        st.error(str(error))
        st.stop()
    paper_by_id = {paper.paper_id: paper for paper in papers}
    paper_ids = [paper.paper_id for paper in papers]
    if health.status != "ok":
        st.warning("The backend is not ready. Check the server's corpus, index, BGE cache and API configuration.")

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
        or health.status != "ok"
        or (compare and len(selected) != 2)
        or (not compare and len(selected) > 1)
    )

    if st.button("Ask", type="primary", disabled=disabled):
        st.session_state.pop("last_result", None)
        with st.spinner("Retrieving evidence and generating a grounded answer…"):
            try:
                request = AskRequest(
                    question=question, paper_ids=selected or None,
                    answer_type="comparison" if compare else "auto",
                    year=int(year_value) if year_value else None,
                    author=author or None, section=section or None,
                )
                result = client.ask(request)
            except ValidationError:
                st.error("Invalid input. Use a 3–1,000 character question and author/section filters under 200 characters.")
            except APIClientError as error:
                st.error(str(error))
            else:
                st.session_state["last_result"] = result
                st.session_state["last_result_key"] = str(uuid4())

    result = st.session_state.get("last_result")
    if result is not None:
        render_answer(result, client, st.session_state["last_result_key"])


if __name__ == "__main__":
    main()
