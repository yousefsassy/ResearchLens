# Standalone deployment verification — 2 November 2026

Base: `feature/deployment` at `427c0c209808284b43d9fb5ed328d58d57433d5c`.
Work isolated on `feature/streamlit-cloud`. No cloud app or release was published.
No live provider inference or 117-question benchmark was run.

| Check | Observed result |
|---|---|
| Complete offline suite | **415 passed** in 12.09 s; all original 388 tests retained |
| New tests | 17 standalone settings/service/UI tests and 10 download/provisioning tests |
| Existing HTTP deployment | Its API, auth, budget, feedback and UI regressions remain passing |
| Clean install | Fresh Python **3.11.17** environment installed `cloud/requirements.txt` successfully |
| CPU-only runtime | torch **2.15.0+cpu**, no CUDA; no PDF extraction/vector-database distributions |
| Dependency consistency | `pip check` clean in project and fresh standalone environments |
| Real retrieval + UI | Existing 1,001-chunk/384-dimension index; pinned BGE encoded a 384-vector; general QA, paper-specific QA with year/author/section filters and two-paper comparison rendered citations using mocked SDK responses |
| Failure/abstention | Mocked unsupported case abstained; actual SDK timeout type mapped to safe `openai_timeout`; authorization, event expiry, rate/budget and initialization failures tested |
| Resource reuse | One cached service/model initialization across reruns; multiple UI sessions share the cache; separate per-request attempt limits remain tested |
| No live inference | Offline smoke replaces the SDK and blocks HTTP transport; five mocked calls, zero paid calls |
| Artifact download | Mocked HTTPS download/redirect/errors, trusted SHA, malicious archive and restart-cache tests; existing artifact integrity/restore tests retained |
| Secret exposure | Real local provider key absent from tracked/proposed files; fake key absent from rendered UI; URLs/provider bodies sanitized; no runtime assets staged |
| Whitespace | `git diff --check` clean |

## Memory measurements

Linux x86_64, CPU, cached local weights and artifacts, no model download. Limits on
the eventual Cloud account remain unknown. Values are process peak RSS, not total
container memory including file cache, pip install, archive transfer or neighbors.

| Run | Initialization | Peak RSS | Extent |
|---|---:|---:|---|
| Existing project environment, standalone UI/AppTest + actual retrieval | 5.281 s | 716.4 MiB | Five mocked-generation UI scenarios |
| Fresh `cloud/requirements.txt` environment, same smoke | 4.827 s | 696.3 MiB | Same five scenarios, one service initialization |
| Actual Streamlit webserver in the fresh environment | 4.704 s | 690.2 MiB | Local WebSocket initiated a script session; real service/model/index warmed; SDK constructor mocked; no Ask sent |

The real-server profile used a temporary local harness that preauthorized its
own server session solely to measure startup; production passcode checks remain
unchanged. The harness ran loopback-only and was stopped afterward. No public
service was exposed. Its number describes startup, not a generation/load test.

The repeatable smoke script is `scripts/smoke_streamlit_cloud.py`; run it with the
appropriate environment's Python. Ignored local result files are
`tmp/cloud-smoke.json`, `tmp/cloud-smoke-clean.json`, and
`tmp/cloud-server-profile.json`. Generation outputs are synthetic contract checks,
not evidence of answer quality or a new benchmark score.

## Remaining manual gates

The public repository was anonymously readable. Its release listing contained no
runtime assets. The owner must publish the existing 76-MiB bundle (or an identical
approved version), provide its actual public URL/trusted hash, configure Cloud
secrets and deploy `cloud/streamlit_app.py` on Python 3.11. Hosted package resolution,
full cold download/restore, resource behavior and the resulting HTTPS URL remain
unverified. Run the limited public acceptance checks only after reviewing spend.

The shared local allowance survives sessions and only those restarts that retain
the disk. It is **not durable across Cloud redeployments**, nor a dollar cap.
Feedback is ephemeral too. Private access, short fixed event expiry, conservative
allowance and manual billing monitoring are required for this demo setup.

[Full manual deployment instructions](streamlit_cloud.md).
