"""Download/bootstrap tests use tiny archives and mocked public HTTPS transport."""
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from app import cloud_artifacts
from app.client import APIClientError
from scripts.runtime_artifacts import digest
from test_runtime_artifacts import bundle

URL = 'https://artifacts.example.invalid/runtime.tar.gz'


def client_for(content, status=200, **headers):
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        status, content=content, headers=headers)))


def test_download_restore_and_cold_restart_reuses_archive(tmp_path, monkeypatch):
    archive, sha = bundle(tmp_path)
    target = tmp_path / 'fresh-checkout'
    target.mkdir()
    check = Mock(return_value={'shape': [1001, 384]})
    monkeypatch.setattr(cloud_artifacts, 'check', check)
    http = client_for(archive.read_bytes())
    assert cloud_artifacts.ensure_runtime(target, URL, sha, client=http)['shape'] == [1001, 384]
    cached = target / 'tmp/cloud-artifacts' / (sha + '.tar.gz')
    assert digest(cached) == sha
    with monkeypatch.context() as local:
        local.setattr(cloud_artifacts, 'download', Mock(side_effect=AssertionError('Unexpected redownload')))
        cloud_artifacts.ensure_runtime(target, URL, sha)
    assert check.call_count == 2


def test_bad_checksum_leaves_no_extracted_artifacts(tmp_path, monkeypatch):
    archive, _ = bundle(tmp_path)
    target = tmp_path / 'fresh'
    target.mkdir()
    check = Mock()
    monkeypatch.setattr(cloud_artifacts, 'check', check)
    with pytest.raises(APIClientError):
        cloud_artifacts.ensure_runtime(target, URL, '0' * 64, client=client_for(archive.read_bytes()))
    assert not (target / 'data').exists()
    assert list((target / 'tmp/cloud-artifacts').iterdir()) == []
    check.assert_not_called()


@pytest.mark.parametrize('url,sha', [('', ''), ('http://example.invalid/a', '0' * 64),
    ('https://private:secret@example.invalid/a', '0' * 64), (URL, 'bad')])
def test_invalid_config_never_downloads(tmp_path, monkeypatch, url, sha):
    download = Mock()
    monkeypatch.setattr(cloud_artifacts, 'download', download)
    with pytest.raises(APIClientError) as exc:
        cloud_artifacts.ensure_runtime(tmp_path, url, sha)
    download.assert_not_called()
    assert 'secret' not in str(exc.value)


def test_http_failure_and_redirect_downgrade_are_sanitized(tmp_path):
    for http in [client_for(b'provider-private-body', status=403),
                 client_for(b'', status=302, location='http://bad.invalid/private')]:
        with pytest.raises(APIClientError) as exc:
            cloud_artifacts.ensure_runtime(tmp_path, URL+'?private-signature', '0' * 64, client=http)
        assert 'private' not in str(exc.value) and '403' not in str(exc.value)


def test_size_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(cloud_artifacts, 'MAX_DOWNLOAD', 5)
    with pytest.raises(APIClientError):
        cloud_artifacts.ensure_runtime(tmp_path, URL, '0' * 64, client=client_for(b'exceeds-limit'))
    assert not (tmp_path / 'data').exists()


def test_corrupt_existing_cache_and_index_fail_closed(tmp_path, monkeypatch):
    archive, sha = bundle(tmp_path)
    check = Mock(side_effect=ValueError('matrix dtype or fingerprint invalid'))
    monkeypatch.setattr(cloud_artifacts, 'check', check)
    target = tmp_path / 'fresh'
    target.mkdir()
    with pytest.raises(APIClientError):
        cloud_artifacts.ensure_runtime(target, URL, sha, client=client_for(archive.read_bytes()))
    check.assert_called_once()
    cached = target / 'tmp/cloud-artifacts' / (sha + '.tar.gz')
    cached.write_bytes(b'corrupt')
    with pytest.raises(APIClientError): cloud_artifacts.ensure_runtime(target, URL, sha)


def test_explicit_local_mode_requires_pinned_model_and_valid_index(tmp_path, monkeypatch):
    check = Mock()
    monkeypatch.setattr(cloud_artifacts, 'check', check)
    with pytest.raises(APIClientError): cloud_artifacts.ensure_runtime(tmp_path, '', '', use_local=True)
    check.assert_not_called()
