"""Small synthetic archives exercise integrity and extraction without model downloads."""
import hashlib
import io
import json
from pathlib import Path
import tarfile

import pytest

from scripts import runtime_artifacts as artifacts


def bundle(tmp_path, *, extra=None, link=False, corrupt=False):
    files = {name: b'fixture' for name in artifacts.FILES}
    prefix = artifacts.CACHE + '/snapshots/' + artifacts.REVISION + '/'
    for name in ['model.safetensors', 'config.json', 'modules.json', 'tokenizer.json',
                 'tokenizer_config.json', '1_Pooling/config.json']:
        files[prefix + name] = b'fixture'
    manifest = {'format': 1, 'model': artifacts.MODEL, 'revision': artifacts.REVISION,
                'fingerprint': artifacts.FINGERPRINT, 'files': {
                    name: {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
                    for name, data in files.items()}}
    if corrupt:
        files[artifacts.FILES[0]] = b'changed'
    files['MANIFEST.json'] = json.dumps(manifest).encode()
    if extra: files[extra] = b'bad'
    archive = tmp_path / 'fixture.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            if link and name == artifacts.FILES[0]:
                member.type = tarfile.SYMTYPE
                member.linkname = '/etc/passwd'
                member.size = 0
                tar.addfile(member)
            else:
                tar.addfile(member, io.BytesIO(data))
    return archive, artifacts.digest(archive)


def test_verify_restore_regular_files_and_idempotence(tmp_path):
    archive, sha = bundle(tmp_path)
    manifest = artifacts.verify(archive, sha)
    target = tmp_path / 'target'
    target.mkdir()
    artifacts.restore(target, archive, sha)
    artifacts.restore(target, archive, sha)
    for name, record in manifest['files'].items():
        assert artifacts.digest(target / name) == record['sha256']
        assert not (target / name).is_symlink()


@pytest.mark.parametrize('extra', ['../escape', '/etc/passwd', '.env', 'data/feedback/a',
                                 '.cache/huggingface/token', artifacts.CACHE + '/snapshots/wrong/config.json'])
def test_forbidden_members_rejected_before_extraction(tmp_path, extra):
    archive, sha = bundle(tmp_path, extra=extra)
    target = tmp_path / 'target'
    target.mkdir()
    with pytest.raises(ValueError): artifacts.restore(target, archive, sha)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize('kwargs', [{'link': True}, {'corrupt': True}])
def test_link_or_corrupt_member_rejected(tmp_path, kwargs):
    archive, sha = bundle(tmp_path, **kwargs)
    with pytest.raises(ValueError): artifacts.verify(archive, sha)


def test_untrusted_archive_checksum_rejected(tmp_path):
    archive, _ = bundle(tmp_path)
    with pytest.raises(ValueError, match='trusted'): artifacts.verify(archive, '0' * 64)


def test_restore_rejects_symlink_destination_and_different_files(tmp_path):
    archive, sha = bundle(tmp_path)
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'data').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'): artifacts.restore(target, archive, sha)
    (target / 'data').unlink()
    file = target / artifacts.FILES[0]
    file.parent.mkdir(parents=True)
    file.write_text('other')
    with pytest.raises(ValueError, match='different'): artifacts.restore(target, archive, sha)
    assert file.read_text() == 'other'


def test_pack_dereferences_real_cache_links_and_uses_whitelist(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, 'check', lambda root: {'model': artifacts.MODEL,
        'revision': artifacts.REVISION, 'fingerprint': artifacts.FINGERPRINT})
    root = tmp_path / 'source'
    root.mkdir()
    for name in artifacts.FILES:
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b'fixture')
    actual_cache = tmp_path / 'actual-cache'
    actual_cache.mkdir()
    cache = root / artifacts.CACHE
    cache.parent.mkdir(parents=True)
    cache.symlink_to(actual_cache, target_is_directory=True)
    snapshot = actual_cache / 'snapshots' / artifacts.REVISION
    for name in ['config.json', 'modules.json', 'tokenizer.json', 'tokenizer_config.json', '1_Pooling/config.json']:
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}')
    blob = actual_cache / 'blobs' / 'hash'
    blob.parent.mkdir()
    blob.write_bytes(b'weights')
    (snapshot / 'model.safetensors').symlink_to('../../blobs/hash')
    (root / '.env').write_text('SECRET=do-not-bundle')
    (actual_cache / 'token').write_text('do-not-bundle')
    archive = tmp_path / 'output.tar.gz'
    result = artifacts.pack(root, archive)
    manifest = artifacts.verify(archive, result['sha256'])
    assert all(artifacts.allowed(name) for name in manifest['files'])
    with tarfile.open(archive) as tar:
        member = tar.getmember(artifacts.CACHE + '/snapshots/' + artifacts.REVISION + '/model.safetensors')
        assert member.isfile() and not member.issym()
