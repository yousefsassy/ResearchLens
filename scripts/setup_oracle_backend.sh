#!/usr/bin/env bash
# Run as the dedicated researchlens user on Ubuntu ARM64, after OS provisioning.
set -euo pipefail
if [[ "$(uname -m)" != aarch64 || "$(id -u)" == 0 ]]; then
    echo 'Run as the non-root researchlens user on the target ARM64 VM.' >&2
    exit 1
fi
cd "$(dirname "$0")/.."
if [[ -e .venv ]]; then
    echo 'Existing .venv found. Refusing to reuse or replace it; inspect it first.' >&2
    exit 1
fi
# A pinned managed interpreter lives outside /home, visible to systemd ProtectHome.
command -v uv >/dev/null || { echo 'Install pinned uv as documented first.' >&2; exit 1; }
export UV_PYTHON_INSTALL_DIR="$PWD/.python"
uv python install 3.11.17
uv venv --seed --managed-python --python 3.11.17 .venv
.venv/bin/python -m pip install 'pip==26.2.2'
.venv/bin/python -m pip install --only-binary=:all: 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install --only-binary=:all: -r deploy/requirements-backend.txt
.venv/bin/python -m pip check
.venv/bin/python - <<'PY'
import platform
import fastapi, numpy, openai, sentence_transformers, torch, uvicorn
assert platform.machine() == 'aarch64'
assert torch.version.cuda is None
print('ARM64 CPU imports validated:', torch.__version__, numpy.__version__)
PY
printf '%s\n' 'Dependencies ready. Restore artifacts, then run scripts/runtime_artifacts.py check.'
