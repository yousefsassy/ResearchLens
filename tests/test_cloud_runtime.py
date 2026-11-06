"""Standalone service/UI regressions. Provider inference is always mocked."""
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app.client import APIClientError
from app.cloud_runtime import CloudRuntime, CloudSettings, DirectResearchClient, build_runtime
from app.schemas import AskRequest, FeedbackRequest
from app.security import DemoGuard
from src.generation.schemas import Clarification, ErrorInfo
from test_web_integration import Generator, configured_service, grounded, service_for
from test_generation import Client
from test_generation_client import success
import json
from pathlib import Path

ENTRY = Path(__file__).resolve().parents[1] / 'cloud/streamlit_app.py'


def settings(**changes):
    return CloudSettings('', '', datetime.now(timezone.utc) + timedelta(hours=1), **changes)


def runtime_for(tmp_path, gen=None, **guard_args):
    gen = gen or Generator()
    service = service_for(gen, tmp_path)
    service.warmup()
    return CloudRuntime(service, DemoGuard(budget_path=tmp_path / 'budget.json',
        ask_per_minute=100, **guard_args)), gen


@pytest.fixture
def cloud_env(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'not-a-real-key-cloud-test')
    monkeypatch.setenv('RESEARCHLENS_DEMO_PASSWORD', 'private-university-demo')
    monkeypatch.setenv('RESEARCHLENS_DEMO_EXPIRES_AT', (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
    monkeypatch.setenv('RESEARCHLENS_CLOUD_MAX_QUESTIONS', '20')
    monkeypatch.delenv('RESEARCHLENS_USE_LOCAL_ARTIFACTS', raising=False)
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def test_settings_require_key_passcode_explicit_expiry(cloud_env, monkeypatch):
    assert CloudSettings.from_env().max_questions == 20
    for key in ['OPENAI_API_KEY', 'RESEARCHLENS_DEMO_PASSWORD', 'RESEARCHLENS_DEMO_EXPIRES_AT']:
        with monkeypatch.context() as local:
            local.delenv(key)
            with pytest.raises(APIClientError): CloudSettings.from_env()


@pytest.mark.parametrize('key,value', [
    ('RESEARCHLENS_DEMO_EXPIRES_AT', '2020-01-01T00:00:00Z'),
    ('RESEARCHLENS_DEMO_EXPIRES_AT', '2099-01-01T00:00:00'),
    ('RESEARCHLENS_CLOUD_MAX_QUESTIONS', '0'),
    ('RESEARCHLENS_CLOUD_MAX_QUESTIONS', '101'),
    ('RESEARCHLENS_CLOUD_MAX_QUESTIONS', 'bad'),
    ('RESEARCHLENS_DEMO_PASSWORD', 'short'),
])
def test_bad_access_settings_fail_closed(cloud_env, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(APIClientError): CloudSettings.from_env()


def test_unauthorized_expired_rate_and_budget_prevent_generation(tmp_path):
    runtime, gen = runtime_for(tmp_path, max_questions=1)
    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    request = AskRequest(question='How does SelfCheckGPT work?')
    denied = DirectResearchClient(runtime, authorized=lambda: False, expires_at=settings().expires_at)
    with pytest.raises(APIClientError, match='authorization'): denied.ask(request)
    with pytest.raises(APIClientError): denied.record_feedback(FeedbackRequest(rating='up'))
    ended = DirectResearchClient(runtime, authorized=lambda: True, expires_at=expired)
    with pytest.raises(APIClientError, match='ended'): ended.ask(request)
    assert not gen.calls and not runtime.guard.path.exists()
    client = DirectResearchClient(runtime, authorized=lambda: True, expires_at=settings().expires_at)
    assert client.ask(request).status == 'complete'
    with pytest.raises(APIClientError, match='exhausted'): client.ask(request)
    assert len(gen.calls) == 1


def test_direct_rate_limit_and_restart_keeps_file_when_disk_survives(tmp_path):
    runtime, gen = runtime_for(tmp_path)
    runtime.guard.limits['ask'] = 1
    client = DirectResearchClient(runtime, authorized=lambda: True, expires_at=settings().expires_at)
    request = AskRequest(question='SelfCheckGPT methodology')
    client.ask(request)
    with pytest.raises(APIClientError, match='rate limit'): client.ask(request)
    assert len(gen.calls) == 1
    restarted = DemoGuard(budget_path=runtime.guard.path, max_questions=1)
    with pytest.raises(Exception) as exc: restarted.reserve('ask')
    assert exc.value.status_code == 429
    # Community Cloud may delete the entire disk; no test assumes durable hosting.


def test_builder_warms_once_and_closes_failed_runtime(tmp_path):
    service = Mock()
    service.warmup.return_value.status = 'ok'
    factory, provision = Mock(return_value=service), Mock()
    runtime = build_runtime(settings(), root=tmp_path, service_factory=factory, provision=provision)
    factory.assert_called_once()
    service.warmup.assert_called_once()
    provision.assert_called_once_with(tmp_path, '', '', use_local=False)
    runtime.close()
    service.close.assert_called_once()
    service.reset_mock()
    service.warmup.return_value.status = 'degraded'
    with pytest.raises(APIClientError): build_runtime(settings(), root=tmp_path, service_factory=factory, provision=provision)
    service.close.assert_called_once()


def test_direct_service_retains_two_attempt_cap_and_shared_retriever(tmp_path):
    sdk = Mock()
    bad = Client().result
    bad['claims'][0]['citations'][0]['quote'] = 'invented unsupported quotation'
    sdk.responses.create.side_effect = [success(output_text=json.dumps(bad))] * 4
    service, backend, factory, owner = configured_service(tmp_path, sdk)
    service.warmup()
    runtime = CloudRuntime(service, DemoGuard(budget_path=tmp_path / 'budget.json'))
    client = DirectResearchClient(runtime, authorized=lambda: True, expires_at=settings().expires_at)
    for _ in range(2):
        result = client.ask(AskRequest(question='How does SelfCheckGPT work?'))
        assert result.metrics.attempts == 2
    assert sdk.responses.create.call_count == 4
    factory.assert_called_once()
    backend.encoder.encode_query.assert_called_once()
    service.close()


def login(at):
    at.text_input[0].set_value('private-university-demo').run()
    next(b for b in at.button if b.label == 'Enter demo').click().run()
    assert not at.exception


def ask(at, question='How does SelfCheckGPT work?'):
    at.text_area[0].set_value(question).run()
    next(b for b in at.button if b.label == 'Ask').click().run()
    assert not at.exception


def test_cloud_ui_gate_cache_filters_comparison_quotes_and_feedback(tmp_path, monkeypatch, cloud_env):
    runtime, gen = runtime_for(tmp_path)
    builder = Mock(return_value=runtime)
    monkeypatch.setattr('app.cloud_runtime.build_runtime', builder)
    with monkeypatch.context() as local:
        # HTTP must never be used by the standalone entrypoint.
        local.setattr('app.client.ResearchAPIClient', Mock(side_effect=AssertionError('HTTP not expected')))
        at = AppTest.from_file(ENTRY, default_timeout=15).run()
        assert not at.exception and not builder.called
        at.text_input[0].set_value('wrong').run()
        at.button[0].click().run()
        assert not builder.called
        login(at)
        ask(at)
        assert gen.calls[-1][1:] == (None, 'auto', {'year': None, 'author': None, 'section': None})
        assert any(e.value == gen.result.citations[0].quote for e in at.code)
        assert any('PDF p. 1' in e.value for e in at.caption)
        at.multiselect[0].set_value(['P002']).run()
        at.number_input[0].set_value(2023).run()
        next(e for e in at.text_input if e.label == 'Author contains').set_value('Manakul').run()
        next(e for e in at.text_input if e.label == 'Section contains').set_value('Methods').run()
        ask(at)
        assert gen.calls[-1][1:] == (['P002'], 'auto', {'year': 2023, 'author': 'Manakul', 'section': 'Methods'})
        at.radio[0].set_value('Compare papers').run()
        at.multiselect[0].set_value(['P002', 'P003']).run()
        ask(at, 'Compare SelfCheckGPT and FActScore methods.')
        assert gen.calls[-1][1:3] == (['P002', 'P003'], 'comparison')
        at.feedback[0].set_value(1).run()
        next(e for e in at.text_input if e.label == 'Optional comment').set_value('Useful demo').run()
        next(e for e in at.button if e.label == 'Send feedback').click().run()
        assert json.loads(runtime.service.feedback.path.read_text().splitlines()[0])['rating'] == 'up'
        second_session = AppTest.from_file(ENTRY, default_timeout=15).run()
        login(second_session)
        builder.assert_called_once()  # Shared model/service across reruns and visitors.
        for elements in [at.markdown, at.caption, at.code, at.error]:
            assert not any('not-a-real-key-cloud-test' in str(e.value) or 'curl ' in str(e.value) for e in elements)


@pytest.mark.parametrize('status', ['partial', 'abstained', 'needs_clarification', 'error'])
def test_cloud_ui_preserves_answer_states(tmp_path, monkeypatch, cloud_env, status):
    result = grounded()
    result.status = status
    if status == 'partial': result.limitations = ['Missing requested finding.']
    if status == 'abstained': result.abstained = True
    if status == 'needs_clarification': result.clarification = Clarification(question='Which paper?', candidate_paper_ids=['P002'])
    if status == 'error': result.error = ErrorInfo(code='openai_timeout', message='Generation timed out.')
    runtime, _ = runtime_for(tmp_path, Generator(result))
    monkeypatch.setattr('app.cloud_runtime.build_runtime', Mock(return_value=runtime))
    at = AppTest.from_file(ENTRY, default_timeout=15).run()
    login(at)
    ask(at)
    text = ' '.join(str(e.value) for group in [at.info, at.warning, at.error] for e in group)
    assert {'partial':'Partial answer', 'abstained':'not contain enough evidence',
            'needs_clarification':'Clarification needed', 'error':'timed out'}[status] in text


def test_cloud_startup_failure_does_not_publish_raw_errors(tmp_path, monkeypatch, cloud_env):
    monkeypatch.setattr('app.cloud_runtime.build_runtime', Mock(side_effect=APIClientError('Runtime artifacts are unavailable.')))
    at = AppTest.from_file(ENTRY, default_timeout=15).run()
    login(at)
    assert not at.exception
    assert any('artifacts' in e.value for e in at.error)
