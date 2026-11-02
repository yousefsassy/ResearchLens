# ResearchLens: FastAPI and Streamlit

The local workflow is **Browser → Streamlit → HTTP → FastAPI → ResearchService →
ResearchGenerator → hybrid retrieval/OpenAI → citation validation → Streamlit**.
Streamlit never loads the corpus, embedding model or OpenAI key. The backend reuses
the existing RAG pipeline; there is no second implementation under `src/api/`.

## Setup

Use Python 3.11 in the project environment:

```bash
.venv/bin/python -m pip install -r requirements-web.txt
.venv/bin/python -m pip check
```

`requirements-web.txt` includes the existing ML/generation requirements plus
FastAPI, Uvicorn and Streamlit. Local verification used FastAPI 0.162.0,
Uvicorn 0.54.0 and Streamlit 1.66.1.

Create the root `.env` **only if it does not already exist**, using `.env.example`
as a template. Add `OPENAI_API_KEY` locally. Do not overwrite a configured `.env`.
The backend reads the project-root file; exported environment variables take
precedence. Do not put the key in Streamlit settings, URLs, source code or browser
requests. The model remains `gpt-5.4-nano`.

Restore the agreed `data/processed/chunks.jsonl`, `data/indexes/embeddings.npy`,
`data/indexes/index_metadata.json`, and pinned BGE model cache. The corpus must
match the vector index. Current artifacts contain eight papers, 250 pages and
1,001 chunks with fingerprint
`3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
Use the existing ingestion/index scripts only when an intentional rebuild is
required; the web application does not rebuild or download a different model.

This development session's ML packages and model cache may reside in temporary
RAM storage (`/tmp/researchlens-ml-deps`, `/tmp/researchlens-model-cache`). Restore
them after reboot, or install/provision them persistently before deployment.

## Start locally

Backend terminal, from the repository root:

```bash
.venv/bin/python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Use one backend worker. Startup loads and validates the corpus/vector index,
initializes BM25 and warms the BGE encoder once without calling OpenAI. A missing
resource keeps the service available for `/health` and `/papers`, but not ready
for generation. Shutdown closes the backend-owned SDK transport once.

Frontend terminal:

```bash
RESEARCHLENS_API_URL=http://127.0.0.1:8000 \
.venv/bin/python -m streamlit run app/streamlit_app.py
```

The UI reads `RESEARCHLENS_API_URL` from its **process environment**, defaulting to
`http://127.0.0.1:8000`. It does not read the backend's `.env`.

- UI: `http://localhost:8501`
- API: `http://127.0.0.1:8000`
- OpenAPI documentation: `http://127.0.0.1:8000/docs`
- Readiness: `http://127.0.0.1:8000/health`

Optional backend variables are `RESEARCHLENS_CORS_ORIGINS` (export before startup)
and `RESEARCHLENS_FEEDBACK_PATH`. No category filter is implemented.

## HTTP contract

| Method | Path | Result |
|---|---|---|
| GET | `/health` | 200 ready; 503 degraded; safe readiness metadata |
| GET | `/papers` | Eight trusted paper summaries; available even when retrieval is degraded |
| POST | `/ask` | Existing `GenerationResponse` 1.0, including evidence/citations/timings/usage |
| POST | `/feedback` | Append feedback once per optional `submission_id` |

`answer_type` is `auto`, `qa` or `comparison`. Explicit comparison mode requires
exactly two selected IDs. `paper_ids`, `year`, `author` and `section` are optional;
omit them or send null for general QA. An explicit empty paper list is invalid.
Years must be positive JSON integers (not booleans, strings or floats). Author
and section are trimmed case-insensitive substring filters; selected filters
combine with AND before ranking. Empty optional text becomes null.

Question length is 3–1,000 characters; author/section length is at most 200.
Unknown explicit paper IDs return 422. Ambiguous paper mentions in a question
can return the generator's `needs_clarification` outcome without inference.

```bash
curl -s http://127.0.0.1:8000/papers
curl -s -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What causes hallucinations?"}'
curl -s -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"How does SelfCheckGPT detect hallucinations?","paper_ids":["P002"],"year":2023,"author":"Manakul"}'
curl -s -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Compare SelfCheckGPT and FActScore methods.","answer_type":"comparison","paper_ids":["P002","P003"]}'
```

Every `/ask` may incur API charges. Streamlit sends the request once, without
automatic POST retries. HTTP connection timeout is five seconds; the answer read
timeout is 400 seconds to accommodate up to two 180-second generation attempts.
A frontend timeout does not cancel work already running on the server.

