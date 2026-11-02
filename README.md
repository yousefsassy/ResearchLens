# ResearchLens

A retrieval-augmented question-answering system for exploring scientific papers about **LLM hallucinations, factuality, and retrieval-augmented generation**. It searches a curated corpus of eight research papers, generates evidence-grounded answers, provides paper/page citations, and can abstain when evidence is insufficient.

ResearchLens combines **BM25 keyword search**, **BGE sentence embeddings**, and **Reciprocal Rank Fusion (RRF)**. An optional cross-encoder reranker is available; the current generation workflow uses hybrid retrieval without reranking. Answers are produced with the OpenAI API and checked against exact source quotations.

## Setup

Requires **Python 3.11**, an **OpenAI API key**, and the dependencies in `requirements.txt`.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your API key to `.env`:

```dotenv
OPENAI_API_KEY=your_api_key_here
```

Do not overwrite an existing configured `.env`. **Never commit `.env` to GitHub.**

For the local web application, install `requirements-web.txt`, then start the
backend and frontend in separate terminals:

```bash
.venv/bin/python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
RESEARCHLENS_API_URL=http://127.0.0.1:8000 .venv/bin/python -m streamlit run app/streamlit_app.py
```

Streamlit calls FastAPI over HTTP; only FastAPI loads BGE and the OpenAI key.
See [web setup and troubleshooting](docs/web_app.md) for installation, optional
filters, readiness, response statuses and examples. No remote service is deployed.

## Run

From the project root, prepare the corpus and vector index if they are not already present:

```powershell
.\.venv\Scripts\python.exe -m src.ingestion.extract
.\.venv\Scripts\python.exe -m src.ingestion.clean
.\.venv\Scripts\python.exe -m src.ingestion.chunk
.\.venv\Scripts\python.exe scripts/build_index.py --device cpu
```

Chunking reads `data/papers_manifest.csv` and attaches paper title, authors, year, category, source URL, licence, and an inferred section to every chunk. If the manifest or the metadata schema changes, rebuild both `chunks.jsonl` and the index.

If `data/processed/chunks.jsonl` and the matching `data/indexes/` files already exist, you can skip rebuilding them. The embedding model is downloaded on first use if it is not cached.

Ask a research question:

```powershell
.\.venv\Scripts\python.exe scripts/ask_researchlens.py --live --question "How does SelfCheckGPT detect hallucinations?" --paper-ids P002
```

To compare papers, omit `--paper-ids` or supply the relevant paper IDs:

```powershell
.\.venv\Scripts\python.exe scripts/ask_researchlens.py --live --question "Compare SelfCheckGPT and FActScore." --paper-ids P002 P003 --answer-type comparison
```

Optional metadata filters restrict retrieval before ranking. `--author` and `--section` are case-insensitive substring matches; `--year` is exact:

```powershell
.\.venv\Scripts\python.exe scripts/ask_researchlens.py --live --question "What limitations does SelfCheckGPT report?" --paper-ids P002 --year 2023 --author Manakul --section Limitations
```

The same filters work with the retrieval-only CLI:

```powershell
.\.venv\Scripts\python.exe scripts/test_retrieval.py --question "How does SelfCheckGPT detect hallucinations?" --mode hybrid --no-rerank --year 2023 --author Manakul --section SelfCheckGPT
```

The command outputs a structured JSON answer with citation details. **Live generation uses the OpenAI API and may incur charges.** A local Streamlit/FastAPI interface is also available.

## Corpus

The current corpus contains **8 papers, 250 PDF pages, and 1,001 text chunks**:

| ID | Paper |
|---|---|
| P001 | A Survey on Hallucination in Large Language Models |
| P002 | SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models |
| P003 | FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation |
| P004 | TruthfulQA: Measuring How Models Mimic Human Falsehoods |
| P005 | Retrieval Augmentation Reduces Hallucination in Conversation |
| P006 | Survey of Hallucination in Natural Language Generation |
| P007 | HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models |
| P008 | Chain-of-Verification Reduces Hallucination in Large Language Models |

## Results

The completed **117-question, eight-paper benchmark** produced 79 complete answers,
27 partial answers, seven abstentions, three clarifications and one generation
error. Combined citation validation was 99.07% (106/107 checked); judge coverage
was 109/117. Mean judged factual accuracy was 95.63% on 101 applicable questions,
not all 117. Mean pipeline latency was 3.80 seconds and estimated total evaluation
cost was $1.03060, including judging. Rubrics remain human-unverified. See
[the full benchmark review](docs/full_benchmark_review.md) for exact denominators,
costs and failure analysis. Historical results below describe earlier versions.

