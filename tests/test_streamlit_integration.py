"""Exercise the unchanged UI layout through its real HTTP adapter and API."""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app.api import create_app
from app.client import ResearchAPIClient
from src.generation.schemas import Clarification, ErrorInfo, GenerationResponse
from test_web_integration import Generator, grounded, service_for

ENTRYPOINT = Path(__file__).resolve().parents[1] / "app/streamlit_app.py"


def widget(elements,label):
    return next(e for e in elements if e.label==label)


@contextmanager
def ui(tmp_path, generator=None):
    gen=generator or Generator()
    service=service_for(gen,tmp_path)
    with TestClient(create_app(service)) as transport:
        # Starlette's in-process transport explicitly has no timeout semantics;
        # production timeouts are exercised separately with httpx/local TCP.
        class InProcessTransport:
            def request(self,*args,**kwargs):
                kwargs.pop("timeout",None)
                return transport.request(*args,**kwargs)
        adapter=ResearchAPIClient("http://testserver",client=InProcessTransport())
        st.cache_resource.clear()
        with patch("app.client.ResearchAPIClient",return_value=adapter):
            at=AppTest.from_file(ENTRYPOINT,default_timeout=15).run()
            assert not at.exception
            yield at,gen,service
        st.cache_resource.clear()


def ask(at,question="How does SelfCheckGPT work?"):
    at.text_area[0].set_value(question).run()
    widget(at.button,"Ask").click().run()
    assert not at.exception


def test_general_qa_uses_http_and_renders_real_citation_fields(tmp_path):
    with ui(tmp_path) as (at,gen,_):
        assert len(at.multiselect[0].options)==8
        ask(at)
        assert gen.calls[-1][1:]==(None,"auto",{"year":None,"author":None,"section":None})
        assert any(e.value==gen.result.citations[0].quote for e in at.code)
        assert any("SelfCheckGPT:" in e.value for e in at.markdown)
        assert any("PDF p. 1" in e.value for e in at.caption)
        assert any("Retrieved evidence" in e.label for e in at.expander)
        assert any("Complete answer" in e.value for e in at.success)
        assert all(e.label != "Sample API request" for e in at.expander)
        assert not any("curl " in e.value for e in at.code)


def test_ui_forwards_all_filters_and_comparison_selection(tmp_path):
    with ui(tmp_path) as (at,gen,_):
        at.multiselect[0].set_value(["P002"]).run()
        at.number_input[0].set_value(2023).run()
        widget(at.text_input,"Author contains").set_value(" Manakul ").run()
        widget(at.text_input,"Section contains").set_value(" Methods ").run()
        ask(at)
        assert gen.calls[-1][1:]==(["P002"],"auto",{"year":2023,"author":"Manakul","section":"Methods"})
        at.radio[0].set_value("Compare papers").run()
        assert widget(at.button,"Ask").disabled
        at.multiselect[0].set_value(["P002","P003"]).run()
        ask(at,"Compare SelfCheckGPT and FActScore methods.")
        assert gen.calls[-1][1:3]==(["P002","P003"],"comparison")


@pytest.mark.parametrize("status",["partial","abstained","needs_clarification","error"])
def test_ui_preserves_domain_and_structured_error_states(tmp_path,status):
    result=grounded();result.status=status
    if status=="partial":result.limitations=["Missing requested findings."]
    if status in {"abstained","needs_clarification","error"}:
        result.claims=[];result.citations=[];result.answer=""
    if status=="abstained":
        result.abstained=True;result.answer="I don't have sufficient usable evidence."
    if status=="needs_clarification":
        result.clarification=Clarification(question="Which paper?",candidate_paper_ids=["P002"])
    if status=="error":result.error=ErrorInfo(code="openai_api_error",message="The provider failed.")
    with ui(tmp_path,Generator(result)) as (at,_,_):
        ask(at)
        assert at.session_state["last_result"].status==status
        if status=="error": assert any("openai_api_error" in e.value for e in at.error)
        elif status=="abstained": assert any("enough evidence" in e.value for e in at.info)
        else: assert at.warning


def test_invalid_input_is_caught_before_http_and_clears_old_answer(tmp_path):
    with ui(tmp_path) as (at,gen,_):
        ask(at)
        assert len(gen.calls)==1
        ask(at,"x"*1001)
        assert len(gen.calls)==1 and "last_result" not in at.session_state
        assert any("Invalid input" in e.value for e in at.error)


@pytest.mark.parametrize("rating,label",[(1,"up"),(0,"down")])
def test_feedback_is_bound_to_answer_and_sent_once(tmp_path,rating,label):
    with ui(tmp_path) as (at,gen,service):
        ask(at)
        answer_key=at.session_state["last_result_key"]
        at.session_state[f"rating-{answer_key}"]=rating
        widget(at.text_input,"Optional comment").set_value("Clear citation").run()
        widget(at.button,"Send feedback").click().run()
        assert not at.exception
        assert widget(at.button,"Send feedback").disabled
        lines=service.feedback.path.read_text().splitlines()
        assert len(lines)==1
        import json
        record=json.loads(lines[0])
        assert record["submission_id"]==answer_key and record["rating"]==label
        assert record["request_id"]==answer_key  # Fixture has no provider request ID.
        at.run()
        assert len(service.feedback.path.read_text().splitlines())==1
        ask(at)
        assert at.session_state["last_result_key"]!=answer_key
        assert not widget(at.button,"Send feedback").disabled


def test_researcher_ui_has_no_debug_api_example(tmp_path):
    with ui(tmp_path) as (at,_,_):
        assert not any("API request" in e.label for e in at.expander)
        assert not any("curl " in e.value for e in at.code)


@pytest.mark.parametrize("mode",["unavailable","malformed"])
def test_unavailable_or_malformed_backend_does_not_show_tracebacks(mode):
    def respond(request):
        if mode=="unavailable": raise httpx.ConnectError("private backend details")
        return httpx.Response(200,json={"not":"the health contract"})
    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        adapter=ResearchAPIClient(client=transport)
        st.cache_resource.clear()
        with patch("app.client.ResearchAPIClient",return_value=adapter):
            at=AppTest.from_file(ENTRYPOINT).run()
            assert not at.exception and at.error
            assert not at.button
            assert all("private" not in e.value for e in at.error)
        st.cache_resource.clear()


def test_unready_backend_shows_papers_but_disables_ask(tmp_path):
    with ui(tmp_path,Generator(index_valid=False)) as (at,gen,_):
        at.text_area[0].set_value("A valid question").run()
        assert len(at.multiselect[0].options)==8 and widget(at.button,"Ask").disabled
        assert any("not ready" in e.value for e in at.warning)
        assert not gen.calls
