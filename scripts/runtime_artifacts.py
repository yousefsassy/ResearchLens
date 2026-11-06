#!/usr/bin/env python3
"""Pack/verify/restore prebuilt runtime data. Verification requires a trusted SHA256.

Only `check` imports ML packages. No command builds an index or calls OpenAI.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('data/processed/chunks.jsonl', 'data/indexes/embeddings.npy',
         'data/indexes/index_metadata.json')
MODEL = 'BAAI/bge-small-en-v1.5'
REVISION = '5c38ec7c405ec4b44b94cc5a9bb96e735b38267a'
CACHE = '.cache/huggingface/models--BAAI--bge-small-en-v1.5'
FINGERPRINT = '3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83'
MAX_BYTES = 2 * 1024 ** 3


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def allowed(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p) != name:
        return False
    if name in FILES:
        return True
    if not name.startswith(CACHE + '/'):
        return False
    # Include the pinned snapshot and any standard cache refs/blobs, never other revisions.
    rest = p.relative_to(CACHE).parts
    return ((len(rest) >= 3 and rest[:2] == ('snapshots', REVISION)) or
            (len(rest) == 2 and rest[0] in {'blobs', 'refs'})) and not any(
                part.startswith('.') or part in {'token', 'tokens', 'credentials'} for part in rest)


def check(root, smoke=False):
    sys.path.insert(0, str(ROOT))
    from src.retrieval.common import load_chunks
    from src.retrieval.config import RetrievalConfig
    from src.retrieval.embeddings import load_index
    config = RetrievalConfig(chunks_path=root / FILES[0], index_dir=root / 'data/indexes',
                             model_cache_dir=root / '.cache/huggingface', device='cpu')
    matrix, metadata = load_index(load_chunks(config.chunks_path), config)
    # load_index verifies the corpus fingerprint against the index metadata.
    if matrix.shape != (1001, 384):
        raise ValueError('Unexpected production index shape')
    # Use the same canonical fingerprint implementation as retrieval.
    from src.retrieval.common import corpus_fingerprint
    if corpus_fingerprint(load_chunks(config.chunks_path)) != FINGERPRINT:
        raise ValueError('Unexpected production corpus fingerprint')
    if smoke:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        from src.retrieval.retriever import ResearchRetriever
        retriever = ResearchRetriever(config)
        results = retriever.search('How does SelfCheckGPT detect hallucinations?',
            top_k=3, mode='hybrid', rerank=False, paper_ids=['P002'], exclude_flagged=True)
        if not results or any(p['paper_id'] != 'P002' for p in results):
            raise ValueError('Filtered hybrid retrieval failed')
    return {'shape': list(matrix.shape), 'fingerprint': FINGERPRINT,
            'model': MODEL, 'revision': REVISION, 'retrieval_smoke': smoke}


def pack(root, archive):
    info = check(root)
    model_dir = (root / CACHE).resolve(strict=True)
    snapshot = model_dir / 'snapshots' / REVISION
    if not (snapshot / 'model.safetensors').is_file():
        raise ValueError('Pinned model snapshot is missing')
    paths = {name: root / name for name in FILES}
    for directory, dirs, names in os.walk(model_dir, followlinks=False):
        if any((Path(directory) / d).is_symlink() for d in dirs):
            raise ValueError('Directory symlinks within the model cache are not supported')
        for filename in names:
            path = Path(directory) / filename
            name = CACHE + '/' + path.relative_to(model_dir).as_posix()
            if not allowed(name):
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(model_dir) or not resolved.is_file():
                raise ValueError('Model cache link escapes the selected model directory')
            paths[name] = resolved
    manifest = {**info, 'format': 1, 'files': {
        name: {'sha256': digest(path), 'size': path.stat().st_size}
        for name, path in sorted(paths.items())}}
    if archive.exists():
        raise ValueError('Archive already exists; choose a new output filename')
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'w:gz', dereference=True) as tar:
        content = json.dumps(manifest, sort_keys=True, indent=2).encode()
        item = tarfile.TarInfo('MANIFEST.json')
        item.size, item.mode = len(content), 0o644
        tar.addfile(item, io.BytesIO(content))
        for name, path in sorted(paths.items()):
            item = tar.gettarinfo(str(path), arcname=name)
            item.uid = item.gid = 0
            item.uname = item.gname = ''
            item.mode = 0o644
            with path.open('rb') as stream:
                tar.addfile(item, stream)
    sha = digest(archive)
    archive.with_name(archive.name + '.sha256').write_text(sha + '  ' + archive.name + '\n')
    verify(archive, sha)
    return {'archive': str(archive), 'sha256': sha, 'files': len(paths), **info}


def verify(archive, expected):
    if len(expected) != 64 or digest(archive) != expected.lower():
        raise ValueError('Archive checksum does not match the trusted SHA256')
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        if len(members) > 5000 or sum(m.size for m in members) > MAX_BYTES:
            raise ValueError('Archive exceeds size limits')
        names = [m.name for m in members]
        if len(names) != len(set(names)) or any(not m.isfile() or m.size < 0 for m in members):
            raise ValueError('Archive must contain unique regular files only')
        if 'MANIFEST.json' not in names or any(n != 'MANIFEST.json' and not allowed(n) for n in names):
            raise ValueError('Archive contains an unexpected path')
        if tar.getmember('MANIFEST.json').size > 1024 * 1024:
            raise ValueError('Manifest too large')
        manifest = json.load(tar.extractfile('MANIFEST.json'))
        if (manifest.get('format') != 1 or manifest.get('model') != MODEL or
                manifest.get('revision') != REVISION or manifest.get('fingerprint') != FINGERPRINT):
            raise ValueError('Unexpected runtime identity')
        records = manifest['files']
        if set(records) != set(names) - {'MANIFEST.json'} or not set(FILES).issubset(records):
            raise ValueError('Manifest file list differs from archive')
        required = CACHE + '/snapshots/' + REVISION + '/'
        for filename in ['model.safetensors', 'config.json', 'modules.json', 'tokenizer.json',
                         'tokenizer_config.json', '1_Pooling/config.json']:
            if required + filename not in records:
                raise ValueError('Pinned model snapshot incomplete')
        for name, record in records.items():
            stream = tar.extractfile(name)
            if tar.getmember(name).size != record['size'] or hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                raise ValueError('File checksum mismatch')
    return manifest


def restore(root, archive, expected):
    manifest = verify(archive, expected)  # Check everything before writing any destination file.
    root = root.resolve(strict=True)
    # Refuse symlink destinations, including the laptop's RAM cache link.
    for name, record in manifest['files'].items():
        destination = root / name
        if any(p.is_symlink() for p in (destination, *destination.parents) if p.is_relative_to(root)):
            raise ValueError('Destination contains a symlink; use a fresh server checkout')
        if destination.exists() and (not destination.is_file() or digest(destination) != record['sha256']):
            raise ValueError('Destination contains different artifacts; stop service and back them up first')
    with tempfile.TemporaryDirectory(prefix='.runtime-', dir=root) as staging:
        with tarfile.open(archive, 'r:gz') as tar:
            for name in manifest['files']:
                target = Path(staging) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(name) as source, target.open('wb') as dest:
                    shutil.copyfileobj(source, dest)
        for name in manifest['files']:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                os.replace(Path(staging) / name, destination)
    return {'restored_files': len(manifest['files']), 'fingerprint': manifest['fingerprint']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['pack', 'verify', 'restore', 'check'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--sha256', help='Trusted SHA256 obtained on the source laptop')
    args = parser.parse_args()
    if args.command in {'pack', 'verify', 'restore'} and not args.archive:
        parser.error('--archive is required')
    if args.command in {'verify', 'restore'} and not args.sha256:
        parser.error('--sha256 is required; obtain it through a trusted channel')
    if args.command == 'pack': result = pack(args.root, args.archive)
    elif args.command == 'verify': result = verify(args.archive, args.sha256)
    elif args.command == 'restore': result = restore(args.root, args.archive, args.sha256)
    else: result = check(args.root, smoke=True)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
