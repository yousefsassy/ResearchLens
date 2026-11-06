# Deployment readiness assessment — 2 November 2026

> Historical assessment from the integration branch. Deployment scripts, authentication
> and a persistent demo allowance have since been prepared. Use the current
> [deployment runbook](deployment.md), including its verified archive restore commands,
> instead of the illustrative tar commands below. No cloud deployment exists yet.

This is an assessment and manual handoff, not a deployment. No Oracle resources,
production configuration, public endpoint or hosting account was created. The
existing NumPy index and BM25 implementation are preserved. Hosting can be free;
OpenAI generation remains billable.

## Recommendation and outstanding gates

Prefer **Streamlit Community Cloud → HTTPS → Oracle A1 ARM VM → existing FastAPI**.
The frontend needs only Streamlit, HTTPX and Pydantic; BGE, the corpus/index and
OpenAI credentials stay on the VM. Current local warm retrieval peaked around
617 MiB RSS. An initial 2-OCPU/4-GB allocation provides reasonable prototype
headroom, subject to an ARM measurement, account allowance and shape availability.

Oracle's current [Always Free documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
lists 1,500 OCPU-hours and 9,000 GB-hours per month, equivalent to **2 OCPUs/12 GB**
for Always Free tenancies. Do not rely on older 4-OCPU/24-GB descriptions. Check
the tenancy console and aggregate existing resources before provisioning. Free
capacity may be unavailable, and idle instances can be reclaimed; retain backups.
Home-region and storage allowances apply to the whole tenancy.

**Not yet verified:** an actual ARM VM, a fully resolved ARM environment, remote
memory/latency, TLS/DNS, account capacity, or Community Cloud deployment. These
remain acceptance gates rather than assumed successes. No server exists in this
session on which to claim a completed target-runtime load test.

## Python and ARM64 assessment

Use Python 3.11 and an ARM Linux image with glibc >=2.28 (for example an appropriate
Ubuntu ARM64 image). The current x86 `.venv` and RAM-backed packages must **not**
be copied to ARM. Install fresh native wheels on the VM.

PyPI release metadata was checked for compatible CPython-3.11/ABI3 ARM64 wheels:

| Package | Version checked | Compatible wheel available |
|---|---|---|
| NumPy | 2.4.6 | Yes |
| SciPy / scikit-learn | 1.17.1 / 1.9.1 | Yes |
| tokenizers / safetensors | 0.23.3 / 0.8.0 | Yes |
| pydantic-core | 2.50.1 | Yes |
| PyMuPDF / PyMuPDF4LLM | 1.28.2 / 0.3.4 | ARM64 / universal |
| sentence-transformers | 5.7.0 | Universal |
| uvloop / httptools | 0.23.0 / 0.9.0 | Yes |

