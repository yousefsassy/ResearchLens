#!/usr/bin/env python3
"""Exercise standalone UI + real local retrieval with mocked SDK and no network.

Requires existing verified runtime artifacts and cloud/requirements.txt. Does not
use your provider key or make inference calls. Linux peak RSS includes AppTest/UI
and the ML runtime, but is not a Community Cloud resource guarantee.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import resource
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    os.environ.update(OPENAI_API_KEY='offline-smoke-not-a-real-key',
        RESEARCHLENS_DEMO_PASSWORD='offline-smoke-passcode', RESEARCHLENS_USE_LOCAL_ARTIFACTS='true',
        RESEARCHLENS_DEMO_EXPIRES_AT=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    from app.cloud_runtime import build_runtime
    from openai import APITimeoutError
    import httpx

    sdk = Mock()
    def mocked_answer(**kwargs):
        payload = json.loads(kwargs['input'])
        question = payload['question']
        if 'simulate timeout' in question:
            raise APITimeoutError(request=httpx.Request('POST', 'https://example.invalid'))
        if 'Neptune-2099' in question:
            output = {'status': 'abstained', 'claims': [], 'limitations': ['No supporting information in the supplied evidence.']}
        else:
            selected = {}
            for source in payload['evidence']:
                selected.setdefault(source['paper_id'], source)
            claims = []
            for source in list(selected.values())[:2]:
                candidates = payload['verbatim_quote_candidates'][source['source_id']]
                quote = candidates[0] if candidates else source['text'][:180]
                claims.append({'text': quote, 'kind': 'reported', 'citations': [
                    {'source_id': source['source_id'], 'quote': quote}]})
            output = {'status': 'partial', 'claims': claims,
                      'limitations': ['Offline transport/UI smoke only; provider output is mocked.']}
        return SimpleNamespace(id='offline-smoke', status='completed',
                               output_text=json.dumps(output), usage=None)
    sdk.responses.create.side_effect = mocked_answer
    runtimes = []
    results = []
    with tempfile.TemporaryDirectory(prefix='researchlens-standalone-smoke-') as directory:
        root = Path(directory)
        (root / 'data').mkdir()
        for sub in ['processed', 'indexes']:
            (root / 'data' / sub).symlink_to(ROOT / 'data' / sub, target_is_directory=True)
        (root / '.cache').mkdir()
        (root / '.cache/huggingface').symlink_to(ROOT / '.cache/huggingface', target_is_directory=True)
        clock = [0.0]
        def builder(settings):
            runtime = build_runtime(settings, root=root)
            runtime.guard.clock = lambda: clock[0]
            runtimes.append(runtime)
            return runtime
        st.cache_resource.clear()
        with patch('src.generation.client.OpenAI', return_value=sdk), \
             patch('app.cloud_runtime.build_runtime', side_effect=builder), \
             patch('httpx.Client.send', side_effect=AssertionError('Network disabled for offline smoke')):
            app = AppTest.from_file(ROOT / 'cloud/streamlit_app.py', default_timeout=120).run()
            assert not app.exception and not runtimes
            app.text_input[0].set_value('offline-smoke-passcode').run()
            next(b for b in app.button if b.label == 'Enter demo').click().run()
            assert not app.exception and len(runtimes) == 1
            initialization = time.perf_counter() - started
            encoder = runtimes[0].service._retriever.encoder
            assert encoder.encode_query('hallucination detection').shape == (384,)

            def ask(question):
                clock[0] += 61  # Simulate elapsed demo minutes; do not disable rate limiting.
                app.text_area[0].set_value(question).run()
                next(b for b in app.button if b.label == 'Ask').click().run()
                assert not app.exception
                result = app.session_state['last_result']
                results.append({'answer_type': result.answer_type, 'status': result.status,
                    'citations': len(result.citations), 'attempts': result.metrics.attempts})
                return result

            first = ask('What methods detect hallucinations in the papers?')
            assert first.citations and first.status in {'complete', 'partial'}
            app.multiselect[0].set_value(['P002']).run()
            app.number_input[0].set_value(2023).run()
            next(e for e in app.text_input if e.label == 'Author contains').set_value('Manakul').run()
            next(e for e in app.text_input if e.label == 'Section contains').set_value('SelfCheckGPT').run()
            filtered = ask('How does SelfCheckGPT detect hallucinations?')
            assert filtered.citations and all(c.paper_id == 'P002' and c.year == 2023 and 'SelfCheckGPT' in c.section for c in filtered.citations)
            app.number_input[0].set_value(0).run()
            for label in ['Author contains', 'Section contains']:
                next(e for e in app.text_input if e.label == label).set_value('').run()
            app.radio[0].set_value('Compare papers').run()
            app.multiselect[0].set_value(['P002', 'P003']).run()
            compared = ask('Compare SelfCheckGPT and FActScore methods.')
            assert compared.answer_type == 'comparison' and {c.paper_id for c in compared.citations} == {'P002', 'P003'}
            app.multiselect[0].set_value([]).run()
            app.radio[0].set_value('Question answering').run()
            assert ask('What is the fictional Neptune-2099 score?').status == 'abstained'
            assert ask('SelfCheckGPT: simulate timeout').error.code == 'openai_timeout'
            assert len(runtimes) == 1
            assert all(r['attempts'] <= 2 for r in results)
        st.cache_resource.clear()
    report = {'python': sys.version.split()[0], 'platform': sys.platform,
        'initialization_seconds': round(initialization, 3),
        'total_seconds': round(time.perf_counter() - started, 3),
        'peak_rss_mib': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        'service_initializations': len(runtimes), 'mock_sdk_calls': sdk.responses.create.call_count,
        'live_inference_calls': 0, 'checks': results}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