### Retrieval — preliminary pilot

A **20-question draft pilot** compared four retrieval methods. These relevance labels were **not human-approved**; results are exploratory, not a validated final retrieval benchmark. The pilot predates the P006-P008 corpus expansion and must be rerun for current numbers.

| Retrieval method | Recall@5 | MRR@10 | Mean search time |
|---|---:|---:|---:|
| BM25 | 0.825 | 0.702 | 6.7 ms |
| Vector | 0.700 | 0.596 | 26.7 ms |
| **Hybrid (RRF)** | **0.900** | **0.733** | 35.6 ms |
| Hybrid + reranker | 0.775 | 0.572 | 1.55 s |

Source: `docs/retrieval_results.md`. These timings exclude initialization.

### Generation — historical 105-question live benchmark

This table is the previous five-paper run. The current `eval/benchmark.v2.jsonl` contains **117 questions** after adding P006-P008; a new live run is required for updated numbers.

One full run of **105 questions** using `gpt-5.4-nano` for generation and an optional `gpt-5.4-mini` LLM judge produced:

| Metric | Result |
|---|---:|
| Questions processed | 105 / 105 |
| Complete answers | 64 (61.0%) |
| Partial answers | 25 (23.8%) |
| Errors | 8 (7.6%) |
| Abstentions / clarification requests | 5 / 3 |
| Expected-status agreement | 72.4% |
| Citation structural/quote validation | 91.8% (89/97 checked) |
| LLM-judged factual accuracy | 94.5% on successfully judged cases only |
| LLM-judged completeness | 90.4% on successfully judged cases only |
| LLM-judged semantic citation support | 96.4% on successfully judged cases only |
| Judge coverage | 60/105 (57.1%); 37 judge-validation errors |
| Mean / median / p95 latency | 4.37 s / 3.68 s / 9.63 s |
| Generation / judge API requests | 117 / 97 |
| Automated tests | 198 passed in the historical run; current integration suite: 362 |

**Evaluation limitations:** The benchmark labels and rubrics have **not been human-verified**. Semantic scores cover only the successfully judged subset and **must not be reported as accuracy over all 105 questions**. Citation validation checks source IDs, quotations, and structure; it is not the same as semantic citation support. Estimated API cost was not calculated.

The main observed weaknesses are multi-paper comparisons, citation-validation errors, and judge-output validation failures. See the generated `report.md`, `answers.md`, `per_question.csv`, and `summary.json` from the full evaluation run for details.

## Evaluation

Run the automated tests (no live generation calls):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the full live benchmark with semantic judging (requires `eval/full_benchmark.py` in your current working tree):

```powershell
.\.venv\Scripts\python.exe -u eval/full_benchmark.py run --live --max-requests 240 --judge-model gpt-5.4-mini --judge-budget 120
```

This command may make up to **240 generation requests** and **120 judge requests**. Saved reports are written under `eval/results/full-<timestamp>/`. Do not run the live benchmark merely to view previous results.

## Repository

| Path | Contents |
|---|---|
| `data/raw/` | Eight scientific PDFs |
| `app/` | FastAPI backend, Streamlit HTTP client/interface, feedback |
| `data/processed/` | Extracted pages, cleaned text, and chunks (generated locally) |
| `data/indexes/` | Cached embeddings and index metadata (generated locally) |
| `src/ingestion/` | PDF extraction, cleaning, and chunking |
| `src/retrieval/` | BM25, vector similarity, RRF fusion, and optional reranking |
| `src/generation/` | Prompting, evidence selection, OpenAI generation, and citation validation |
| `scripts/` | Index building and question-answering commands |
| `eval/` | Benchmark dataset, scoring, judge, and evaluation tools |
| `tests/` | Unit and regression tests |
| `docs/` | Corpus, retrieval, and generation design notes |

Detailed system design: [`docs/retrieval_design.md`](docs/retrieval_design.md) · [`docs/generation_design.md`](docs/generation_design.md) · Preliminary retrieval analysis: [`docs/retrieval_results.md`](docs/retrieval_results.md).

## Limitations

ResearchLens currently covers eight papers. PDF extraction can be unreliable for equations and tables; multi-paper comparisons sometimes omit requested details; and generated responses can fail strict citation validation. The LLM judge still requires reliability improvements and human-reviewed evaluation labels. CLI and local Streamlit/FastAPI interfaces are available; a remote service has not been deployed.
