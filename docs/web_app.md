# ResearchLens web application

This branch adds a thin FastAPI + Streamlit layer around the existing RAG
pipeline. Ingestion, retrieval, generation, citation validation, and evaluation
are unchanged.

## Architecture

```text
Browser
  |
  v
Streamlit app (app/streamlit_app.py)
  |
  v
ResearchService (app/service.py)
  |
  v
ResearchGenerator -> ResearchRetriever -> BM25 + BGE index -> OpenAI
```

FastAPI (`app/api.py`) exposes the same service for API clients and tests. The
Streamlit app can call the service directly, which keeps the deployment to one
public URL.

## Local setup

Use Python 3.11 and the existing corpus/index:

```bash
python -m pip install -r requirements-web.txt
cp .env.example .env   # add OPENAI_API_KEY
```

If `data/processed/chunks.jsonl` or `data/indexes/` is missing:

```bash
python -m src.ingestion.extract
python -m src.ingestion.clean
python -m src.ingestion.chunk
python scripts/build_index.py --device cpu
```

Start the UI:

```bash
streamlit run app/streamlit_app.py
```

Start the API:

```bash
uvicorn app.api:app --reload --port 8000
```

API documentation is available at `http://localhost:8000/docs`.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Corpus/index/model status |
| `GET` | `/papers` | Paper metadata for the UI |
| `POST` | `/ask` | Grounded answer with citations |
| `POST` | `/feedback` | Store a thumbs rating without question text |

Example:

```bash
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How does SelfCheckGPT detect hallucinations?","paper_ids":["P002"],"year":2023}'
```

The response is the existing `GenerationResponse` JSON, including `status`,
`answer`, `citations`, `evidence`, `limitations`, and `metrics`.

## Request rules

- Question length: 3–1000 characters.
- At most two papers are accepted.
- `answer_type="comparison"` requires exactly two `paper_ids`.
- `year` must be a positive integer.
- `author` and `section` are optional case-insensitive substring filters.
- The OpenAI key is read by the backend only. It is never included in a
  response or sent to the browser.

## Deployment

Recommended: **Hugging Face Spaces**.

For the smallest deployment, use the Streamlit SDK and include the existing
`data/processed/chunks.jsonl` and `data/indexes/` artifacts, or build them in a
Docker image. Do not rebuild the index on every request.

Set the key as a Space secret:

```text
OPENAI_API_KEY=...
```

If FastAPI must also run, use one Docker Space with FastAPI on internal port
8000 and Streamlit on public port 7860. Streamlit calls
`http://127.0.0.1:8000`.

## Current limitations

- No conversation memory; each question is independent.
- Feedback is append-only JSONL and may not survive a free-host restart.
- The app does not render PDFs; citations identify paper, page, chunk, and quote.
- The 117-case benchmark still needs a live run and human verification after
  the corpus expansion.
