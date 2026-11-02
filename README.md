# ResearchLens

**A citation-grounded retrieval-augmented research assistant for eight papers on LLM hallucination, factuality, and RAG.**

ResearchLens retrieves relevant passages with **BM25 + BGE embeddings**, fuses rankings with **Reciprocal Rank Fusion (RRF)**, and generates answers grounded only in the retrieved evidence. Every claim is checked against an exact source quotation, and the system abstains when the evidence is insufficient.

## Repository and demo

| Item | Value |
|---|---|
| Repository | https://github.com/yousefsassy/ResearchLens |
| Active branch | `feature/streamlit-cloud` |
| Demo passcode | `ResearchLens!2026#Demo47` |
| Demo entrypoint | `cloud/streamlit_app.py` |
| Public deployment | Pending final Streamlit Community Cloud release |

> The demo passcode is for the course demonstration only. Rotate it after grading.

## At a glance

| Component | Choice |
|---|---|
| Corpus | 8 papers · 250 PDF pages · 1,001 chunks |
| Keyword search | BM25 (`rank-bm25`) |
| Embeddings | `BAAI/bge-small-en-v1.5`, 384 dimensions |
| Vector index | NumPy exact cosine, 1,001 × 384 |
| Fusion | Reciprocal Rank Fusion, k = 60 |
| Generation | OpenAI API, structured claims + quote validation |
| Backend | FastAPI |
| Frontend | Streamlit |
| Benchmark | 117 questions |
| Tests | 415 passed |

## Architecture

```text
PDFs + papers_manifest.csv
        |
        v
extract -> clean -> chunk + metadata
        |
        +--> BM25 keyword index
        |
        +--> BGE embeddings -> validated NumPy index
        |
        v
BM25 + vector search -> RRF -> metadata filters
        |
        v
evidence selection -> grounded prompt -> OpenAI
        |
        v
citation validation -> answer + paper/page/chunk citations
```

The browser talks to Streamlit. Streamlit can call FastAPI over HTTP, or use the shared `ResearchService` directly in standalone Streamlit Cloud mode. **The OpenAI key stays server-side.**

## Demo access

The Streamlit Community Cloud entrypoint is:

```text
cloud/streamlit_app.py
```

Use the passcode shown above. The app includes:

- question answering over all papers or one selected paper,
- two-paper comparisons,
- `year`, `author`, and `section` metadata filters,
- grounded answers with paper/page/chunk/quote citations,
- evidence and limitations,
- request latency and token metrics,
- thumbs-up/down feedback.

The public URL is added here after the final deployment is verified.

## Corpus

| ID | Paper |
|---|---|
| P001 | A Survey on Hallucination in Large Language Models |
| P002 | SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection |
| P003 | FActScore: Fine-grained Atomic Evaluation of Factual Precision |
| P004 | TruthfulQA: Measuring How Models Mimic Human Falsehoods |
| P005 | Retrieval Augmentation Reduces Hallucination in Conversation |
| P006 | Survey of Hallucination in Natural Language Generation |
| P007 | HaluEval: A Large-Scale Hallucination Evaluation Benchmark |
| P008 | Chain-of-Verification Reduces Hallucination in Large Language Models |

Chunking is paragraph-aware, page-scoped, with a **1,500-character target** and **200-character overlap**. Every chunk preserves paper ID, PDF page, title, authors, year, section, and review flags.

## Results — 117-question benchmark

| Metric | Result |
|---|---:|
| Questions processed | 117 / 117 |
| Complete / partial | 79 / 27 |
| Abstained / clarification / error | 7 / 3 / 1 |
| Citation validation | 99.07% (106/107 checked) |
| Judge coverage | 109 / 117 |
| Factual accuracy | 95.63% on 101 applicable questions |
| Completeness | 85.32% on 109 judged questions |
| Semantic citation support | 98.04% on 101 judged questions |
| Mean / p95 latency | 3.80 s / 8.24 s |
| Estimated evaluation cost | $1.03060 including judging |

**Evaluation limits:** benchmark rubrics and labels are **not human-verified**. These are automated judge scores and must be reported with their denominators, not as accuracy over all 117 questions. See [`docs/full_benchmark_review.md`](docs/full_benchmark_review.md).

## Quick start

Requires **Python 3.11** and an **OpenAI API key**.

```bash
python -m pip install -r requirements-web.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
```

Prepare the corpus and index if they are not already present:

```bash
python -m src.ingestion.extract
python -m src.ingestion.clean
python -m src.ingestion.chunk
python scripts/build_index.py --device cpu
```

Start the backend:

```bash
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```bash
RESEARCHLENS_API_URL=http://127.0.0.1:8000 \
  python -m streamlit run app/streamlit_app.py
```

Ask a question from the CLI:

```bash
python scripts/ask_researchlens.py --live \
  --question "How does SelfCheckGPT detect hallucinations?" \
  --paper-ids P002
```

Run the tests:

```bash
python -m pytest -q
```

> Live generation calls the OpenAI API and may incur charges. No API key is committed.

## Documentation

- [Web application setup](docs/web_app.md)
- [Standalone Streamlit Cloud deployment](docs/streamlit_cloud.md)
- [Oracle ARM + FastAPI deployment](docs/deployment.md)
- [Full 117-question benchmark review](docs/full_benchmark_review.md)
- [Retrieval design](docs/retrieval_design.md)
- [Generation design](docs/generation_design.md)
- [Corpus notes](docs/corpus_notes.md)

## Team contributions

| Member | Contribution |
|---|---|
| Youssef Sassi | PDF extraction, cleaning, chunking, corpus provenance |
| Nour Guidara | Hybrid retrieval, retrieval evaluation, benchmark/reporting |
| Asma Turki | Generation, reliability, API cost tracking, deployment preparation |
| Emna Smaali | Metadata and filtering, corpus expansion, FastAPI/Streamlit integration, deployment |

## Limitations

- Benchmark labels and rubrics remain human-unverified.
- PDF extraction can damage equations, tables, and reading order; flagged chunks are excluded from evidence.
- The public demo is not yet verified; the passcode is a temporary course-demo control.
- Feedback and demo allowances are local and may reset on cloud redeployment.
- There is no conversation memory; each question is independent.
