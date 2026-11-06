# Standalone Streamlit Community Cloud deployment

Prepared on `feature/streamlit-cloud` from deployment commit `427c0c2`.
**No public application is deployed yet.** Oracle registration is not required for
this mode. The existing HTTP frontend, FastAPI backend and Oracle templates remain
available as an alternative.

## Architecture and feasibility

```text
Browser → Community Cloud Streamlit → DirectResearchClient → ResearchService
  → ResearchGenerator → BM25 + BGE + NumPy/RRF → OpenAI → citation validation
```

`cloud/streamlit_app.py` imports and reuses `app/streamlit_app.py`'s complete UI.
The UI accepts an optional client factory; the default still uses HTTP. The direct
adapter implements `health`, `papers`, `ask` and `record_feedback` by delegating to
the existing service. It does not duplicate interpretation, retrieval, generation,
repair or citation logic. No FastAPI/Uvicorn server is started in standalone mode.
FastAPI is still a Python dependency because the shared demo guard uses its safe
HTTPException type; Streamlit also has server-related dependencies of its own.

One global `st.cache_resource` holds a service and allowance guard across users and
reruns. `ResearchService` loads the corpus, NumPy matrix, BM25 and CPU BGE once,
warms a query once and serializes generation with its existing lock. A cached SDK
owner is reused; each question retains its own maximum **two inference attempts**.
Cache release closes the service. Startup failures are safe UI errors, never
answers from model memory. No category filter or debugging API panel is added.

Previously separate-server assumptions are addressed as follows:

| Existing HTTP deployment | Standalone mode |
|---|---|
| API URL and health/catalog HTTP calls | Direct service health/catalog calls |
| Shared HTTP Bearer token | Private server-checked attendee passcode, expiry, local allowance |
| API startup warms retrieval | First authorized session initializes a globally cached service |
| Backend holds provider credentials | Cloud server holds `OPENAI_API_KEY` in secrets |
| Persistent Oracle feedback/budget paths | Local ephemeral Cloud files, explicitly not durable |
| Generated files absent from Git checkout | Verified versioned bundle downloaded on cold start |

A fresh Python 3.11.17 environment installed `cloud/requirements.txt` successfully;
CPU torch 2.15.0+cpu was loaded with no CUDA, PDF ingestion or vector-database
packages. The standalone UI plus real retrieval, with mocked provider calls,
peaked at **696.3 MiB RSS** in the clean environment (4.827 s initialization).
The existing environment measured 716.4 MiB. A separate actual Streamlit server
process, driven through a local WebSocket session and loading the real service,
peaked at **690.2 MiB during initialization**, about 4.70 s. This last measurement
covers startup, not sustained questions or many live clients. Artifact network
download time was excluded; local caches/weights were available.