PyTorch 2.15.0 also has an ARM64 wheel, but use its **CPU build**. The official
[CPU wheel index](https://download.pytorch.org/whl/cpu/torch/) contains
`torch-2.15.0+cpu-cp311-cp311-manylinux_2_28_aarch64.whl`. Ordinary PyPI torch
metadata includes Linux CUDA dependencies, so do not blindly substitute it for
the locally verified CPU build. Wheel availability is not proof of a complete
dependency installation or runtime success; run the target checks below.

## Artifact portability and provisioning

The existing index is **1,001 x 384 normalized float32**, loaded using NumPy with
`allow_pickle=False`. NumPy's [NPY specification](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html)
stores shape/dtype information for loading across machine architectures. BGE's
Safetensors/tokenizer/config files are model data, not x86 native libraries.
Native Python dependencies must still match ARM.

Verified locally: copied the unchanged corpus, vector index and complete pinned
model directory to a fresh temporary location, dereferencing symlinks; loaded the
matrix with the existing validator and encoded a 384-dimensional query with BGE
in offline mode. This succeeded on **x86_64**, without API inference or rebuilding.
Repeat it on ARM before declaring the backend ready for public use.

Transfer these exact artifacts together, using SCP or a private versioned artifact
download, not a Git force-add:

```text
data/processed/chunks.jsonl
data/indexes/embeddings.npy
data/indexes/index_metadata.json
.cache/huggingface/models--BAAI--bge-small-en-v1.5/
```

The checked-in paper manifest and generation catalog come from the same Git commit.
Raw PDFs are not needed for current runtime citation rendering; provision them
separately only if needed for the demonstration. Do not copy `.env`, `.venv`, SSH
keys or user feedback into an artifact bundle.

After approval, an explicit packaging/transfer example is (workstation repository
root, then VM repository root; substitute the chosen SSH key/host):

```bash
tar -chzf /tmp/researchlens-runtime.tar.gz \
  data/processed/chunks.jsonl data/indexes/embeddings.npy \
  data/indexes/index_metadata.json \
  .cache/huggingface/models--BAAI--bge-small-en-v1.5
sha256sum /tmp/researchlens-runtime.tar.gz
scp -i PATH_TO_KEY /tmp/researchlens-runtime.tar.gz ubuntu@VM:/tmp/
# On VM: compare the archive SHA-256 with the workstation value before extracting.
# From the VM repository root:
tar -xzf /tmp/researchlens-runtime.tar.gz
```

The `-h` packaging option dereferences cache symlinks; do not archive the entire
repository. An archive checksum validates the included model files too. Use an
authenticated private artifact location instead of SCP if that is approved later.

Pinned BGE revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. Preserve the complete
HF cache layout, including snapshot configuration/tokenizer/pooling files and any
referenced blobs. Dereference existing symlinks when packaging: this workstation's
cache points into `/tmp`. The model weights are approximately 127 MiB.

Byte-level SHA-256 values of current runtime artifacts:

| File | Bytes | SHA-256 |
|---|---:|---|
| chunks.jsonl | 1811185 | `09584a03b374b2a8eaa6a6da76e966858b0003ac243fe50adfb9d8e54d4f2c1e` |
| embeddings.npy | 1537664 | `3f249d86c09f94f1d7ab820dd69d877d573e7df3c1a1430d692bcff7ae90ba8e` |
| index_metadata.json | 23398 | `93def738a697dee02962b995199e65a2eaece0974f61a7c03049a6135a3e00ac` |

Corpus fingerprint:
`3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
Transfer a SHA-256 inventory of model files with the bundle as well, then compare
it on the VM. Keep artifacts in persistent storage at the project-relative paths
above, or mount persistent directories there. The index metadata's recorded build
paths do not require using the workstation's absolute directory on the server.

Startup must **load, not regenerate**, the existing embedding index. BM25's small
in-memory keyword structure is initialized from the transferred chunks once per
process; that is not embedding regeneration. Enable `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1` after provisioning so startup cannot silently download
another snapshot. An incomplete cache should fail readiness. No replacement vector
database, ChromaDB, Qdrant, FAISS, or new embedding model is needed.

## Repository work needed after hosting approval

These changes are proposed, not implemented in this assessment:

1. Add a frontend-only `app/requirements.txt` with tested Streamlit/HTTPX/Pydantic
   pins. Community Cloud searches the entrypoint directory before the root. The
   current root requirements unnecessarily pull ML/ingestion packages for the UI;
   `requirements-web.txt` is not an automatically selected filename. See
   [dependency discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
2. Add a reproducible ARM backend dependency/CPU-torch constraint set, a runtime
   artifact checksum inventory, and a one-time provisioning/validation procedure.
3. Add service/proxy configuration only after the VM OS, DNS and access policy are
   chosen. Do not add model downloading/index rebuilding to the service startup.
4. Add an approved demo access policy before exposing funded inference. A backend
   shared token sent server-to-server and an appropriate viewer/demo restriction
   need small client/API changes; neither is currently implemented. HTTPS and CORS
   alone do not stop unauthorized API consumption or public-UI usage.

Streamlit's [root-level secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
are available as environment variables, so the existing `os.environ` API URL
reader is compatible. Configure `RESEARCHLENS_API_URL="https://<api-hostname>"`
in Community Cloud settings. Do not put `OPENAI_API_KEY` there for the split design.

## Manual cloud setup sequence, after approval

1. In OCI, select the home region, inspect free entitlement and existing usage,
   then choose an eligible A1 Flex ARM image/allocation. Start with one VM and
   one backend worker; do not accept a paid shape when free capacity is absent.
   Choose persistent boot/block storage within the tenancy allowance and save
   an SSH key. No such resources have been created here.
2. Create the network/subnet/internet routing required for the VM. Restrict SSH
   ingress to the administrator's IP. Later allow 80/443 for the TLS proxy in
   both OCI network rules and the OS firewall. Keep 8000 closed externally.
3. SSH to the VM, install Git, CA certificates, `libgomp1` on Ubuntu and an ARM
   Python 3.11 runtime. If the image lacks Python 3.11, use a supported managed
   installer (e.g. uv), then `uv python install 3.11` and
   `uv venv --python 3.11 --seed .venv`. Do not replace system Python.
4. Clone the reviewed `feature/full-integration` commit into the chosen service
   directory. In its fresh venv, preinstall CPU torch:
   `.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.15.0+cpu'`.
   Install the approved backend requirements with that torch constraint and run
   `pip check`. Current full `requirements-web.txt` is suitable for a compatibility
   trial, although it installs unnecessary frontend packages on the VM.
5. Copy the explicit artifact bundle once, preserving paths and dereferencing
   workstation symlinks. Check SHA-256 values, ownership and readable permissions.
   Do not transfer the x86 environment or configure per-start downloads.
6. Run the no-paid-call acceptance test below. Stop if any check fails; investigate
   mismatched artifacts/dependencies instead of silently regenerating the index.
7. Create a non-root service account. Set backend `OPENAI_API_KEY` in a protected,
   non-repository environment file (mode 0600), with offline HF settings,
   `OMP_NUM_THREADS=2` and `RESEARCHLENS_FEEDBACK_PATH` pointing to persistent storage.
   Create the feedback directory with write permission for that account.
8. Start Uvicorn bound to `127.0.0.1:8000`, explicitly `--workers 1`, managed by
   systemd with the repository as working directory and the protected environment
   file. Verify `/health` is 200 and `/papers` contains eight records. Health loads
   no paid probes; each question has its own two-attempt budget. Requests unable
   to acquire the inference lock within one second receive 503 `service_busy`.
9. Select a DNS name you control (or an approved free DNS hostname), point it at
   the VM public address and install a reverse proxy with a valid HTTPS certificate.
   A hostname/free-DNS choice is still outstanding. Proxy to loopback port 8000;
   allow at least 400 seconds upstream read timeout for generation. Test trusted
   HTTPS, readiness and the agreed access protection before connecting the UI.
10. In Community Cloud, connect the GitHub repository, select the pushed branch
    and `app/streamlit_app.py`, choose Python 3.11, and set the root-level API URL
    secret to the HTTPS hostname. Deploy only after the slim dependency file and
    access-policy changes are reviewed. The browser gets a `streamlit.app` URL;
    Streamlit's server sends HTTP requests to FastAPI, so this is not browser-side
    cross-origin inference. Keep TLS verification enabled.
11. Verify metadata controls and all response states with mocks first, then perform
    only an approved small live test. Back up corpus/index/cache and feedback,
    record the deployed commit and versions, and monitor demo usage. Document
    recovery from VM reclamation and ephemeral frontend restarts.

### Mandatory no-inference acceptance test on the ARM VM

Run from the checked-out repository after provisioning, with the venv active:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=2 \
.venv/bin/python - <<'PY'
import platform
from src.retrieval import ResearchRetriever
from src.retrieval.config import RetrievalConfig
from src.retrieval.embeddings import load_index
r = ResearchRetriever(RetrievalConfig(device="cpu"))
matrix, metadata = load_index(r.chunks, r.config)
assert platform.machine() in {"aarch64", "arm64"}
assert matrix.shape == (1001, 384) and str(matrix.dtype) == "float32"
assert metadata["corpus_fingerprint"] == "3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83"
hits = r.search("How does SelfCheckGPT work?", top_k=3, mode="hybrid",
                rerank=False, paper_ids=["P002"], exclude_flagged=True)
assert hits and all(hit["paper_id"] == "P002" for hit in hits)
assert r.encoder.encode_query("test query").shape == (384,)
print("ARM corpus/index/model load verified; no generation API call")
PY
```

## One-process Community Cloud fallback

This is **not the current HTTP-only frontend**. It would require an approved
alternate entrypoint calling `ResearchService` directly and the full ML runtime,
artifacts and backend key in that process. Do not switch the existing UI or its
architecture speculatively. The official current Community Cloud status page does
not establish a fixed RAM allowance sufficient for this model, and the measured
617-MiB backend excludes the full Streamlit process and cloud build overhead.
There is therefore no verified memory guarantee for this fallback. It also has
ephemeral feedback/cache risks and model cold starts. Evaluate actual cloud limits
and a no-inference memory smoke test before approval; prefer the split deployment.
If feasible later, persistent model/artifact provisioning must still avoid index
regeneration on every start. No database migration is warranted.
