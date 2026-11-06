"""Demo controls: mocked inference, no external network or credentials."""
from concurrent.futures import ThreadPoolExecutor
import json

from fastapi import HTTPException
from fastapi.testclient import TestClient
import httpx
import pytest

from app.api import create_app
from app.client import APIClientError, ResearchAPIClient
from app.schemas import AskRequest, FeedbackRequest
from app.security import DemoGuard
from test_web_integration import Generator, service_for

TOKEN = 'a' * 40
AUTH = {'Authorization': 'Bearer ' + TOKEN}
QUESTION = {'question': 'How does SelfCheckGPT work?'}


def test_auth_public_metadata_and_protected_posts(tmp_path):
    gen = Generator()
    guard = DemoGuard(TOKEN, budget_path=tmp_path / 'budget.json')
    with TestClient(create_app(service_for(gen, tmp_path), guard=guard)) as api:
        assert api.get('/health').status_code == 200
        assert api.get('/papers').status_code == 200
        for endpoint, body in [('/ask', QUESTION), ('/feedback', {'rating': 'up'})]:
            for headers in [{}, {'Authorization': 'Bearer wrong'}]:
                result = api.post(endpoint, json=body, headers=headers)
                assert result.status_code == 401
                assert TOKEN not in result.text and 'wrong' not in result.text
        assert not gen.calls and not guard.path.exists()
        assert api.post('/ask', json=QUESTION, headers=AUTH).status_code == 200
        assert api.post('/feedback', json={'rating': 'up'}, headers=AUTH).status_code == 200


def test_missing_production_token_fails_closed(tmp_path):
    guard = DemoGuard(required=True)
    with TestClient(create_app(service_for(Generator(), tmp_path), guard=guard)) as api:
        assert api.get('/health').status_code == 503
        assert api.get('/papers').status_code == 200
        assert api.post('/ask', json=QUESTION).status_code == 503


def test_local_default_unchanged(tmp_path):
    with TestClient(create_app(service_for(Generator(), tmp_path), guard=DemoGuard())) as api:
        assert api.post('/ask', json=QUESTION).status_code == 200


def test_rate_windows_and_independent_feedback(tmp_path):
    now = [0]
    guard = DemoGuard(TOKEN, budget_path=tmp_path / 'budget.json',
                      ask_per_minute=1, feedback_per_minute=1, clock=lambda: now[0])
    guard.admit(AUTH['Authorization'], 'ask')
    guard.admit(AUTH['Authorization'], 'feedback')
    for kind in ['ask', 'feedback']:
        with pytest.raises(HTTPException) as exc:
            guard.admit(AUTH['Authorization'], kind)
        assert exc.value.status_code == 429
        assert exc.value.headers['Retry-After'] == '60'
    now[0] = 60
    guard.admit(AUTH['Authorization'], 'ask')
    assert json.loads(guard.path.read_text())['questions'] == 2


def test_budget_survives_restart_and_is_atomic_under_threads(tmp_path):
    path = tmp_path / 'budget.json'
    guard = DemoGuard(TOKEN, budget_path=path, max_questions=3, ask_per_minute=100)
    def call(_):
        try:
            guard.admit(AUTH['Authorization'], 'ask')
            return 200
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(call, range(12)))
    assert results.count(200) == 3 and results.count(429) == 9
    assert path.stat().st_mode & 0o777 == 0o600
    restarted = DemoGuard(TOKEN, budget_path=path, max_questions=3)
    with pytest.raises(HTTPException) as exc:
        restarted.admit(AUTH['Authorization'], 'ask')
    assert exc.value.status_code == 429


@pytest.mark.parametrize('content', ['broken', '{}', '{"version":1,"questions":-1}',
                                  '{"version":1,"questions":true}', 'null'])
def test_corrupt_budget_sanitized(tmp_path, content):
    path = tmp_path / 'budget.json'
    path.write_text(content)
    guard = DemoGuard(TOKEN, budget_path=path)
    with TestClient(create_app(service_for(Generator(), tmp_path), guard=guard)) as api:
        result = api.post('/ask', json=QUESTION, headers=AUTH)
        assert result.status_code == 503
        assert str(path) not in result.text and TOKEN not in result.text


def test_storage_failure_sanitized(tmp_path):
    path = tmp_path / 'not-a-directory'
    path.write_text('x')
    guard = DemoGuard(TOKEN, budget_path=path / 'budget.json')
    with pytest.raises(HTTPException) as exc:
        guard.admit(AUTH['Authorization'], 'ask')
    assert exc.value.status_code == 503
    assert str(path) not in str(exc.value.detail)


def test_client_posts_token_only_and_no_retry():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(429, text='private provider detail ' + TOKEN)
    client = ResearchAPIClient('https://api.example.invalid',
        client=httpx.Client(transport=httpx.MockTransport(handler)), api_token=TOKEN)
    with pytest.raises(APIClientError, match='allowance') as error:
        client.ask(AskRequest(**QUESTION))
    assert len(requests) == 1 and requests[0].headers['Authorization'] == 'Bearer ' + TOKEN
    assert TOKEN not in str(error.value)
    with pytest.raises(APIClientError):
        client.papers()
    assert 'Authorization' not in requests[1].headers
    with pytest.raises(APIClientError):
        client.record_feedback(FeedbackRequest(rating='up'))
    assert requests[2].headers['Authorization'] == 'Bearer ' + TOKEN


def test_remote_plaintext_token_rejected():
    with pytest.raises(APIClientError, match='HTTPS'):
        ResearchAPIClient('http://remote.example.invalid', api_token=TOKEN)


def test_streamlit_demo_gate_requires_separate_passcode(tmp_path, monkeypatch):
    from pathlib import Path
    from unittest.mock import patch
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('RESEARCHLENS_DEMO_PASSWORD', 'university-demo-secret')
    monkeypatch.setenv('RESEARCHLENS_API_TOKEN', TOKEN)
    st.cache_resource.clear()
    gen = Generator()
    guard = DemoGuard(TOKEN, budget_path=tmp_path / 'budget.json')
    with TestClient(create_app(service_for(gen, tmp_path), guard=guard)) as api:
        class Transport:
            def request(self, *args, **kwargs):
                kwargs.pop('timeout', None)
                return api.request(*args, **kwargs)
        adapter = ResearchAPIClient('http://testserver', client=Transport(), api_token=TOKEN)
        with patch('app.client.ResearchAPIClient', return_value=adapter) as factory:
            entry = Path(__file__).resolve().parents[1] / 'app/streamlit_app.py'
            at = AppTest.from_file(entry, default_timeout=15).run()
            assert not at.exception and not factory.called
            assert at.text_input[0].proto.type == 1
            at.text_input[0].set_value('wrong').run()
            at.button[0].click().run()
            assert not at.exception and not factory.called
            at.text_input[0].set_value('university-demo-secret').run()
            at.button[0].click().run()
            assert not at.exception and factory.called
            assert at.session_state['demo_authorized'] is True
            assert not any(TOKEN in str(e.value) or 'university-demo-secret' in str(e.value)
                           for elements in [at.markdown, at.caption, at.code, at.error]
                           for e in elements)
    st.cache_resource.clear()
