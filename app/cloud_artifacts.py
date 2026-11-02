"""Provision a public, versioned runtime bundle once per cached cloud runtime."""
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

import httpx

from app.client import APIClientError
from scripts.runtime_artifacts import CACHE, REVISION, check, digest, restore

MAX_DOWNLOAD = 512 * 1024 * 1024


def _https_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Artifact URL must be public HTTPS')
    return value


def download(url, destination, *, client=None):
    """Bounded streamed download; reject HTTPS-to-HTTP redirects and never log URLs."""
    owned = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(45, connect=10), follow_redirects=False)
    try:
        for _ in range(6):
            _https_url(url)
            with client.stream('GET', url, follow_redirects=False) as response:
                if response.is_redirect:
                    from urllib.parse import urljoin
                    url = _https_url(urljoin(url, response.headers['location']))
                    continue
                response.raise_for_status()
                total = 0
                with destination.open('wb') as output:
                    for block in response.iter_bytes(1024 * 1024):
                        total += len(block)
                        if total > MAX_DOWNLOAD:
                            raise ValueError('Runtime archive exceeds download size limit')
                        output.write(block)
                return
        raise ValueError('Too many artifact redirects')
    finally:
        if owned:
            client.close()


def ensure_runtime(root: Path, url: str, sha256: str, *, use_local=False, client=None):
    """Do not import the encoder or build vectors here. Caller caches this operation."""
    root = Path(root)
    staging = None
    try:
        if not use_local:
            _https_url(url)
            if not re.fullmatch(r'[0-9a-fA-F]{64}', sha256):
                raise ValueError('Configure a trusted archive checksum')
            archive_dir = root / 'tmp/cloud-artifacts'
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive = archive_dir / (sha256.lower() + '.tar.gz')
            if not archive.exists():
                with tempfile.NamedTemporaryFile(dir=archive_dir, delete=False) as temp:
                    staging = Path(temp.name)
                download(url, staging, client=client)
                if digest(staging) != sha256.lower():
                    raise ValueError('Downloaded archive checksum mismatch')
                os.replace(staging, archive)
                staging = None
            # Restore verifies outer SHA and every allowed member before any extraction.
            # On restart it accepts existing matching files, never mixed/different ones.
            restore(root, archive, sha256)
        snapshot = root / CACHE / 'snapshots' / REVISION
        for name in ['model.safetensors', 'config.json', 'modules.json', 'tokenizer.json',
                     'tokenizer_config.json', '1_Pooling/config.json']:
            if not (snapshot / name).is_file():
                raise ValueError('Pinned BGE snapshot incomplete')
        return check(root)
    except Exception:
        # Public URLs may contain signatures. Never expose transport/provider/path details.
        raise APIClientError('Runtime artifacts are unavailable or invalid. Check the configured artifact URL, trusted SHA256 and matching corpus/index/model bundle.') from None
    finally:
        if staging is not None:
            staging.unlink(missing_ok=True)