### Outcomes and failures

- Complete, partial, abstained and needs-clarification responses use HTTP 200.
- Invalid request bodies/IDs use 422.
- Missing corpus/index/cache/credentials, shutdown or busy service use 503.
- Upstream API failure, malformed/incomplete generation or invalid citations use
  502 while preserving the existing structured generation error.
- An actual SDK `APITimeoutError` is classified `openai_timeout` and uses 504.
  Other uncertain connection errors remain `openai_api_error`, not guessed timeouts.

The UI validates HTTP payloads with Pydantic. Structured errors preserve their
code, safe message and retryability; malformed bodies/provider exception text are
not displayed as answers. Old results are cleared before a new submission.

## Resource ownership and feedback

One backend service owns the retriever, validated in-memory index, encoder and SDK
transport. Every question borrows them with a **new generation wrapper and a
two-attempt budget** (initial request plus at most one citation repair). There is
no application-lifetime 25-attempt counter. The application serializes inference;
another request waits at most one second for the lock, then receives a structured
503 `service_busy`. There is no unbounded inference queue.

Health reports the readiness of resources validated/loaded at startup. It does
not make paid probes or verify the account's current quota. Restart the backend
after restoring startup resources or changing credentials. The loaded in-memory
index is the active snapshot; replacing files is not a live reload mechanism.

Feedback controls retain ratings/comments and are tied to a unique UI answer ID
and the provider request ID when present. Successful submissions disable the send
button. The same `submission_id` is ignored on repeat, including after store
recreation. This is a single-worker JSONL store, not a multi-worker database.
Feedback comments can contain user-entered information; treat the ignored
`data/feedback/` directory appropriately and do not commit it.

## Verification and troubleshooting

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
git diff --check
```

Tests use mocked inference and include real localhost HTTP plus Streamlit AppTest
interactions. Automated tests never use the professor's API key for inference.

Integration verification on 2 November 2026: **360 tests passed, zero failures or
skips**. This includes 35 sequential successful questions on one service, per-request
repair budgets, readiness/error statuses, real localhost HTTP with mocked SDK
responses, and 11 Streamlit interaction tests. `pip check` and `git diff --check`
passed. No ingestion, retrieval, metadata-filter or benchmark-scoring code changed.

One explicitly authorized live smoke test used the actual Streamlit code via
AppTest, localhost FastAPI, real hybrid retrieval and `gpt-5.4-nano`. With P002,
year 2023 and author Manakul selected, it returned complete: six evidence passages,
three claims and three validated citation links. It used one generation attempt,
zero repair/judge requests, 7,772 input tokens and 333 output tokens; pipeline
latency was 5.67 seconds and UI HTTP roundtrip 5.72 seconds. The frontend process
had no `OPENAI_API_KEY`. This is one smoke observation, not a new benchmark or
latency guarantee. Headless Streamlit launch was checked separately; no browser
visual inspection was claimed. Ignored records are in
`eval/results/integration-smoke-20261102-045345/`.

- **Cannot reach backend:** start Uvicorn and check `RESEARCHLENS_API_URL`.
- **503 readiness:** inspect the safe `/health` fields, restore matching artifacts
  and the pinned BGE cache, configure the backend key, then restart.
- **502 API error:** check server-side key access/quota. No paid fallback exists.
- **504:** the upstream SDK timed out. The frontend does not retry automatically.
- **503 busy:** wait for the active question to finish before submitting again.
- **No evidence:** use optional filters carefully; there is no unfiltered retry.
- **Invalid input:** correct the fields; the UI displays validation messages.

The full 117-case benchmark **has run**: 79 complete, 27 partial, seven abstained,
three clarifications and one generation error; 109 valid judgments, estimated
cost $1.03060. See `docs/full_benchmark_review.md` for denominators and limitations.
That benchmark predates this web integration and was not rerun for it.

## Deployment boundary

No hosting provider is configured or selected. Provision Python 3.11, the same
corpus/index/cache, persistent feedback storage if desired, and outbound OpenAI
access. Keep the API/key private to the backend and configure the UI's API URL.
Start with one worker; additional workers duplicate model memory. Local warmed
retrieval used about 617 MiB peak RSS in review; this is not a remote capacity
guarantee. Existing RAM-backed caches must not be relied on in deployment.
The prototype has no authentication layer; do not expose the professor's funded
generation endpoint publicly without an appropriate access policy.