These measurements make a trial reasonable; **they do not guarantee free-cloud
compatibility**. Native imports, model loading, archive extraction, request/session
buffers and package installation need headroom. There is no fixed RAM allowance
verified here for your account. Check Cloud resource/build logs. Streamlit documents
[resource-limit failures](https://docs.streamlit.io/knowledge-base/deploy/resource-limits)
and recommends caching/profiling; an educational resource increase can be requested
if appropriate. Do not change the embedding model or RAG architecture to hide an
out-of-memory failure. Keep concurrency low; if hosting fails, report that limit.

## Dependencies and entrypoint discovery

Choose **`cloud/streamlit_app.py`**, with **Python 3.11**. Community Cloud searches
[the entrypoint directory before the repository root](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
so it will find **`cloud/requirements.txt`**, not frontend-only `app/requirements.txt`.
The file includes the pinned existing backend runtime and frontend requirements,
plus direct official Linux CPython-3.11 CPU torch wheel URLs with SHA256 fragments.
There is no GPU/CUDA extra index. `cloud/packages.txt` supplies `libgomp1`.

No PDF extraction or ingestion is run. NumPy/BM25 and the exact BGE model/revision
are preserved; no vector database is introduced. The Debian Cloud environment is
expected to support manylinux_2_28 wheels, but actual hosted installation remains
an acceptance check. See [Cloud environment details](https://docs.streamlit.io/deploy/streamlit-community-cloud/status).

## Publish the existing runtime bundle manually

The repository is publicly readable, but its release listing had **no runtime
assets** at review time. No artifact was published by this work. Do not put the
bundle/model/index into ordinary Git history.

The existing local bundle is:

```text
tmp/researchlens-runtime.tar.gz
tmp/researchlens-runtime.tar.gz.sha256
```

SHA256:

```text
2ece5bf14990e4ab0189180161f4d0b031cc5c9b9f45e77caeafafd840650dc2
```

On your laptop, verify it first:

```bash
cd /home/asma/Documents/ResearchLens
.venv/bin/python scripts/runtime_artifacts.py verify \
  --archive tmp/researchlens-runtime.tar.gz \
  --sha256 2ece5bf14990e4ab0189180161f4d0b031cc5c9b9f45e77caeafafd840650dc2
```

GitHub browser steps:

1. Open `yousefsassy/ResearchLens` → **Releases → Draft a new release**.
2. Create a new tag **`researchlens-runtime-v1`**, targeting `feature/deployment`
   at the artifact preparation commit `427c0c2`. Do not move an existing release tag.
3. Title: `ResearchLens runtime v1`. Describe the unchanged 1,001-chunk corpus,
   pinned BGE model/revision and the SHA256 above.
4. Attach **both files** listed above. Publish the release (not only a draft).
5. Copy the actual **download link for the .tar.gz release asset**, not the release
   page/source-code archive. Verify that link downloads without GitHub login.
   Put this real link in `RESEARCHLENS_ARTIFACT_URL`. No download URL is assumed.

If you use GitHub CLI, the equivalent explicit manual publication is:

```bash
gh auth login
# Run only when you intend to create the public runtime release:
gh release create researchlens-runtime-v1 \
  tmp/researchlens-runtime.tar.gz tmp/researchlens-runtime.tar.gz.sha256 \
  --repo yousefsassy/ResearchLens \
  --target 427c0c209808284b43d9fb5ed328d58d57433d5c \
  --title 'ResearchLens runtime v1' \
  --notes 'Pinned BGE runtime, 1001 chunks. Verify the attached SHA256 before extraction.'
gh release view researchlens-runtime-v1 --repo yousefsassy/ResearchLens --json assets
```

If the laptop bundle is gone, restore the agreed cache/corpus/index, then run
`scripts/runtime_artifacts.py pack --archive tmp/researchlens-runtime-v2.tar.gz`.
Record the **new** printed SHA256 and publish a new version; never assume a
repacked archive has the old hash. Do not recreate embeddings to fill missing data.
Do not substitute a different corpus or model.

## Required Community Cloud settings and secrets

Open **https://share.streamlit.io**, sign in with the GitHub account authorized to
deploy this repository, then **Create app / Deploy from GitHub**:

| Setting | Value |
|---|---|
| Repository | `yousefsassy/ResearchLens` |
| Branch | `feature/streamlit-cloud` |
| Main file | `cloud/streamlit_app.py` |
| Advanced settings → Python | **3.11** |
| Secrets | Fill `cloud/secrets.toml.example` as described below |

Root-level TOML keys become server environment variables through
[Streamlit secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management).
Required values:

```toml
OPENAI_API_KEY = "<YOUR_DEDICATED_PROVIDER_KEY>"
RESEARCHLENS_DEMO_PASSWORD = "<PRIVATE_RANDOM_PASSCODE_AT_LEAST_12_CHARACTERS>"
RESEARCHLENS_DEMO_EXPIRES_AT = "<REAL_EVENT_END_YYYY-MM-DDTHH:MM:SSZ>"
RESEARCHLENS_CLOUD_MAX_QUESTIONS = "20"
RESEARCHLENS_ARTIFACT_URL = "<ACTUAL_PUBLIC_HTTPS_RELEASE_ASSET_DOWNLOAD_LINK>"
RESEARCHLENS_ARTIFACT_SHA256 = "2ece5bf14990e4ab0189180161f4d0b031cc5c9b9f45e77caeafafd840650dc2"
```

Replace every placeholder. Choose a short demonstration window with an explicit
UTC end. Generate the passcode privately, e.g. `python3 -c 'import secrets;
print(secrets.token_urlsafe(24))'`. Use a dedicated provider project/key and monitor
billing. Never paste secrets into GitHub code, issue comments, application questions
or screenshots. `RESEARCHLENS_API_URL` and the shared HTTP API token are unused.
Do **not** set `RESEARCHLENS_USE_LOCAL_ARTIFACTS` on Community Cloud.

Click Deploy. Record the **actual assigned HTTPS URL** after it is healthy. This
repository does not invent or claim that URL. Cloud continues running independently
of your laptop, subject to hosting sleep/reboot/resource policies.

## Initialization and artifact validation

Before model initialization, the app checks key/passcode/expiry configuration.
The passcode gate prevents unauthenticated visitors initializing the runtime.
The first authorized visitor sees an initialization spinner:

1. Stream the HTTPS bundle to an ignored temporary directory, bounded to 512 MiB;
   HTTPS redirects are allowed, HTTPS-to-HTTP redirects are rejected.
2. Validate the trusted outer archive SHA256 **before extraction**.
3. Validate the manifest, per-file hashes, regular-file/path whitelist and complete
   pinned snapshot using the existing artifact utility; unsafe archives fail closed.
4. Restore the unchanged corpus/index/cache. Validate corpus fingerprint,
   model/revision, ordered chunk IDs, index file hash, **(1001,384) float32** shape,
   finite normalized vectors and metadata with the existing loader.
5. Load BGE offline on CPU and warm once via the existing service.

The canonical corpus fingerprint is
`3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
BGE is `BAAI/bge-small-en-v1.5`, revision
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.

No vectors are regenerated and no alternate model is selected. The cache resource
avoids downloads/model loads on page reruns or new sessions. After process restart,
a surviving local archive is reverified and reused; after disk loss/cold deployment,
it is downloaded again. This requires the public asset to remain accessible.
A cached archive with a bad hash or differing existing runtime files is rejected;
do not overwrite a live mixed index/corpus. Reprovision a clean app filesystem if
restored content differs. The model-cache file links in the laptop bundle were
already dereferenced into regular files.

## Demo controls and feedback: exact persistence limits

- Private passcode required (minimum 12 characters). Authorization is server-side;
  it gates the UI and is rechecked before every ask/feedback call. The OpenAI key
  is only used on the Streamlit server and is never rendered or sent to browsers.
- Required fixed UTC expiry blocks requests even if an old session/runtime remains
  cached. Missing/invalid/expired configuration fails closed.
- Global **3 asks/minute** and **20 feedback submissions/minute**, shared across
  sessions in this one process. Service generation is serialized. Extra simultaneous
  questions can return the existing safe `service_busy` result.
- Default **20 admitted questions** (configurable 1–100), counted before service
  execution, including failures. Maximum two provider attempts per question.
  No automatic POST/semantic repair loop beyond the existing bounded repair.
- The budget JSON is atomic and shared across sessions at
  `data/demo/cloud-budget.json`. It survives process restart **only if local disk
  survives**. It may reset on Cloud rebuild/redeployment/eviction. Rate counters
  reset on process restart. **There is no durable global or dollar spend cap.**
  Repeated cold starts can reopen an allowance; do not treat 20×2 as an account-wide
  lifetime limit. Restrict the audience, use a short event expiry, monitor provider
  billing and stop the app/revoke its key after the demo. Do not publish the passcode
  alongside the public URL. A permanent public service would need durable accounting.
- Feedback remains append-only/idempotent JSONL at
  `data/feedback/cloud-feedback.jsonl`, without a new database. It can be lost on
  Cloud redeployment. Do not claim permanent retention or collect sensitive comments.

Restart/reboot the app after changing keys, passcode or runtime settings so cached
resources and old sessions are replaced. Changing the question allowance is an
explicit administrator action, not an automatic budget reset.

## Local verification and future public checks

Complete offline tests:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
git diff --check
# Real local artifacts + complete UI, provider mocked and network blocked:
.venv/bin/python scripts/smoke_streamlit_cloud.py --report tmp/cloud-smoke.json
```

A fresh installation was tested using `python3.11 -m venv <NEW_VENV>` and
`<NEW_VENV>/bin/pip install -r cloud/requirements.txt`, then the same smoke script.
The smoke uses temporary budget/feedback paths, a fake key and mocked SDK; it
makes no paid inference calls and is **not a generation-quality benchmark**.

For an interactive laptop trial with existing trusted artifacts, export
`OPENAI_API_KEY`, a private `RESEARCHLENS_DEMO_PASSWORD`, future UTC
`RESEARCHLENS_DEMO_EXPIRES_AT`, and `RESEARCHLENS_USE_LOCAL_ARTIFACTS=true`, then:

```bash
.venv/bin/python -m streamlit run cloud/streamlit_app.py
```

A real Ask in that interactive trial is billable. Root `.env` is not used to
satisfy the cloud preflight: explicitly supply secrets/environment. Never commit a
populated secrets file; existing `.streamlit/secrets.toml` is ignored.

After manual Cloud deployment, verify the actual public HTTPS URL, passcode gate,
eight-paper selector and initialization. With explicit spending approval, ask one
question, one comparison and an unsupported query; check references/pages/quotes
and optional filters, then send feedback. Test an expired event end separately to
confirm generation is blocked. Do not rerun the full 117-question benchmark.

## Troubleshooting

| Failure | Action |
|---|---|
| Missing passcode/key/expiry | Fill root-level Cloud secrets; choose a future UTC end and restart. The error never includes the secret value. |
| Artifact configuration error | Publish the real release asset, copy its anonymous HTTPS download link and exact SHA256. Release page/source ZIP URLs are incorrect. |
| Checksum/index mismatch | Verify laptop hash and coherent corpus/index/model; do not regenerate vectors or reuse a hash from a different pack. |
| Existing files differ | Start with a clean Cloud app filesystem and the correct versioned bundle; do not mix snapshots. |
| torch/CUDA install problem | Confirm Python 3.11 and `cloud/streamlit_app.py`; its neighboring requirements use official CPU wheel URLs. Do not select `app/streamlit_app.py` for standalone mode. |
| Model/cache unavailable | Check the pinned full snapshot and offline initialization error. No automatic model download fallback is enabled. |
| Memory/resource limit | Inspect Cloud logs, reduce audience/concurrency, measure again; request educational capacity if available. Do not silently replace BGE. |
| Rate/allowance exhausted | Wait for the minute window or have the owner review billing and settings. Rebooting can lose counters; it is not a safe budget-management policy. |
| Startup spinner is slow | Cold download/native import/model loading is expected; later page reruns reuse the global resource. Network latency is not covered by local timings. |
| Feedback lost | Local Cloud storage is ephemeral; preserve only as a convenience for this demo. |
| Provider timeout/invalid output | Existing safe error/repair handling applies; no automatic retry from the UI. Inspect usage before manually retrying. |

See [verification results](streamlit_cloud_verification.md). The remaining manual
blockers are publishing the runtime asset, configuring secrets and deploying the
app through your Streamlit/GitHub accounts; hosted resource compatibility and the
actual public URL remain unverified.
